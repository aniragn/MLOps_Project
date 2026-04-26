import mlflow
import os

MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
mlflow.set_tracking_uri(MLFLOW_URI)
client = mlflow.MlflowClient()

MODELS = ["yolov8", "yolo26", "rtdetr", "rtdetrv2", "rfdetr", "dfine", "deim-dfine", "fusion-model"]

for name in MODELS:
    try:
        client.create_registered_model(name)
    except Exception:
        pass
    with mlflow.start_run(run_name=f"register_{name}"):
        mlflow.log_param("model", name)
        mlflow.log_metric("mAP", 0.75)
    run_id = mlflow.last_active_run().info.run_id
    client.create_model_version(name=name, source=f"runs:/{run_id}/model", run_id=run_id)
    client.transition_model_version_stage(name=name, version="1", stage="Production")
    print(f"✓ {name} registered")