"""Capture body is the consented amount, never the full authorization."""

from repairbrake.paypal_client import CapturePlan, PayPalClient
import httpx


def test_capture_plan_sends_partial_amount_not_full_auth():
    plan = CapturePlan(authorization_id="AUTH-1", amount_cents=2800, final_capture=False)
    body = plan.body()
    assert body["amount"]["value"] == "28.00"
    assert body["amount"]["currency_code"] == "USD"
    assert body["final_capture"] is False


def test_client_posts_capture_to_payments_v2(httpx_mock=None):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/v2/payments/authorizations/AUTH-1/capture"
        return httpx.Response(201, json={"id": "CAP-DEMO", "status": "COMPLETED"})

    transport = httpx.MockTransport(handler)
    client = PayPalClient("https://api-m.sandbox.paypal.com", "tok", transport=transport)
    result = client.capture_authorization(CapturePlan("AUTH-1", 2800))
    assert result["id"] == "CAP-DEMO"
