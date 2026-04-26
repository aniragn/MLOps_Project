import io, requests, pytest

BASE = "http://localhost:8000"

def test_api_end_to_end():
    # Health
    assert requests.get(f"{BASE}/health").json()["status"] == "ok"
    # Models list
    models = requests.get(f"{BASE}/models").json()
    assert isinstance(models, list)
    # Predict with an inline minimal JPEG
    fake_image = io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
    r = requests.post(f"{BASE}/predict",
        data={"latitude": "48.8566", "longitude": "2.3522", "model_name": "yolov8"},
        files={"file": ("test.jpg", fake_image, "image/jpeg")})
    assert r.status_code == 200
    assert "model_used" in r.json()
