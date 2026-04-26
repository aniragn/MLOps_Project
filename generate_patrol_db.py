import sqlite3, random, datetime, os

DB = "data/drone_patrol.db"
os.makedirs("data", exist_ok=True)
con = sqlite3.connect(DB)
con.execute("""CREATE TABLE IF NOT EXISTS drone_detections (
    id INTEGER PRIMARY KEY, timestamp TEXT, latitude REAL, longitude REAL,
    confiance REAL, rubbish INTEGER, processed INTEGER DEFAULT 0
)""")
con.commit()

rows = []
for _ in range(50):
    ts = datetime.datetime.utcnow().isoformat()
    rows.append((ts, random.uniform(43,51), random.uniform(-5,10),
                 round(random.uniform(0.3, 0.99), 2), random.randint(1,10), 0))
con.executemany("INSERT INTO drone_detections (timestamp,latitude,longitude,confiance,rubbish,processed) VALUES (?,?,?,?,?,?)", rows)
con.commit(); con.close()
print(f"✓ Mission simulated — drone_patrol.db updated\n  {len(rows)} new detections inserted")