import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"

def test_predict_invalid_file():
    r = client.post("/predict",
        data={"latitude":"48.8","longitude":"2.3","model_name":"yolov8"},
        files={"file":("req.txt", b"hello", "text/plain")})
    assert r.status_code == 422

def test_predict_invalid_gps():
    r = client.post("/predict",
        data={"latitude":"999","longitude":"2.3","model_name":"yolov8"},
        files={"file":("img.jpg", b"\xff\xd8\xff", "image/jpeg")})
    assert r.status_code == 422

def test_predict_unknown_model():
    r = client.post("/predict",
        data={"latitude":"48.8","longitude":"2.3","model_name":"unknown_model"},
        files={"file":("img.jpg", b"\xff\xd8\xff", "image/jpeg")})
    assert r.status_code == 422