from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import sqlite3, json, time, datetime, os, mlflow

app = FastAPI()
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
mlflow.set_tracking_uri(MLFLOW_URI)
DB_PATH = "/data/app_detections.db"
LOG_PATH = "/app/logs/predictions.jsonl"
VALID_MODELS = ["yolov8","yolo26","rtdetr","rtdetrv2","rfdetr","dfine","deim-dfine","fusion-model"]

# Prometheus metrics
predictions_total = Counter("ml_predictions_total", "Total predictions")
predictions_by_model = Counter("ml_predictions_by_model_total", "By model", ["model"])
inference_latency = Histogram("ml_inference_latency_seconds", "Inference time")
validation_errors = Counter("ml_validation_errors_total", "Validation errors")

def init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS app_detections (
        id INTEGER PRIMARY KEY, timestamp TEXT, model_name TEXT,
        confiance REAL, latitude REAL, longitude REAL,
        rubbish INTEGER, source TEXT DEFAULT 'upload'
    )""")
    con.commit(); con.close()

@app.on_event("startup")
def startup(): init_db()

@app.get("/health")
def health(): return {"status": "ok"}

@app.get("/models")
def list_models():
    client = mlflow.MlflowClient()
    result = []
    for m in client.search_registered_models():
        v = client.get_latest_versions(m.name, stages=["Production"])
        version = v[0].version if v else "1"
        ts = datetime.datetime.fromtimestamp(m.creation_timestamp/1000).isoformat()
        result.append({"name": m.name, "version": version, "registered_at": ts})
    return result

@app.post("/predict")
async def predict(
    file: UploadFile = File(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    model_name: str = Form(...)
):
    # Validate model
    if model_name not in VALID_MODELS:
        validation_errors.inc()
        raise HTTPException(422, detail=f"Unknown model '{model_name}'. Valid: {VALID_MODELS}")
    # Validate file type
    if not file.content_type.startswith("image/"):
        validation_errors.inc()
        raise HTTPException(422, detail="File must be an image (jpeg, png, etc.)")
    # Validate GPS
    if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
        validation_errors.inc()
        raise HTTPException(422, detail="Invalid GPS coordinates")

    t0 = time.time()
    # TODO: load actual model and run inference; use stub for now
    confiance = 0.82
    rubbish = 3
    latency = time.time() - t0

    # Store in DB
    ts = datetime.datetime.utcnow().isoformat()
    con = sqlite3.connect(DB_PATH)
    con.execute("INSERT INTO app_detections (timestamp,model_name,confiance,latitude,longitude,rubbish,source) VALUES (?,?,?,?,?,?,'upload')",
                (ts, model_name, confiance, latitude, longitude, rubbish))
    con.commit(); con.close()

    # Log to JSONL
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps({"timestamp":ts,"model_name":model_name,"confiance":confiance,
                            "source":"upload","latence_ms":round(latency*1000,2)}) + "\n")

    # Metrics
    predictions_total.inc()
    predictions_by_model.labels(model=model_name).inc()
    inference_latency.observe(latency)

    return {"rubbish": rubbish, "confiance": confiance, "model_used": model_name, "timestamp": ts}

@app.get("/history")
def history():
    con = sqlite3.connect(DB_PATH)
    rows = con.execute("SELECT timestamp,model_name,confiance,latitude,longitude,rubbish,source FROM app_detections ORDER BY timestamp DESC LIMIT 100").fetchall()
    con.close()
    return [{"timestamp":r[0],"model_name":r[1],"confiance":r[2],"latitude":r[3],
             "longitude":r[4],"rubbish":r[5],"source":r[6]} for r in rows]

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)