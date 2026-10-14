"""Live sandbox spike. Prints capture id or fails. No fake ids.

Requires PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET in .env
(copy from .env.example). Buyer approval cannot be fully automated;
this script only proves token + capture endpoint wiring until a
saved authorization id is provided as PAYPAL_AUTHORIZATION_ID.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from repairbrake.paypal_client import CapturePlan, PayPalClient  # noqa: E402


def load_env() -> None:
    path = ROOT / ".env"
    if not path.exists():
        print("missing .env — copy .env.example and add sandbox credentials")
        sys.exit(2)
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def access_token(base: str, cid: str, secret: str) -> str:
    r = httpx.post(
        f"{base}/v1/oauth2/token",
        data={"grant_type": "client_credentials"},
        auth=(cid, secret),
        timeout=30.0,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def main() -> int:
    load_env()
    cid = os.environ.get("PAYPAL_CLIENT_ID", "")
    secret = os.environ.get("PAYPAL_CLIENT_SECRET", "")
    base = os.environ.get("PAYPAL_API_BASE", "https://api-m.sandbox.paypal.com")
    if not cid or not secret:
        print("PAYPAL_CLIENT_ID / PAYPAL_CLIENT_SECRET empty")
        return 2
    token = access_token(base, cid, secret)
    print("oauth=ok")
    auth_id = os.environ.get("PAYPAL_AUTHORIZATION_ID", "")
    if not auth_id:
        print("oauth works. set PAYPAL_AUTHORIZATION_ID after a buyer-approved AUTHORIZE order to prove partial capture.")
        return 0
    client = PayPalClient(base, token)
    result = client.capture_authorization(CapturePlan(auth_id, 2800, final_capture=False))
    cap_id = result.get("id")
    if not cap_id:
        print("no capture id", result)
        return 1
    print("capture_id", cap_id)
    print("status", result.get("status"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
