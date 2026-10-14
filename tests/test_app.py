from fastapi.testclient import TestClient

from repairbrake.app import create_app
from repairbrake.job import JobStore
from repairbrake.payments import MockPayments


def test_demo_path_captures_tube_holds_wheel():
    client = TestClient(create_app(JobStore(MockPayments())))
    created = client.post(
        "/api/jobs",
        json={"authorized_cents": 13800, "bill_text": "tube $28, I also put a new wheel on, $110"},
    )
    assert created.status_code == 200
    job = created.json()
    assert job["mock"] is True
    assert len(job["lines"]) == 2
    client.post(f"/api/jobs/{job['id']}/consent/0", json={"consented": True})
    cap = client.post(f"/api/jobs/{job['id']}/capture")
    assert cap.status_code == 200
    body = cap.json()
    assert body["capture_cents"] == 2800
    assert body["uncaptured_cents"] == 11000
    assert body["capture_id"].startswith("MOCK-CAP-")


def test_home_page_loads():
    client = TestClient(create_app(JobStore(MockPayments())))
    page = client.get("/")
    assert page.status_code == 200
    assert "RepairBrake" in page.text
    assert "MOCK-" in page.text
