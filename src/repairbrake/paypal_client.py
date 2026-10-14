"""PayPal Orders v2 authorize then Payments v2 partial capture.

Live calls belong in scripts/spike_partial_capture.py, not in unit tests.
"""

from __future__ import annotations

from dataclasses import dataclass
import httpx


@dataclass(frozen=True)
class CapturePlan:
    authorization_id: str
    amount_cents: int
    currency: str = "USD"
    final_capture: bool = False

    def body(self) -> dict:
        dollars, cents = divmod(self.amount_cents, 100)
        return {
            "amount": {
                "currency_code": self.currency,
                "value": f"{dollars}.{cents:02d}",
            },
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

    def capture_authorization(self, plan: CapturePlan) -> dict:
        r = self._client.post(
            f"/v2/payments/authorizations/{plan.authorization_id}/capture",
            json=plan.body(),
        )
        r.raise_for_status()
        return r.json()
