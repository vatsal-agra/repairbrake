# RepairBrake — development system

**Product:** The quoted amount is the only money that can be captured. A later bill (voice or photo) is split into consented lines vs extras. Consented lines capture. Extras stay authorized and uncaptured until the customer taps yes.

This file is the process. Do not skip gates.

## Gates (hard)

1. **No UI** until `scripts/spike_partial_capture.py` prints a real sandbox capture id for an amount **less than** the authorization, then voids or leaves the rest uncaptured.
2. **No production code** without a failing test first (TDD). Exception: this DEVELOPMENT.md, LICENSE, `.env.example`.
3. **No PayPal secrets** in git. `.env` is gitignored. CI uses GitHub secrets later.
4. **No second hackathon idea** until a 3-minute demo path exists: quote → bill → split → capture id on screen.
5. **Do not fake capture ids.** If sandbox cannot partial-capture, stop and change the product. Do not splice two charges.

## Phases

| Phase | Exit criterion |
| --- | --- |
| 0 Scaffold | Repo, tests runner, quote tests red then green |
| 1 Domain | Quote/consent/capture math covered by tests |
| 2 PayPal client | Unit tests against a fake HTTP; live spike script gated on `.env` |
| 3 Spike | Live sandbox: authorize $138, capture $28, remainder not captured |
| 4 Web demo | One screen: quote, bill text, split, Capture / Hold extras |
| 5 Parse | AI splits bill text into lines; human confirms before capture |
| 6 Submit | Public GitHub, README, 3-min video, Devpost |

## Commands

```bash
python -m pytest tests -q
python scripts/spike_partial_capture.py   # needs PAYPAL_CLIENT_ID + PAYPAL_CLIENT_SECRET in .env
```

## Stack

Python 3.11, pytest, httpx. PayPal Orders v2 `intent=AUTHORIZE` then Payments v2 capture with `amount` + `final_capture`. Demo UI later (FastAPI + one HTML page). No Hermes-as-product.

## Updates

Telegram milestones only: gate passed, gate failed, or blocked on sandbox login. Not every commit.
