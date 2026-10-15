#!/usr/bin/env python3
"""
ETL Pipeline UI — AdventureWorks2019 (SQL Server) → PostgreSQL
Airbyte-inspired web interface for managing the ETL pipeline.

Install : pip install fastapi uvicorn sqlalchemy pyodbc psycopg2-binary
Run     : uvicorn etl_ui:app --port 8080
Open    : http://localhost:8080
"""

import json
import subprocess
import sys
import uuid
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# ─── Paths ────────────────────────────────────────────────────────────────────
ROOT         = Path(__file__).parent
STATE_FILE   = ROOT / "etl_state.json"
ETL_SCRIPT   = ROOT / "etl_pipeline_polars.py"
LOG_BUF: deque = deque(maxlen=3000)   # in-memory ring buffer

# ─── Table metadata (mirrors TABLE_MAP in etl_pipeline.py) ───────────────────
TABLE_META: Dict[str, Dict] = {
    "address":                    {"src_schema": "Person",     "src_table": "Address"},
    "customer":                   {"src_schema": "Sales",      "src_table": "Customer"},
    "salesorderdetail":           {"src_schema": "Sales",      "src_table": "SalesOrderDetail"},
    "salesorderheader":           {"src_schema": "Sales",      "src_table": "SalesOrderHeader"},
    "salesorderheadersalesreason":{"src_schema": "Sales",      "src_table": "SalesOrderHeaderSalesReason"},
    "countryregion":              {"src_schema": "Person",     "src_table": "CountryRegion"},
    "person":                     {"src_schema": "dbo",        "src_table": "vw_person"},
    "product":                    {"src_schema": "Production", "src_table": "Product"},
    "productcategory":            {"src_schema": "Production", "src_table": "ProductCategory"},
    "productsubcategory":         {"src_schema": "Production", "src_table": "ProductSubcategory"},
    "salesreason":                {"src_schema": "Sales",      "src_table": "SalesReason"},
    "salesterritory":             {"src_schema": "Sales",      "src_table": "SalesTerritory"},
    "stateprovince":              {"src_schema": "Person",     "src_table": "StateProvince"},
    "store":                      {"src_schema": "Sales",      "src_table": "Store"},
    "businessentityaddress":      {"src_schema": "Person",     "src_table": "BusinessEntityAddress"},
}

DEFAULT_STATE: Dict[str, Any] = {
    "source": {
        "host": "localhost", "port": 1433,
        "database": "AdventureWorks2019",
        "username": "etl", "password": "demopass",
        "driver": "ODBC Driver 17 for SQL Server", "trust_cert": True,
    },
    "destination": {
        "host": "localhost", "port": 5432,
        "database": "adventureworks", "schema": "source",
        "username": "etl", "password": "demopass",
    },
    "streams": {
        name: {"enabled": True, "sync_mode": "Full refresh | Overwrite",
               "last_sync": None, "last_rows": None}
        for name in TABLE_META
    },
    "replication_frequency": "Manual",
    "sync_running": False,
    "current_run_id": None,
    "history": [],
}


def load_state() -> Dict:
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            saved = json.load(f)
        merged = {**DEFAULT_STATE, **saved}
        for k, v in DEFAULT_STATE["streams"].items():
            if k not in merged.get("streams", {}):
                merged["streams"][k] = dict(v)
        merged["sync_running"] = False   # always reset on startup
        return merged
    return {k: (dict(v) if isinstance(v, dict) else v) for k, v in DEFAULT_STATE.items()}


def save_state(s: Dict):
    with open(STATE_FILE, "w") as f:
        json.dump(s, f, indent=2, default=str)


STATE = load_state()


def add_log(level: str, msg: str, run_id: Optional[str] = None):
    LOG_BUF.append({
        "ts": datetime.now().isoformat(timespec="seconds"),
        "level": level, "message": msg, "run_id": run_id,
    })


# ─── FastAPI app ──────────────────────────────────────────────────────────────
app = FastAPI(title="ETL Pipeline UI")


# ─── Background sync task ─────────────────────────────────────────────────────
def _run_sync(tables: List[str], run_id: str):
    global STATE
    STATE["sync_running"] = True
    STATE["current_run_id"] = run_id

    cmd = [sys.executable, str(ETL_SCRIPT)]
    if len(tables) < len(STATE["streams"]):      # selective sync
        cmd += ["--table"] + tables

    add_log("INFO", f"▶  Run {run_id} started — {len(tables)} table(s)", run_id)
    add_log("INFO", "   " + " ".join(cmd), run_id)

    started = datetime.now()
    run_rec = {
        "id": run_id, "started": started.isoformat(),
        "finished": None, "status": "running",
        "tables": tables, "duration_s": None, "log_lines": 0,
    }
    STATE["history"].insert(0, run_rec)
    save_state(STATE)

    lines = 0
    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, cwd=str(ROOT),
        )
        for raw in proc.stdout:
            line = raw.rstrip()
            if not line:
                continue
            lvl = ("ERROR"   if "ERROR"   in line or "FAILED" in line
                   else "WARNING" if "WARNING" in line
                   else "INFO")
            add_log(lvl, line, run_id)
            lines += 1
        proc.wait()

        finished = datetime.now()
        dur = (finished - started).total_seconds()
        status = "success" if proc.returncode == 0 else "failed"
        icon = "✓" if status == "success" else "✗"
        add_log("INFO" if status == "success" else "ERROR",
                f"{icon}  Run {run_id} {status} in {dur:.1f}s", run_id)

        for rec in STATE["history"]:
            if rec["id"] == run_id:
                rec.update(finished=finished.isoformat(), status=status,
                           duration_s=round(dur, 1), log_lines=lines)

        ts = finished.isoformat()
        for t in tables:
            if t in STATE["streams"]:
                STATE["streams"][t]["last_sync"] = ts

    except Exception as exc:
        add_log("ERROR", f"✗  Run {run_id} crashed: {exc}", run_id)
        for rec in STATE["history"]:
            if rec["id"] == run_id:
                rec.update(status="failed", finished=datetime.now().isoformat())

    STATE["sync_running"] = False
    STATE["current_run_id"] = None
    save_state(STATE)


# ─── API Routes ───────────────────────────────────────────────────────────────

@app.get("/api/state")
def api_state():
    return STATE


@app.get("/api/streams")
def api_streams():
    dst_schema = STATE["destination"]["schema"]
    return [
        {
            "name":        name,
            "enabled":     cfg["enabled"],
            "sync_mode":   cfg.get("sync_mode", "Full refresh | Overwrite"),
            "last_sync":   cfg.get("last_sync"),
            "last_rows":   cfg.get("last_rows"),
            "src_schema":  TABLE_META[name]["src_schema"],
            "src_table":   TABLE_META[name]["src_table"],
            "dest_schema": dst_schema,
            "dest_table":  name,
        }
        for name, cfg in STATE["streams"].items()
    ]


