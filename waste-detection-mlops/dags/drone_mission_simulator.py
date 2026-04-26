from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sqlite3, random

def simulate_mission():
    import os
    DB = "/data/drone_patrol.db"
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS drone_detections (
        id INTEGER PRIMARY KEY, timestamp TEXT, latitude REAL, longitude REAL,
        confiance REAL, rubbish INTEGER, processed INTEGER DEFAULT 0)""")
    rows = [(datetime.utcnow().isoformat(), random.uniform(43,51),
             random.uniform(-5,10), round(random.uniform(0.3,0.99),2),
             random.randint(1,10), 0) for _ in range(10)]
    con.executemany("INSERT INTO drone_detections (timestamp,latitude,longitude,confiance,rubbish,processed) VALUES (?,?,?,?,?,?)", rows)
    con.commit(); con.close()

with DAG("drone_mission_simulator", schedule_interval="*/5 * * * *",
         start_date=datetime(2024,1,1), catchup=False) as dag:
    PythonOperator(task_id="simulate", python_callable=simulate_mission)