from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
client = TestClient(app)


def auth_headers():
    client.post("/auth/signup", json={"email": "a@x.com", "password": "password123"})
    r = client.post("/auth/login", json={"email": "a@x.com", "password": "password123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_flow():
    h = auth_headers()
    c = client.post("/centres/", json={"name": "City Lab", "location": "BLR"}, headers=h).json()
    t = client.post("/tests/", json={"centre_id": c["id"], "name": "CBC", "price": 299}, headers=h).json()
    future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    b = client.post("/bookings/", json={"test_id": t["id"], "appointment_at": future}, headers=h)
    assert b.status_code == 201, b.text
    bid = b.json()["id"]
    assert b.json()["status"] == "PENDING"
    p = client.post("/payments/", json={"booking_id": bid, "succeed": True}, headers=h)
    assert p.json()["status"] == "SUCCESS"
    assert client.get(f"/bookings/{bid}", headers=h).json()["status"] == "CONFIRMED"


def test_webhook_idempotent():
    h = auth_headers()
    centres = client.get("/centres/").json()
    tests = client.get("/tests/").json()
    future = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    bid = client.post("/bookings/", json={"test_id": tests[0]["id"], "appointment_at": future}, headers=h).json()["id"]
    body = {"event_id": "evt-1", "booking_id": bid, "status": "SUCCESS"}
    r1 = client.post("/payments/webhook/", json=body)
    r2 = client.post("/payments/webhook/", json=body)
    assert r1.json()["id"] == r2.json()["id"]
    assert client.get(f"/bookings/{bid}", headers=h).json()["status"] == "CONFIRMED"
    assert client.get("/bookings/", headers=h).json()


def test_edge_cases():
    h = auth_headers()
    assert client.post("/bookings/", json={"test_id": 9999, "appointment_at": "2030-01-01T10:00:00Z"}, headers=h).status_code == 404
    assert client.post("/payments/webhook/", json={"event_id": "e-x", "booking_id": 9999, "status": "SUCCESS"}).status_code == 404
    assert client.get("/bookings/9999", headers=h).status_code == 404
    assert client.get("/bookings/").status_code == 403
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    tests = client.get("/tests/").json()
    assert client.post("/bookings/", json={"test_id": tests[0]["id"], "appointment_at": past}, headers=h).status_code == 422
