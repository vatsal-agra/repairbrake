from repairbrake.job import JobStore
from repairbrake.payments import MockPayments


def test_capture_only_consented_lines_and_returns_mock_id():
    store = JobStore(payments=MockPayments())
    job = store.create(authorized_cents=13800, bill_text="tube $28, I also put a new wheel on, $110")
    store.set_consent(job.id, 0, True)
    store.set_consent(job.id, 1, False)
    result = store.capture(job.id)
    assert result.capture_cents == 2800
    assert result.uncaptured_cents == 11000
    assert result.capture_id.startswith("MOCK-CAP-")
    assert result.authorization_id.startswith("MOCK-AUTH-")


def test_refuses_capture_when_consented_exceeds_cap():
    store = JobStore(payments=MockPayments())
    job = store.create(authorized_cents=2800, bill_text="tube $28 wheel $110")
    store.set_consent(job.id, 0, True)
    store.set_consent(job.id, 1, True)
    try:
        store.capture(job.id)
        raise AssertionError("should refuse")
    except Exception as e:
        assert "exceeds" in str(e).lower()
