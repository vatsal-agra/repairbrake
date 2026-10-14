from __future__ import annotations

from dataclasses import dataclass
import itertools
import os
from pathlib import Path

import httpx

from repairbrake.paypal_client import CapturePlan, PayPalClient


@dataclass(frozen=True)
class CapStart:
    order_id: str
    approve_url: str | None
    authorization_id: str | None


class Payments:
    def start_cap(self, amount_cents: int, return_url: str, cancel_url: str) -> CapStart:
        raise NotImplementedError

    def complete_cap(self, order_id: str) -> str:
        raise NotImplementedError

    def capture(self, authorization_id: str, amount_cents: int) -> str:
        raise NotImplementedError


class MockPayments(Payments):
    """Ids always start with MOCK-. Used in tests and when live keys are absent."""

    def __init__(self) -> None:
        self._n = itertools.count(1)

    def start_cap(self, amount_cents: int, return_url: str, cancel_url: str) -> CapStart:
        n = next(self._n)
        return CapStart(f"MOCK-ORDER-{n}", None, f"MOCK-AUTH-{amount_cents}-{n}")

    def complete_cap(self, order_id: str) -> str:
        return order_id.replace("MOCK-ORDER-", "MOCK-AUTH-")

    def capture(self, authorization_id: str, amount_cents: int) -> str:
        if not authorization_id.startswith("MOCK-AUTH-"):
            raise ValueError("mock adapter only captures MOCK-AUTH ids")
        return f"MOCK-CAP-{amount_cents}-{next(self._n)}"


def _load_env() -> dict[str, str]:
    path = Path(__file__).resolve().parents[2] / ".env"
    env: dict[str, str] = {}
    if path.exists():
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    env.update({k: os.environ[k] for k in ("PAYPAL_CLIENT_ID", "PAYPAL_CLIENT_SECRET", "PAYPAL_API_BASE") if k in os.environ})
    return env


class LivePayments(Payments):
    def __init__(self, client_id: str, client_secret: str, base_url: str):
        self._id = client_id
        self._secret = client_secret
        self._base = base_url.rstrip("/")
        self._token = ""

    def _client(self) -> PayPalClient:
        r = httpx.post(
            f"{self._base}/v1/oauth2/token",
            data={"grant_type": "client_credentials"},
            auth=(self._id, self._secret),
            timeout=30.0,
        )
        r.raise_for_status()
        return PayPalClient(self._base, r.json()["access_token"])

    def start_cap(self, amount_cents: int, return_url: str, cancel_url: str) -> CapStart:
        body = self._client().create_authorize_order(amount_cents, return_url, cancel_url)
        links = {l.get("rel"): l.get("href") for l in body.get("links") or []}
        return CapStart(body["id"], links.get("approve") or links.get("payer-action"), None)

    def complete_cap(self, order_id: str) -> str:
        return self._client().authorize_order(order_id)

    def capture(self, authorization_id: str, amount_cents: int) -> str:
        result = self._client().capture_authorization(CapturePlan(authorization_id, amount_cents, final_capture=False))
        cap_id = result.get("id")
        if not cap_id:
            raise RuntimeError("capture response missing id")
        return cap_id


def payments_from_env() -> Payments:
    env = _load_env()
    cid, secret = env.get("PAYPAL_CLIENT_ID") or "", env.get("PAYPAL_CLIENT_SECRET") or ""
    if cid and secret:
        return LivePayments(cid, secret, env.get("PAYPAL_API_BASE") or "https://api-m.sandbox.paypal.com")
    return MockPayments()
