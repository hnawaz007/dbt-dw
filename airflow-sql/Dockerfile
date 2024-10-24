FROM apache/airflow:2.9.0

RUN pip install dbt-postgres==1.8.2 \
	&& pip install markupsafe==2.0.1 \
	&& pip install apache-airflow-providers-postgres \
	&& pip install apache-airflow-providers-odbc \
	&& pip install psycopg2-binary \
	&& pip install pyodbc \
	&& pip install apache-airflow-providers-microsoft-mssql \
	&& pip install apache-airflow-providers-microsoft-mssql[odbc] \
	&& pip install apache-airflow-providers-microsoft-azure \
	&& pip install gitpython \
	&& pip install apache-airflow-providers-airbyte[http] \
	&& pip install apache-airflow-providers-airbyte \
	&& pip install oracledb --upgrade \
	&& pip install apache-airflow-providers-common-sql \
	&& pip install apache-airflow-providers-oracle \
	&& pip install apache-airflow-providers-oracle[common.sql] \
	&& pip install dbt-airflow \
	&& pip install plyvel \
	&& pip install --upgrade cmake \
	&& pip install --upgrade pyarrow==14.0.0 \
	&& pip install airflow-provider-great-expectations \
	&& pip uninstall dbt \
	&& pip install dbt-core==1.8.2


USER root
RUN sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys B7B3B788A8D3785C
RUN sudo apt-get update
RUN sudo apt-get install -y git

USER airflow
RUN airflow db migrate
#RUN airflow db init
#RUN airflow db upgrade