from airflow.operators.email import EmailOperator
from datetime import datetime, timedelta

from email_config import send_mail


from airflow import DAG




default_args = {
    "owner": "Airflow",
    "start_date": datetime(2023, 4, 12),
    "catchup": False
}

with DAG(dag_id="Sending_mail",
        schedule_interval="@once",
        default_args=default_args,
        ) as dag:

    send_email_notification= print("Hello World!")##send_mail("hnawaz@localmail.com", "Airflow Notification ", f"This is a test message. Data extract error: File location " ) # print("Hello World!")#
    
send_email_notification