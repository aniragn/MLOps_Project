import requests, pytest

BASE = "http://localhost:8000"

def test_api_end_to_end():
    # Health
    assert requests.get(f"{BASE}/health").json()["status"] == "ok"
    # Models list
    models = requests.get(f"{BASE}/models").json()
    assert len(models) == 8
    # Predict
    with open("test_image.jpg", "rb") as f:
        r = requests.post(f"{BASE}/predict",
            data={"latitude":"48.8566","longitude":"2.3522","model_name":"yolov8"},
            files={"file": f})
    assert r.status_code == 200
    assert "model_used" in r.json()