# NOTE: /api/streams/bulk MUST be defined before /api/streams/{name}
@app.put("/api/streams/bulk")
def api_streams_bulk(body: Dict):
    enabled = body.get("enabled", True)
    names   = body.get("names", list(STATE["streams"].keys()))
    for n in names:
        if n in STATE["streams"]:
            STATE["streams"][n]["enabled"] = enabled
    save_state(STATE)
    return {"updated": len(names)}


class StreamUpdate(BaseModel):
    enabled: Optional[bool] = None
    sync_mode: Optional[str] = None


@app.put("/api/streams/{name}")
def api_stream_update(name: str, body: StreamUpdate):
    if name not in STATE["streams"]:
        raise HTTPException(404, f"Stream '{name}' not found")
    if body.enabled is not None:
        STATE["streams"][name]["enabled"] = body.enabled
    if body.sync_mode is not None:
        STATE["streams"][name]["sync_mode"] = body.sync_mode
    save_state(STATE)
    return STATE["streams"][name]


@app.put("/api/connections/{conn_type}")
def api_conn_update(conn_type: str, body: Dict):
    if conn_type not in ("source", "destination"):
        raise HTTPException(400, "conn_type must be 'source' or 'destination'")
    STATE[conn_type].update(body)
    save_state(STATE)
    return STATE[conn_type]


