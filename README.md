# RepairBrake

The quoted amount is the only money PayPal is allowed to capture.

A later bill (voice or photo) is split into consented lines and extras. Consented lines capture. Upsells stay authorized and uncaptured until the customer taps yes.

PayPal AI Hackathon. Process: `DEVELOPMENT.md`.

## Run the demo (no PayPal keys)

```bash
python -m pytest tests -q
python scripts/serve.py
```

Open http://127.0.0.1:8766

Capture ids start with `MOCK-` until sandbox Client ID/Secret are in `.env`.

## Status

Quote math, bill parse, consent, mock capture, one-screen demo: tested.

Live sandbox: OAuth works. Card processing is not enabled on this app, so the cap is authorized via **PayPal Checkout** (sandbox personal account), then consented lines are partial-captured. `.env` is local only.

## License

MIT
