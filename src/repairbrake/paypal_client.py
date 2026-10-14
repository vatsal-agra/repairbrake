"""PayPal Orders v2 authorize then Payments v2 partial capture.

Live calls belong in scripts/spike_partial_capture.py, not in unit tests.
"""

from __future__ import annotations

from dataclasses import dataclass
import httpx


def dollars(cents: int) -> str:
    d, c = divmod(cents, 100)
    return f"{d}.{c:02d}"


@dataclass(frozen=True)
class CapturePlan:
    authorization_id: str
    amount_cents: int
    currency: str = "USD"
    final_capture: bool = False

    def body(self) -> dict:
        return {
            "amount": {"currency_code": self.currency, "value": dollars(self.amount_cents)},
            "final_capture": self.final_capture,
        }


class PayPalClient:
    def __init__(self, base_url: str, token: str, transport: httpx.BaseTransport | None = None):
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            transport=transport,
            timeout=30.0,
        )

    def create_authorize_order(self, amount_cents: int, return_url: str, cancel_url: str) -> dict:
        r = self._client.post(
            "/v2/checkout/orders",
            json={
                "intent": "AUTHORIZE",
                "purchase_units": [
                    {"amount": {"currency_code": "USD", "value": dollars(amount_cents)}}
                ],
                "application_context": {
                    "brand_name": "RepairBrake",
                    "user_action": "CONTINUE",
                    "return_url": return_url,
                    "cancel_url": cancel_url,
                },
            },
        )
        r.raise_for_status()
        return r.json()

    def authorize_order(self, order_id: str) -> str:
        r = self._client.post(f"/v2/checkout/orders/{order_id}/authorize")
        r.raise_for_status()
        body = r.json()
        units = body.get("purchase_units") or []
        auths = ((units[0].get("payments") or {}).get("authorizations") or []) if units else []
        if not auths or not auths[0].get("id"):
            raise RuntimeError("authorize response missing authorization id")
        return auths[0]["id"]

    def capture_authorization(self, plan: CapturePlan) -> dict:
        r = self._client.post(
            f"/v2/payments/authorizations/{plan.authorization_id}/capture",
            json=plan.body(),
        )
        r.raise_for_status()
        return r.json()
