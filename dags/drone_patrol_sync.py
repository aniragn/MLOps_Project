from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import sqlite3

PATROL_DB = "/data/drone_patrol.db"
APP_DB = "/data/app_detections.db"
THRESHOLD = 0.65

def extract(**ctx):
    con = sqlite3.connect(PATROL_DB)
    rows = con.execute("SELECT id,timestamp,latitude,longitude,confiance,rubbish FROM drone_detections WHERE processed=0").fetchall()
    con.close()
    ctx["ti"].xcom_push(key="rows", value=rows)

def transform(**ctx):
    rows = ctx["ti"].xcom_pull(key="rows", task_ids="extract")
    filtered = [r for r in rows if r[4] >= THRESHOLD]
    ctx["ti"].xcom_push(key="filtered", value=filtered)
    ctx["ti"].xcom_push(key="all_ids", value=[r[0] for r in rows])

def load(**ctx):
    filtered = ctx["ti"].xcom_pull(key="filtered", task_ids="transform")
    all_ids  = ctx["ti"].xcom_pull(key="all_ids",  task_ids="transform")
    # Load into app DB
    app_con = sqlite3.connect(APP_DB)
    app_con.execute("""CREATE TABLE IF NOT EXISTS app_detections (
        id INTEGER PRIMARY KEY, timestamp TEXT, model_name TEXT,
        confiance REAL, latitude REAL, longitude REAL, rubbish INTEGER, source TEXT)""")
    for r in filtered:
        app_con.execute("INSERT INTO app_detections (timestamp,model_name,confiance,latitude,longitude,rubbish,source) VALUES (?,?,?,?,?,?,'drone_patrol')",
                        (r[1],"yolov8",r[4],r[2],r[3],r[5]))
    app_con.commit(); app_con.close()
    # Mark processed=1 in patrol DB
    patrol_con = sqlite3.connect(PATROL_DB)
    if all_ids:
        patrol_con.execute(f"UPDATE drone_detections SET processed=1 WHERE id IN ({','.join('?'*len(all_ids))})", all_ids)
    patrol_con.commit(); patrol_con.close()

with DAG("drone_patrol_sync", schedule_interval=None,
         start_date=datetime(2024,1,1), catchup=False) as dag:
    t1 = PythonOperator(task_id="extract",   python_callable=extract,   provide_context=True)
    t2 = PythonOperator(task_id="transform", python_callable=transform, provide_context=True)
    t3 = PythonOperator(task_id="load",      python_callable=load,      provide_context=True)
    t1 >> t2 >> t3