@app.post("/api/connections/{conn_type}/test")
def api_conn_test(conn_type: str):
    try:
        from sqlalchemy import create_engine, text  # type: ignore
        if conn_type == "source":
            s   = STATE["source"]
            drv = s.get("driver", "ODBC Driver 17 for SQL Server").replace(" ", "+")
            tc  = "yes" if s.get("trust_cert", True) else "no"
            url = (f"mssql+pyodbc://{s['username']}:{s['password']}"
                   f"@{s['host']}:{s['port']}/{s['database']}"
                   f"?driver={drv}&TrustServerCertificate={tc}")
        else:
            d   = STATE["destination"]
            url = (f"postgresql+psycopg2://{d['username']}:{d['password']}"
                   f"@{d['host']}:{d['port']}/{d['database']}")
        engine = create_engine(url)
        with engine.connect() as c:
            c.execute(text("SELECT 1"))
        return {"status": "ok",    "message": "Connection successful ✓"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@app.put("/api/settings")
def api_settings(body: Dict):
    if "replication_frequency" in body:
        STATE["replication_frequency"] = body["replication_frequency"]
    save_state(STATE)
    return {"replication_frequency": STATE["replication_frequency"]}


class SyncRequest(BaseModel):
    tables: Optional[List[str]] = None


@app.post("/api/sync/start")
def api_sync_start(body: SyncRequest, background_tasks: BackgroundTasks):
    if STATE.get("sync_running"):
        raise HTTPException(409, "A sync is already running")
    enabled = [n for n, c in STATE["streams"].items() if c["enabled"]]
    tables  = [t for t in (body.tables or enabled) if t in enabled]
    if not tables:
        raise HTTPException(400, "No enabled streams to sync")
    run_id = str(uuid.uuid4())[:8]
    background_tasks.add_task(_run_sync, tables, run_id)
    return {"run_id": run_id, "tables": tables, "status": "started"}


@app.get("/api/sync/status")
def api_sync_status():
    return {"running": STATE.get("sync_running", False),
            "run_id":  STATE.get("current_run_id")}


@app.get("/api/history")
def api_history():
    return STATE.get("history", [])


@app.get("/api/logs")
def api_logs(run_id: Optional[str] = None,
             level:  Optional[str] = None,
             limit:  int = 600):
    logs = list(LOG_BUF)
    if run_id:
        logs = [l for l in logs if l.get("run_id") == run_id]
    if level:
        logs = [l for l in logs if l.get("level") == level.upper()]
    return logs[-limit:]


# ─── Frontend ─────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def serve_ui():
    return HTML_PAGE


# ─────────────────────────────────────────────────────────────────────────────
HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ETL Pipeline — AdventureWorks</title>
<style>
/* ── Reset ── */
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
     background:#F1F5F9;color:#1E293B;min-height:100vh;display:flex}
a{text-decoration:none;color:inherit}

/* ── Sidebar ── */
.sidebar{width:224px;min-height:100vh;background:#fff;border-right:1px solid #E2E8F0;
         display:flex;flex-direction:column;position:fixed;top:0;left:0;bottom:0;z-index:100}
.sb-logo{padding:18px 16px 14px;border-bottom:1px solid #E2E8F0}
.sb-logo-mark{display:flex;align-items:center;gap:10px}
.sb-logo-icon{width:32px;height:32px;background:linear-gradient(135deg,#3B82F6,#6366F1);
               border-radius:8px;display:flex;align-items:center;justify-content:center;
               font-size:16px;color:#fff}
.sb-logo-text{font-size:14px;font-weight:700;color:#1E293B}
.sb-logo-sub{font-size:11px;color:#94A3B8;margin-top:2px}
.sb-section{padding:8px 8px 0;font-size:10px;font-weight:600;color:#94A3B8;
             letter-spacing:.6px;text-transform:uppercase;margin-top:8px;padding-bottom:4px}
.sb-nav{padding:8px;flex:1;overflow-y:auto}
.nav-item{display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:7px;
          cursor:pointer;color:#64748B;font-size:13.5px;font-weight:500;margin-bottom:1px;
          transition:all .12s}
.nav-item:hover{background:#F8FAFC;color:#1E293B}
.nav-item.active{background:#EFF6FF;color:#2563EB}
.nav-item .ni{width:20px;text-align:center;font-size:15px;flex-shrink:0}
.sb-footer{padding:12px 14px;border-top:1px solid #E2E8F0;font-size:12px}
.sb-status{display:flex;align-items:center;gap:6px;color:#64748B}

/* ── Main ── */
.main{margin-left:224px;flex:1;min-height:100vh;display:flex;flex-direction:column}
.page-header{background:#fff;border-bottom:1px solid #E2E8F0;padding:18px 28px;
             display:flex;justify-content:space-between;align-items:center;
             position:sticky;top:0;z-index:50}
.ph-left h2{font-size:17px;font-weight:700;color:#0F172A}
.ph-left .ph-sub{font-size:12px;color:#94A3B8;margin-top:2px}
.ph-actions{display:flex;align-items:center;gap:8px}
.page-body{padding:24px 28px;flex:1}

/* ── Buttons ── */
.btn{display:inline-flex;align-items:center;gap:6px;padding:7px 14px;border-radius:7px;
     font-size:13px;font-weight:500;cursor:pointer;border:none;transition:all .12s;
     white-space:nowrap}
.btn-primary{background:#2563EB;color:#fff}
.btn-primary:hover{background:#1D4ED8}
.btn-primary:disabled{background:#93C5FD;cursor:not-allowed}
.btn-ghost{background:transparent;color:#475569;border:1px solid #E2E8F0}
.btn-ghost:hover{background:#F8FAFC;border-color:#CBD5E1}
.btn-danger{background:#FEF2F2;color:#DC2626;border:1px solid #FECACA}
.btn-danger:hover{background:#FEE2E2}
.btn-success{background:#10B981;color:#fff}
.btn-success:hover{background:#059669}
.btn-sm{padding:5px 10px;font-size:12px}
.btn-xs{padding:3px 8px;font-size:11px;border-radius:5px}

/* ── Cards ── */
.card{background:#fff;border:1px solid #E2E8F0;border-radius:10px;padding:20px}
.card-title{font-size:13px;font-weight:600;color:#0F172A;margin-bottom:14px;
            display:flex;align-items:center;gap:7px}

/* ── Grids ── */
.g2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.g3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px}
.g4{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}

/* ── Stat cards ── */
.stat{background:#fff;border:1px solid #E2E8F0;border-radius:10px;padding:18px 20px}
.stat-label{font-size:11.5px;font-weight:600;color:#94A3B8;text-transform:uppercase;
            letter-spacing:.4px}
.stat-value{font-size:30px;font-weight:700;color:#0F172A;margin-top:8px;line-height:1}
.stat-sub{font-size:12px;color:#64748B;margin-top:6px}
.stat-icon{width:36px;height:36px;border-radius:9px;display:flex;align-items:center;
           justify-content:center;font-size:17px;float:right;margin-top:-4px}

/* ── Form ── */
.form-group{display:flex;flex-direction:column;gap:5px;margin-bottom:12px}
.form-row{display:grid;gap:12px}
.form-row.c2{grid-template-columns:1fr 1fr}
.form-row.c3{grid-template-columns:1fr 1fr 1fr}
label{font-size:11.5px;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:.3px}
input,select,textarea{padding:8px 10px;border:1px solid #E2E8F0;border-radius:7px;
                       font-size:13px;color:#1E293B;background:#fff;width:100%;
                       transition:border-color .12s,box-shadow .12s}
input:focus,select:focus{outline:none;border-color:#3B82F6;
                          box-shadow:0 0 0 3px rgba(59,130,246,.1)}
input[type=checkbox]{width:auto;cursor:pointer}
.inline-sel{width:auto!important;padding:4px 8px!important;font-size:12px!important;
            border-radius:5px!important}

/* ── Toggle ── */
.toggle{position:relative;display:inline-block;width:38px;height:21px;flex-shrink:0}
.toggle input{opacity:0;width:0;height:0}
.tslider{position:absolute;cursor:pointer;inset:0;background:#CBD5E1;border-radius:21px;
          transition:.2s}
.tslider::before{content:'';position:absolute;height:15px;width:15px;left:3px;bottom:3px;
                  background:#fff;border-radius:50%;transition:.2s;box-shadow:0 1px 3px rgba(0,0,0,.2)}
.toggle input:checked+.tslider{background:#2563EB}
.toggle input:checked+.tslider::before{transform:translateX(17px)}
.toggle input:disabled+.tslider{opacity:.5;cursor:not-allowed}

/* ── Table ── */
.tbl-wrap{overflow-x:auto;border-radius:10px}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;padding:10px 14px;font-size:11px;font-weight:600;color:#94A3B8;
   text-transform:uppercase;letter-spacing:.5px;border-bottom:1px solid #E2E8F0;
   background:#F8FAFC;white-space:nowrap}
td{padding:11px 14px;border-bottom:1px solid #F1F5F9;color:#374151;vertical-align:middle}
tr:last-child td{border-bottom:none}
tbody tr:hover td{background:#F8FAFC}
.tbl-empty{text-align:center;padding:36px 14px;color:#94A3B8;font-size:13px}

/* ── Badges ── */
.badge{display:inline-flex;align-items:center;gap:4px;padding:2px 9px;border-radius:20px;
       font-size:11.5px;font-weight:600;white-space:nowrap}
.b-success{background:#DCFCE7;color:#15803D}
.b-error{background:#FEE2E2;color:#DC2626}
.b-warning{background:#FEF9C3;color:#CA8A04}
.b-info{background:#DBEAFE;color:#2563EB}
.b-gray{background:#F1F5F9;color:#64748B}
.b-running{background:#FEF3C7;color:#D97706}
.b-view{background:#F0FDF4;color:#16A34A}

/* ── Dot ── */
.dot{width:8px;height:8px;border-radius:50%;display:inline-block;flex-shrink:0}
.d-green{background:#22C55E}
.d-red{background:#EF4444}
.d-gray{background:#CBD5E1}
.d-yellow{background:#F59E0B}

/* ── Conn card ── */
.conn-card{border:1px solid #E2E8F0;border-radius:10px;overflow:hidden}
.conn-head{padding:14px 20px;background:#F8FAFC;border-bottom:1px solid #E2E8F0;
           display:flex;align-items:center;justify-content:space-between}
.conn-type-wrap{display:flex;align-items:center;gap:12px}
.conn-icon{width:40px;height:40px;border-radius:10px;display:flex;align-items:center;
           justify-content:center;font-size:20px}
.ci-mssql{background:#DBEAFE}
.ci-pg{background:#E0F2FE}
.conn-name{font-weight:600;font-size:14px;color:#0F172A}
.conn-sub{font-size:12px;color:#94A3B8}
.conn-body{padding:20px}

/* ── Log viewer ── */
.log-wrap{background:#0F172A;border-radius:10px;padding:14px 16px;
          height:500px;overflow-y:auto;font-family:'Cascadia Code','Consolas',monospace;font-size:12px}
.ll{padding:1px 0;line-height:1.7}
.lINFO{color:#94A3B8}
.lWARNING{color:#FCD34D}
.lERROR{color:#F87171}
.lts{color:#475569;margin-right:10px;font-size:11px;user-select:none}
.lrun{color:#6366F1;margin-right:6px;font-size:10px}

/* ── Alerts ── */
.alert{padding:10px 14px;border-radius:8px;font-size:13px;margin-bottom:12px;
       display:flex;align-items:flex-start;gap:8px}
.a-info{background:#EFF6FF;color:#1D4ED8;border:1px solid #BFDBFE}
.a-success{background:#F0FDF4;color:#15803D;border:1px solid #BBF7D0}
.a-error{background:#FEF2F2;color:#B91C1C;border:1px solid #FECACA}
.a-warning{background:#FFFBEB;color:#92400E;border:1px solid #FDE68A}

/* ── Spinner ── */
@keyframes spin{to{transform:rotate(360deg)}}
.spin{width:14px;height:14px;border:2px solid #E2E8F0;border-top-color:#2563EB;
      border-radius:50%;animation:spin .6s linear infinite;display:inline-block;flex-shrink:0}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.6}}
.pulsing{animation:pulse 1.4s ease-in-out infinite}

/* ── Pages ── */
.page{display:none}.page.active{display:block}

/* ── Section title ── */
.sec-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}
.sec-title{font-size:14px;font-weight:600;color:#0F172A}

/* ── Misc ── */
.mt2{margin-top:8px}.mt3{margin-top:12px}.mt4{margin-top:16px}.mt6{margin-top:24px}
.mb3{margin-bottom:12px}.mb4{margin-bottom:16px}
.text-muted{color:#94A3B8}.text-sm{font-size:12px}
.flex{display:flex}.fac{display:flex;align-items:center}.gap2{gap:8px}.gap3{gap:12px}
code{font-family:'Cascadia Code','Consolas',monospace;font-size:12px;
     background:#F1F5F9;padding:1px 5px;border-radius:4px;color:#4338CA}
hr{border:none;border-top:1px solid #E2E8F0;margin:20px 0}
</style>
</head>
<body>

<!-- ═══════════════════════════ SIDEBAR ═══════════════════════════ -->
<aside class="sidebar">
  <div class="sb-logo">
    <div class="sb-logo-mark">
      <div class="sb-logo-icon">🔄</div>
      <div>
        <div class="sb-logo-text">ETL Pipeline</div>
        <div class="sb-logo-sub">AdventureWorks2019</div>
      </div>
    </div>
  </div>

  <nav class="sb-nav">
    <div class="sb-section">Pipeline</div>
    <div class="nav-item active" data-page="overview" onclick="navTo('overview',this)">
      <span class="ni">📊</span> Overview
    </div>
    <div class="nav-item" data-page="streams" onclick="navTo('streams',this)">
      <span class="ni">📋</span> Streams
    </div>
    <div class="nav-item" data-page="history" onclick="navTo('history',this)">
      <span class="ni">⏱️</span> Sync History
    </div>
    <div class="nav-item" data-page="logs" onclick="navTo('logs',this)">
      <span class="ni">📄</span> Logs
    </div>
    <div class="sb-section">Configuration</div>
    <div class="nav-item" data-page="source" onclick="navTo('source',this)">
      <span class="ni">🗄️</span> Source
    </div>
    <div class="nav-item" data-page="destination" onclick="navTo('destination',this)">
      <span class="ni">🐘</span> Destination
    </div>
    <div class="nav-item" data-page="settings" onclick="navTo('settings',this)">
      <span class="ni">⚙️</span> Settings
    </div>
  </nav>

  <div class="sb-footer">
    <div class="sb-status" id="sb-status">
      <span class="dot d-gray"></span> Idle
    </div>
    <div class="text-sm text-muted mt2" id="sb-freq">Manual sync</div>
  </div>
</aside>

<!-- ═══════════════════════════ MAIN ═══════════════════════════ -->
<main class="main">

<!-- ── OVERVIEW ── -->
<div id="page-overview" class="page active">
  <div class="page-header">
    <div class="ph-left">
      <h2>Overview</h2>
      <div class="ph-sub" id="ov-last-sync">Last sync: never</div>
    </div>
    <div class="ph-actions">
      <button class="btn btn-ghost btn-sm" onclick="refreshAll()">↻ Refresh</button>
      <button class="btn btn-primary" id="sync-btn" onclick="startSync()">▶ Sync Now</button>
    </div>
  </div>
  <div class="page-body">
    <div id="ov-alert" style="display:none"></div>
    <div class="g4 mb4">
      <div class="stat">
        <div class="stat-icon" style="background:#EFF6FF">📋</div>
        <div class="stat-label">Total Streams</div>
        <div class="stat-value" id="ov-total">15</div>
        <div class="stat-sub" id="ov-enabled-sub">15 enabled</div>
      </div>
      <div class="stat">
        <div class="stat-icon" style="background:#F0FDF4">✓</div>
        <div class="stat-label">Last Run Status</div>
        <div class="stat-value" style="font-size:16px;margin-top:14px" id="ov-last-status">—</div>
        <div class="stat-sub" id="ov-last-dur">No runs yet</div>
      </div>
      <div class="stat">
        <div class="stat-icon" style="background:#FEF9C3">⏱</div>
        <div class="stat-label">Total Runs</div>
        <div class="stat-value" id="ov-run-count">0</div>
        <div class="stat-sub" id="ov-success-rate">—</div>
      </div>
      <div class="stat">
        <div class="stat-icon" style="background:#F5F3FF">📦</div>
        <div class="stat-label">Destination Tables</div>
        <div class="stat-value" id="ov-dest-tables">15</div>
        <div class="stat-sub" id="ov-dest-schema">schema: source</div>
      </div>
    </div>

    <div class="g2 mb4">
      <div class="card">
        <div class="card-title">Source Connection</div>
        <div class="fac gap2 mb3">
          <span class="dot" id="ov-src-dot"></span>
          <span id="ov-src-label" style="font-size:13px">SQL Server · localhost:1433</span>
        </div>
        <div class="text-sm text-muted" id="ov-src-db"></div>
        <hr>
        <div class="text-sm" style="color:#374151">15 source tables mapped across 4 schemas</div>
      </div>
      <div class="card">
        <div class="card-title">Destination Connection</div>
        <div class="fac gap2 mb3">
          <span class="dot" id="ov-dst-dot"></span>
          <span id="ov-dst-label" style="font-size:13px">PostgreSQL · localhost:5432</span>
        </div>
        <div class="text-sm text-muted" id="ov-dst-db"></div>
        <hr>
        <div class="text-sm" style="color:#374151" id="ov-dst-schema-note"></div>
      </div>
    </div>

    <div class="card">
      <div class="sec-head">
        <div class="sec-title">Recent Sync Runs</div>
        <button class="btn btn-ghost btn-sm" onclick="navTo('history')">View All</button>
      </div>
      <div class="tbl-wrap">
        <table>
          <thead><tr>
            <th>Run ID</th><th>Started</th><th>Duration</th>
            <th>Tables</th><th>Log Lines</th><th>Status</th>
          </tr></thead>
          <tbody id="ov-history-body">
            <tr><td colspan="6" class="tbl-empty">No sync runs yet — click Sync Now to start</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>

<!-- ── STREAMS ── -->
<div id="page-streams" class="page">
  <div class="page-header">
    <div class="ph-left">
      <h2>Streams</h2>
      <div class="ph-sub" id="str-sub">15 streams · 15 enabled</div>
    </div>
    <div class="ph-actions">
      <button class="btn btn-ghost btn-sm" onclick="toggleAll(true)">Enable All</button>
      <button class="btn btn-ghost btn-sm" onclick="toggleAll(false)">Disable All</button>
      <button class="btn btn-primary" id="str-sync-btn" onclick="startSync()">▶ Sync Enabled</button>
    </div>
  </div>
  <div class="page-body">
    <div class="card" style="padding:0;overflow:hidden">
      <div class="tbl-wrap">
        <table id="streams-table">
          <thead><tr>
            <th style="width:54px;text-align:center">Sync</th>
            <th>Namespace</th>
            <th>Source Table</th>
            <th>Sync Mode</th>
            <th>Destination Schema</th>
            <th>Destination Stream</th>
            <th>Last Synced</th>
            <th></th>
          </tr></thead>
          <tbody id="streams-body">
            <tr><td colspan="8" class="tbl-empty">Loading…</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>

<!-- ── SYNC HISTORY ── -->
<div id="page-history" class="page">
  <div class="page-header">
    <div class="ph-left">
      <h2>Sync History</h2>
      <div class="ph-sub">All past sync runs</div>
    </div>
    <div class="ph-actions">
      <button class="btn btn-ghost btn-sm" onclick="loadHistory()">↻ Refresh</button>
    </div>
  </div>
  <div class="page-body">
    <div class="card" style="padding:0;overflow:hidden">
      <div class="tbl-wrap">
        <table>
          <thead><tr>
            <th>Run ID</th><th>Started</th><th>Finished</th>
            <th>Duration</th><th>Tables</th><th>Log Lines</th>
            <th>Status</th><th></th>
          </tr></thead>
          <tbody id="hist-body">
            <tr><td colspan="8" class="tbl-empty">No runs yet</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>

<!-- ── LOGS ── -->
<div id="page-logs" class="page">
  <div class="page-header">
    <div class="ph-left">
      <h2>Logs</h2>
      <div class="ph-sub">Real-time pipeline output</div>
    </div>
    <div class="ph-actions">
      <select id="log-run" class="inline-sel" onchange="loadLogs()">
        <option value="">All runs</option>
      </select>
      <select id="log-level" class="inline-sel" onchange="loadLogs()">
        <option value="">All levels</option>
        <option value="INFO">INFO</option>
        <option value="WARNING">WARNING</option>
        <option value="ERROR">ERROR</option>
      </select>
      <button class="btn btn-ghost btn-sm" onclick="loadLogs()">↻ Refresh</button>
      <button class="btn btn-ghost btn-sm" onclick="document.getElementById('log-viewer').innerHTML=''">🗑 Clear</button>
    </div>
  </div>
  <div class="page-body">
    <div class="log-wrap" id="log-viewer">
      <div class="ll lINFO"><span class="lts">—</span>waiting for log entries…</div>
    </div>
  </div>
</div>

<!-- ── SOURCE ── -->
<div id="page-source" class="page">
  <div class="page-header">
    <div class="ph-left">
      <h2>Source Connection</h2>
      <div class="ph-sub">Microsoft SQL Server — AdventureWorks2019</div>
    </div>
    <div class="ph-actions">
      <button class="btn btn-ghost btn-sm" onclick="testConn('source','src-result')">🔌 Test</button>
      <button class="btn btn-primary" onclick="saveSource()">💾 Save</button>
    </div>
  </div>
  <div class="page-body">
    <div id="src-result" class="mb3"></div>
    <div class="conn-card mb4">
      <div class="conn-head">
        <div class="conn-type-wrap">
          <div class="conn-icon ci-mssql">🗄️</div>
          <div>
            <div class="conn-name">SQL Server</div>
            <div class="conn-sub">mssql+pyodbc · ODBC Driver 17</div>
          </div>
        </div>
      </div>
      <div class="conn-body">
        <div class="form-row c2">
          <div class="form-group"><label>Host</label><input id="src-host" value="localhost"></div>
          <div class="form-group"><label>Port</label><input id="src-port" type="number" value="1433"></div>
        </div>
        <div class="form-row c2">
          <div class="form-group"><label>Database</label><input id="src-db" value="AdventureWorks2019"></div>
          <div class="form-group"><label>ODBC Driver</label><input id="src-driver" value="ODBC Driver 17 for SQL Server"></div>
        </div>
        <div class="form-row c2">
          <div class="form-group"><label>Username</label><input id="src-user" value="sa"></div>
          <div class="form-group"><label>Password</label><input id="src-pass" type="password" value="Aneela_01"></div>
        </div>
        <div class="form-group">
          <label style="display:flex;align-items:center;gap:7px;cursor:pointer;text-transform:none;font-size:13px">
            <input type="checkbox" id="src-trust" checked> Trust Server Certificate
          </label>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-title">📋 Mapped Source Tables</div>
      <div class="tbl-wrap">
        <table>
          <thead><tr><th>Schema</th><th>Table</th><th>Type</th><th>Destination Table</th><th>Special Handling</th></tr></thead>
          <tbody>
            <tr><td><code>Person</code></td><td>Address</td><td><span class="badge b-info">Table</span></td><td><code>source.address</code></td><td><span class="badge b-warning">Geography cast</span></td></tr>
            <tr><td><code>Sales</code></td><td>Customer</td><td><span class="badge b-info">Table</span></td><td><code>source.customer</code></td><td>—</td></tr>
            <tr><td><code>Sales</code></td><td>SalesOrderDetail</td><td><span class="badge b-info">Table</span></td><td><code>source.salesorderdetail</code></td><td>—</td></tr>
            <tr><td><code>Sales</code></td><td>SalesOrderHeader</td><td><span class="badge b-info">Table</span></td><td><code>source.salesorderheader</code></td><td>—</td></tr>
            <tr><td><code>Sales</code></td><td>SalesOrderHeaderSalesReason</td><td><span class="badge b-info">Table</span></td><td><code>source.salesorderheadersalesreason</code></td><td>—</td></tr>
            <tr><td><code>Person</code></td><td>CountryRegion</td><td><span class="badge b-info">Table</span></td><td><code>source.countryregion</code></td><td>—</td></tr>
            <tr><td><code>dbo</code></td><td>vw_person</td><td><span class="badge b-view">View</span></td><td><code>source.person</code></td><td>—</td></tr>
            <tr><td><code>Production</code></td><td>Product</td><td><span class="badge b-info">Table</span></td><td><code>source.product</code></td><td>—</td></tr>
            <tr><td><code>Production</code></td><td>ProductCategory</td><td><span class="badge b-info">Table</span></td><td><code>source.productcategory</code></td><td>—</td></tr>
            <tr><td><code>Production</code></td><td>ProductSubcategory</td><td><span class="badge b-info">Table</span></td><td><code>source.productsubcategory</code></td><td>—</td></tr>
            <tr><td><code>Sales</code></td><td>SalesReason</td><td><span class="badge b-info">Table</span></td><td><code>source.salesreason</code></td><td>—</td></tr>
            <tr><td><code>Sales</code></td><td>SalesTerritory</td><td><span class="badge b-info">Table</span></td><td><code>source.salesterritory</code></td><td>—</td></tr>
            <tr><td><code>Person</code></td><td>StateProvince</td><td><span class="badge b-info">Table</span></td><td><code>source.stateprovince</code></td><td>—</td></tr>
            <tr><td><code>Sales</code></td><td>Store</td><td><span class="badge b-info">Table</span></td><td><code>source.store</code></td><td>—</td></tr>
            <tr><td><code>Person</code></td><td>BusinessEntityAddress</td><td><span class="badge b-info">Table</span></td><td><code>source.businessentityaddress</code></td><td>—</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>

<!-- ── DESTINATION ── -->
<div id="page-destination" class="page">
  <div class="page-header">
    <div class="ph-left">
      <h2>Destination Connection</h2>
      <div class="ph-sub">PostgreSQL — adventureworks</div>
    </div>
    <div class="ph-actions">
      <button class="btn btn-ghost btn-sm" onclick="testConn('destination','dst-result')">🔌 Test</button>
      <button class="btn btn-primary" onclick="saveDest()">💾 Save</button>
    </div>
  </div>
  <div class="page-body">
    <div id="dst-result" class="mb3"></div>
    <div class="conn-card mb4">
      <div class="conn-head">
        <div class="conn-type-wrap">
          <div class="conn-icon ci-pg">🐘</div>
          <div>
            <div class="conn-name">PostgreSQL</div>
            <div class="conn-sub">postgresql+psycopg2</div>
          </div>
        </div>
      </div>
      <div class="conn-body">
        <div class="form-row c2">
          <div class="form-group"><label>Host</label><input id="dst-host" value="localhost"></div>
          <div class="form-group"><label>Port</label><input id="dst-port" type="number" value="5432"></div>
        </div>
        <div class="form-row c2">
          <div class="form-group"><label>Database</label><input id="dst-db" value="adventureworks"></div>
          <div class="form-group"><label>Target Schema</label><input id="dst-schema" value="source"></div>
        </div>
        <div class="form-row c2">
          <div class="form-group"><label>Username</label><input id="dst-user" value="etl"></div>
          <div class="form-group"><label>Password</label><input id="dst-pass" type="password" value="demopass"></div>
        </div>
        <div class="alert a-info mt3">
          ℹ️ All tables land in the <strong>source</strong> schema. Column names are lowercased automatically.
          Each sync does a full <strong>replace</strong> (DROP + CREATE + INSERT).
        </div>
      </div>
    </div>
  </div>
</div>

<!-- ── SETTINGS ── -->
<div id="page-settings" class="page">
  <div class="page-header">
    <div class="ph-left">
      <h2>Settings</h2>
      <div class="ph-sub">Transfer and replication configuration</div>
    </div>
    <div class="ph-actions">
      <button class="btn btn-primary" onclick="saveSettings()">💾 Save Settings</button>
    </div>
  </div>
  <div class="page-body">
    <div class="card mb4">
      <div class="card-title">⏱️ Transfer Settings</div>
      <div class="form-row c2">
        <div class="form-group">
          <label>Replication Frequency</label>
          <select id="set-freq">
            <option value="Manual">Manual (trigger only)</option>
            <option value="Hourly">Every hour</option>
            <option value="Every 6 hours">Every 6 hours</option>
            <option value="Every 12 hours">Every 12 hours</option>
            <option value="Daily">Every 24 hours</option>
          </select>
        </div>
        <div class="form-group">
          <label>Sync Mode (default)</label>
          <select>
            <option selected>Full refresh | Overwrite</option>
            <option>Full refresh | Append</option>
          </select>
        </div>
      </div>
      <div class="alert a-warning mt3">
        ⚠️ Auto-scheduling requires Windows Task Scheduler or cron.
        Schedule: <code>python etl_pipeline.py</code> at the desired interval.
      </div>
    </div>

    <div class="card mb4">
      <div class="card-title">🗂️ Namespace Settings</div>
      <div class="form-row c3">
        <div class="form-group">
          <label>Destination Namespace</label>
          <select><option>Custom format</option></select>
        </div>
        <div class="form-group">
          <label>Custom Format</label>
          <input value="source" readonly>
        </div>
        <div class="form-group">
          <label>Stream Prefix (Optional)</label>
          <input placeholder="e.g. src_ → src_address">
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-title">ℹ️ Pipeline Info</div>
      <div class="g2">
        <div>
          <div class="text-sm text-muted mb3">Source</div>
          <div class="text-sm"><strong>Engine:</strong> SQL Server 2019 (pyodbc)</div>
          <div class="text-sm mt2"><strong>Database:</strong> AdventureWorks2019</div>
          <div class="text-sm mt2"><strong>Tables:</strong> 14 tables + 1 view (vw_person)</div>
          <div class="text-sm mt2"><strong>Special:</strong> Geography → WKT via STAsText()</div>
        </div>
        <div>
          <div class="text-sm text-muted mb3">Destination</div>
          <div class="text-sm"><strong>Engine:</strong> PostgreSQL (psycopg2)</div>
          <div class="text-sm mt2"><strong>Database:</strong> adventureworks</div>
          <div class="text-sm mt2"><strong>Schema:</strong> source</div>
          <div class="text-sm mt2"><strong>Columns:</strong> lowercased · batch size 1 000</div>
        </div>
      </div>
    </div>
  </div>
</div>

</main>

<!-- ═══════════════════════════ JAVASCRIPT ═══════════════════════════ -->
<script>
// ── globals ───────────────────────────────────────────────────────────────────
let pollTimer = null;
let logTimer  = null;

// ── nav ───────────────────────────────────────────────────────────────────────
function navTo(page, el) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('page-' + page).classList.add('active');
  const target = el || document.querySelector(`[data-page="${page}"]`);
  if (target) target.classList.add('active');

  if (page === 'streams')  loadStreams();
  if (page === 'history')  loadHistory();
  if (page === 'logs')     { loadLogs(); startLogPoll(); }
  if (page === 'overview') refreshAll();
  if (page !== 'logs') stopLogPoll();
}

// ── sync ──────────────────────────────────────────────────────────────────────
async function startSync(tables) {
  const btn = document.getElementById('sync-btn');
  if (btn && btn.disabled) return;
  if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spin"></span> Syncing…'; btn.classList.add('pulsing'); }

  const sbtn = document.getElementById('str-sync-btn');
  if (sbtn) { sbtn.disabled = true; sbtn.innerHTML = '<span class="spin"></span> Running…'; }

  try {
    const res = await fetch('/api/sync/start', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(tables ? { tables } : {})
    });
    const data = await res.json();
    if (!res.ok) { showAlert('ov-alert','error', data.detail || 'Failed to start sync'); resetSyncBtns(); return; }
    showAlert('ov-alert','info', `Run <strong>${data.run_id}</strong> started · ${data.tables.length} tables queued`);
    pollSync();
  } catch(e) {
    showAlert('ov-alert','error','Network error: ' + e.message);
    resetSyncBtns();
  }
}

function resetSyncBtns() {
  const btn = document.getElementById('sync-btn');
  if (btn) { btn.disabled = false; btn.innerHTML = '▶ Sync Now'; btn.classList.remove('pulsing'); }
  const sbtn = document.getElementById('str-sync-btn');
  if (sbtn) { sbtn.disabled = false; sbtn.innerHTML = '▶ Sync Enabled'; }
}

function pollSync() {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(async () => {
    const r = await fetch('/api/sync/status');
    const s = await r.json();
    const sb = document.getElementById('sb-status');
    if (s.running) {
      if (sb) sb.innerHTML = '<span class="dot d-yellow"></span> Syncing…';
    } else {
      if (sb) sb.innerHTML = '<span class="dot d-green"></span> Idle';
      clearInterval(pollTimer); pollTimer = null;
      resetSyncBtns();
      refreshAll();
    }
  }, 2500);
}

// ── streams ───────────────────────────────────────────────────────────────────
async function loadStreams() {
  const res = await fetch('/api/streams');
  const rows = await res.json();
  const enabled = rows.filter(r => r.enabled).length;
  const sub = document.getElementById('str-sub');
  if (sub) sub.textContent = `${rows.length} streams · ${enabled} enabled`;

  const body = document.getElementById('streams-body');
  body.innerHTML = rows.map(s => `
    <tr>
      <td style="text-align:center">
        <label class="toggle">
          <input type="checkbox" ${s.enabled ? 'checked' : ''}
                 onchange="toggleStream('${s.name}',this.checked)">
          <span class="tslider"></span>
        </label>
      </td>
      <td><code>${s.src_schema}</code></td>
      <td><strong>${s.src_table}</strong></td>
      <td>
        <select class="inline-sel" onchange="setSyncMode('${s.name}',this.value)">
          <option ${s.sync_mode==='Full refresh | Overwrite'?'selected':''}>Full refresh | Overwrite</option>
          <option ${s.sync_mode==='Full refresh | Append'?'selected':''}>Full refresh | Append</option>
        </select>
      </td>
      <td><code>${s.dest_schema}</code></td>
      <td><code>${s.dest_table}</code></td>
      <td class="text-muted text-sm">${s.last_sync ? fmtDate(s.last_sync) : '—'}</td>
      <td>
        <button class="btn btn-ghost btn-xs" onclick="syncOne('${s.name}')">▶ Run</button>
      </td>
    </tr>
  `).join('');
}

async function toggleStream(name, enabled) {
  await fetch('/api/streams/' + name, {
    method:'PUT', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ enabled })
  });
  loadStreams();
}

async function setSyncMode(name, sync_mode) {
  await fetch('/api/streams/' + name, {
    method:'PUT', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ sync_mode })
  });
}

async function toggleAll(enabled) {
  await fetch('/api/streams/bulk', {
    method:'PUT', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ enabled })
  });
  loadStreams();
}

async function syncOne(name) {
  await startSync([name]);
  navTo('logs');
}

// ── connections ───────────────────────────────────────────────────────────────
async function testConn(type, resultId) {
  const el = document.getElementById(resultId);
  el.innerHTML = '<div class="alert a-info"><span class="spin"></span> Testing connection…</div>';
  const res  = await fetch('/api/connections/' + type + '/test', {method:'POST'});
  const data = await res.json();
  el.innerHTML = data.status === 'ok'
    ? `<div class="alert a-success">✅ ${data.message}</div>`
    : `<div class="alert a-error">❌ ${data.message}</div>`;
}

async function saveSource() {
  const resultEl = document.getElementById('src-result');
  resultEl.innerHTML = '<div class="alert a-info">💾 Saving…</div>';
  const body = {
    host: v('src-host'), port: parseInt(v('src-port')),
    database: v('src-db'), username: v('src-user'),
    password: v('src-pass'), driver: v('src-driver'),
    trust_cert: document.getElementById('src-trust').checked
  };
  try {
    const res = await fetch('/api/connections/source', {method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
    if (!res.ok) {
      const err = await res.json().catch(() => ({detail: res.statusText}));
      resultEl.innerHTML = `<div class="alert a-error">❌ Save failed: ${err.detail || res.statusText}</div>`;
      return;
    }
    resultEl.innerHTML = '<div class="alert a-success">✅ Source connection saved.</div>';
  } catch(e) {
    resultEl.innerHTML = `<div class="alert a-error">❌ Network error: ${e.message}</div>`;
  }
}

async function saveDest() {
  const resultEl = document.getElementById('dst-result');
  resultEl.innerHTML = '<div class="alert a-info">💾 Saving…</div>';
  const body = {
    host: v('dst-host'), port: parseInt(v('dst-port')),
    database: v('dst-db'), schema: v('dst-schema'),
    username: v('dst-user'), password: v('dst-pass')
  };
  try {
    const res = await fetch('/api/connections/destination', {method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
    if (!res.ok) {
      const err = await res.json().catch(() => ({detail: res.statusText}));
      resultEl.innerHTML = `<div class="alert a-error">❌ Save failed: ${err.detail || res.statusText}</div>`;
      return;
    }
    resultEl.innerHTML = '<div class="alert a-success">✅ Destination connection saved.</div>';
  } catch(e) {
    resultEl.innerHTML = `<div class="alert a-error">❌ Network error: ${e.message}</div>`;
  }
}

// ── history ───────────────────────────────────────────────────────────────────
async function loadHistory() {
  const res  = await fetch('/api/history');
  const hist = await res.json();
  const body = document.getElementById('hist-body');
  if (!hist.length) {
    body.innerHTML = '<tr><td colspan="8" class="tbl-empty">No sync runs yet.</td></tr>';
    return;
  }
  body.innerHTML = hist.map(r => `
    <tr>
      <td><code>${r.id}</code></td>
      <td>${fmtDate(r.started)}</td>
      <td>${r.finished ? fmtDate(r.finished) : '…'}</td>
      <td>${r.duration_s != null ? r.duration_s + 's' : '…'}</td>
      <td>${(r.tables||[]).length}</td>
      <td>${r.log_lines || 0}</td>
      <td>${statusBadge(r.status)}</td>
      <td><button class="btn btn-ghost btn-xs" onclick="viewRunLogs('${r.id}')">Logs</button></td>
    </tr>
  `).join('');
}

function viewRunLogs(runId) {
  navTo('logs');
  document.getElementById('log-run').value = runId;
  loadLogs();
}

// ── logs ──────────────────────────────────────────────────────────────────────
async function loadLogs() {
  const runId = document.getElementById('log-run').value;
  const level = document.getElementById('log-level').value;
  let url = '/api/logs?limit=600';
  if (runId)  url += '&run_id=' + runId;
  if (level)  url += '&level='  + level;

  const res  = await fetch(url);
  const logs = await res.json();

  // Rebuild run-filter options
  const hRes  = await fetch('/api/history');
  const hist  = await hRes.json();
  const sel   = document.getElementById('log-run');
  const cur   = sel.value;
  sel.innerHTML = '<option value="">All runs</option>' +
    hist.map(r => `<option value="${r.id}" ${r.id===cur?'selected':''}>${r.id} · ${fmtDate(r.started)}</option>`).join('');
  if (cur) sel.value = cur;

  const viewer = document.getElementById('log-viewer');
  if (!logs.length) {
    viewer.innerHTML = '<div class="ll lINFO"><span class="lts">—</span>No log entries found.</div>';
    return;
  }
  viewer.innerHTML = logs.map(l =>
    `<div class="ll l${l.level}"><span class="lts">${l.ts}</span>${l.run_id ? `<span class="lrun">[${l.run_id}]</span>` : ''}${esc(l.message)}</div>`
  ).join('');
  viewer.scrollTop = viewer.scrollHeight;
}

function startLogPoll() {
  if (logTimer) return;
  logTimer = setInterval(loadLogs, 3000);
}

function stopLogPoll() {
  if (logTimer) { clearInterval(logTimer); logTimer = null; }
}

// ── settings ──────────────────────────────────────────────────────────────────
async function saveSettings() {
  const freq = document.getElementById('set-freq').value;
  await fetch('/api/settings', {method:'PUT', headers:{'Content-Type':'application/json'},
              body: JSON.stringify({ replication_frequency: freq })});
  showAlert('ov-alert','success','Settings saved.');
  const sbFreq = document.getElementById('sb-freq');
  if (sbFreq) sbFreq.textContent = freq === 'Manual' ? 'Manual sync' : freq;
}

// ── overview ──────────────────────────────────────────────────────────────────
async function refreshAll() {
  const res   = await fetch('/api/state');
  const state = await res.json();

  // Sidebar freq
  const sbFreq = document.getElementById('sb-freq');
  if (sbFreq) sbFreq.textContent = state.replication_frequency === 'Manual' ? 'Manual sync' : state.replication_frequency;

  // Sync running?
  const sbStat = document.getElementById('sb-status');
  if (state.sync_running) {
    if (sbStat) sbStat.innerHTML = '<span class="dot d-yellow"></span> Syncing…';
    pollSync();
  } else {
    if (sbStat) sbStat.innerHTML = '<span class="dot d-green"></span> Idle';
  }

  // Connection labels
  const src = state.source || {}; const dst = state.destination || {};
  setText('ov-src-label', `SQL Server · ${src.host}:${src.port}`);
  setText('ov-src-db',    `Database: ${src.database}`);
  setText('ov-dst-label', `PostgreSQL · ${dst.host}:${dst.port}`);
  setText('ov-dst-db',    `Database: ${dst.database}`);
  setText('ov-dst-schema-note', `Target schema: ${dst.schema} · Full refresh overwrite`);
  setText('ov-dest-schema', `schema: ${dst.schema}`);

  // Dots
  setAttr('ov-src-dot','className','dot d-green');
  setAttr('ov-dst-dot','className','dot d-green');

  // Stats
  const streams = state.streams || {};
  const total   = Object.keys(streams).length;
  const enabled = Object.values(streams).filter(s => s.enabled).length;
  setText('ov-total',       total);
  setText('ov-enabled-sub', `${enabled} enabled`);
  setText('ov-dest-tables', enabled);

  const hist = state.history || [];
  setText('ov-run-count', hist.length);
  const ok   = hist.filter(r => r.status === 'success').length;
  const rate = hist.length ? Math.round(ok/hist.length*100) : 0;
  setText('ov-success-rate', hist.length ? `${rate}% success rate` : '—');

  if (hist.length) {
    const last = hist[0];
    setHTML('ov-last-status', statusBadge(last.status));
    setText('ov-last-dur', last.duration_s ? `${last.duration_s}s duration` : 'finished');
    setText('ov-last-sync', `Last sync: ${fmtDate(last.started)}`);
  }

  // Populate form fields from saved state
  setVal('src-host', src.host); setVal('src-port', src.port);
  setVal('src-db', src.database); setVal('src-user', src.username);
  setVal('src-pass', src.password); setVal('src-driver', src.driver);
  setVal('dst-host', dst.host); setVal('dst-port', dst.port);
  setVal('dst-db', dst.database); setVal('dst-schema', dst.schema);
  setVal('dst-user', dst.username); setVal('dst-pass', dst.password);
  if (state.replication_frequency) setVal('set-freq', state.replication_frequency);

  // Overview history table
  const obody = document.getElementById('ov-history-body');
  if (obody) {
    if (!hist.length) {
      obody.innerHTML = '<tr><td colspan="6" class="tbl-empty">No sync runs yet — click Sync Now to start.</td></tr>';
    } else {
      obody.innerHTML = hist.slice(0,5).map(r => `
        <tr>
          <td><code>${r.id}</code></td>
          <td>${fmtDate(r.started)}</td>
          <td>${r.duration_s != null ? r.duration_s+'s' : '…'}</td>
          <td>${(r.tables||[]).length} tables</td>
          <td>${r.log_lines||0}</td>
          <td>${statusBadge(r.status)}</td>
        </tr>
      `).join('');
    }
  }
}

// ── helpers ───────────────────────────────────────────────────────────────────
function v(id) { const el = document.getElementById(id); return el ? el.value : ''; }
function setText(id, val) { const el = document.getElementById(id); if (el) el.textContent = val; }
function setHTML(id, val) { const el = document.getElementById(id); if (el) el.innerHTML  = val; }
function setVal(id, val)  { const el = document.getElementById(id); if (el && val != null) el.value = val; }
function setAttr(id, attr, val) { const el = document.getElementById(id); if (el) el[attr] = val; }

function fmtDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('en-GB', {dateStyle:'short', timeStyle:'short'});
}

function statusBadge(s) {
  const m = {
    success: '<span class="badge b-success">✓ success</span>',
    failed:  '<span class="badge b-error">✗ failed</span>',
    running: '<span class="badge b-running">↻ running</span>',
  };
  return m[s] || `<span class="badge b-gray">${s}</span>`;
}

function showAlert(containerId, type, msg) {
  const cls = type==='error' ? 'a-error' : type==='success' ? 'a-success' : 'a-info';
  const el  = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = `<div class="alert ${cls}">${msg}</div>`;
  el.style.display = 'block';
  setTimeout(() => { el.style.display='none'; }, 7000);
}

function esc(s) {
  return String(s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// ── init ──────────────────────────────────────────────────────────────────────
refreshAll();
setInterval(refreshAll, 30000);
</script>
</body>
</html>"""


# ─── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=False)
