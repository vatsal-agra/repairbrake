from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field

from repairbrake.job import Job, JobStore
from repairbrake.payments import payments_from_env
from repairbrake.quote import QuoteError

STORE = JobStore(payments=payments_from_env())


class CreateJob(BaseModel):
    authorized_cents: int = Field(gt=0)
    bill_text: str = Field(min_length=1)


class ConsentBody(BaseModel):
    consented: bool


def _job_json(job: Job) -> dict:
    return {
        "id": job.id,
        "authorized_cents": job.authorized_cents,
        "bill_text": job.bill_text,
        "order_id": job.order_id,
        "approve_url": job.approve_url,
        "authorization_id": job.authorization_id,
        "captured": job.captured,
        "capture_id": job.capture_id,
        "mock": (job.authorization_id or job.order_id or "").startswith("MOCK-"),
        "lines": [
            {"name": line.name, "amount_cents": line.amount_cents, "consented": line.consented}
            for line in job.lines
        ],
    }


def create_app(store: JobStore | None = None) -> FastAPI:
    jobs = store or STORE
    app = FastAPI(title="RepairBrake")

    @app.get("/", response_class=HTMLResponse)
    def home() -> str:
        return INDEX_HTML

    @app.post("/api/jobs")
    def create_job(body: CreateJob) -> dict:
        job = jobs.create(body.authorized_cents, body.bill_text)
        return _job_json(job)

    @app.post("/api/jobs/{job_id}/consent/{index}")
    def consent(job_id: str, index: int, body: ConsentBody) -> dict:
        try:
            job = jobs.set_consent(job_id, index, body.consented)
        except (KeyError, IndexError):
            raise HTTPException(404, "unknown job or line") from None
        except QuoteError as e:
            raise HTTPException(409, str(e)) from e
        return _job_json(job)

    @app.get("/return")
    def paypal_return(token: str):
        try:
            jobs.complete_order(token)
        except KeyError:
            raise HTTPException(404, "unknown PayPal order") from None
        return RedirectResponse("/?paypal=authorized")

    @app.get("/cancel")
    def paypal_cancel():
        return RedirectResponse("/?paypal=cancel")

    @app.post("/api/jobs/{job_id}/capture")
    def capture(job_id: str) -> dict:
        try:
            result = jobs.capture(job_id)
        except KeyError:
            raise HTTPException(404, "unknown job") from None
        except QuoteError as e:
            raise HTTPException(409, str(e)) from e
        return {
            "capture_id": result.capture_id,
            "authorization_id": result.authorization_id,
            "capture_cents": result.capture_cents,
            "uncaptured_cents": result.uncaptured_cents,
            "mock": result.capture_id.startswith("MOCK-"),
        }

    return app


app = create_app()

INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>RepairBrake</title>
  <style>
    :root { --ink:#1b1b18; --paper:#f4efe6; --line:#d9d0c3; --yes:#2f6f4e; --no:#9b3b2a; }
    body { margin:0; font: 16px/1.45 system-ui, sans-serif; background:var(--paper); color:var(--ink); }
    main { max-width: 40rem; margin: 2rem auto; padding: 0 1rem 4rem; }
    h1 { font-size: 1.6rem; margin: 0 0 .25rem; }
    .sub { color:#5c574e; margin-bottom: 1.5rem; }
    label { display:block; font-size:.85rem; margin: .8rem 0 .25rem; }
    input, textarea { width:100%; box-sizing:border-box; padding:.55rem .6rem; border:1px solid var(--line); background:#fff; font: inherit; }
    button { font: inherit; padding:.55rem .9rem; border:0; background:var(--ink); color:var(--paper); cursor:pointer; }
    button.ghost { background:transparent; color:var(--ink); border:1px solid var(--line); }
    .row { display:flex; gap:.5rem; align-items:center; justify-content:space-between; padding:.7rem 0; border-bottom:1px solid var(--line); }
    .amt { font-variant-numeric: tabular-nums; }
    .yes { color:var(--yes); }
    .no { color:var(--no); }
    .ids { font-family: ui-monospace, monospace; font-size:.8rem; background:#fff; padding:.75rem; border:1px solid var(--line); margin-top:1rem; }
    .warn { background:#f3e2d8; padding:.6rem .75rem; margin:1rem 0; }
  </style>
</head>
<body>
<main>
  <h1>RepairBrake</h1>
  <p class="sub">The quote is the only money that can be captured. Extras stay on hold until you tap yes.</p>
  <div class="warn" id="mode">Sandbox keys load from .env. If PayPal Checkout opens, log in with a sandbox personal account. MOCK- ids mean the mock adapter.</div>
  <label>Authorized cap (USD)
    <input id="cap" value="138.00" />
  </label>
  <label>Bill (voice note or text)
    <textarea id="bill" rows="3">tube $28, I also put a new wheel on, $110</textarea>
  </label>
  <p><button id="split">Split bill</button></p>
  <div id="lines"></div>
  <p><button id="go">Capture consented only</button></p>
  <div class="ids" id="out"></div>
</main>
<script>
const $ = (id) => document.getElementById(id);
let job = null;
function usd(c) { return '$' + (c/100).toFixed(2); }
function render() {
  if (!job) return;
  $('lines').innerHTML = job.lines.map((l,i) =>
    `<div class="row">
      <div><strong>${l.name}</strong><div class="amt">${usd(l.amount_cents)}</div></div>
      <button class="ghost" data-i="${i}">${l.consented ? 'Consented' : 'Extra / hold'}</button>
    </div>`
  ).join('');
  $('lines').querySelectorAll('button').forEach(b => b.onclick = async () => {
    const i = +b.dataset.i;
    const r = await fetch(`/api/jobs/${job.id}/consent/${i}`, {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({consented: !job.lines[i].consented})
    });
    job = await r.json();
    render();
  });
}
$('split').onclick = async () => {
  const cap = Math.round(parseFloat($('cap').value) * 100);
  const r = await fetch('/api/jobs', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({authorized_cents: cap, bill_text: $('bill').value})
  });
  job = await r.json();
  render();
  if (job.approve_url) {
    $('out').textContent = 'Opening PayPal to authorize the cap...';
    location.href = job.approve_url;
    return;
  }
  $('out').textContent = 'Authorized ' + job.authorization_id;
};
$('go').onclick = async () => {
  if (!job) return;
  const r = await fetch(`/api/jobs/${job.id}/capture`, {method:'POST'});
  const data = await r.json();
  if (!r.ok) { $('out').textContent = data.detail || JSON.stringify(data); return; }
  $('out').innerHTML = `<div class="yes">Captured ${usd(data.capture_cents)} · ${data.capture_id}</div>
    <div class="no">Held / uncaptured ${usd(data.uncaptured_cents)}</div>
    <div>Auth ${data.authorization_id}</div>`;
};
</script>
</body>
</html>
"""
