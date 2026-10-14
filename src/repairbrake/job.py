from __future__ import annotations

from dataclasses import dataclass
import uuid

from repairbrake.parse import parse_bill
from repairbrake.payments import Payments
from repairbrake.quote import Line, Quote, QuoteError


@dataclass
class Job:
    id: str
    authorized_cents: int
    bill_text: str
    lines: list[Line]
    order_id: str
    approve_url: str | None
    authorization_id: str | None
    captured: bool = False
    capture_id: str | None = None


@dataclass(frozen=True)
class CaptureResult:
    capture_id: str
    authorization_id: str
    capture_cents: int
    uncaptured_cents: int


class JobStore:
    def __init__(self, payments: Payments):
        self._payments = payments
        self._jobs: dict[str, Job] = {}
        self._by_order: dict[str, str] = {}

    def create(self, authorized_cents: int, bill_text: str, return_url: str = "http://127.0.0.1:8766/return", cancel_url: str = "http://127.0.0.1:8766/cancel") -> Job:
        lines = parse_bill(bill_text)
        start = self._payments.start_cap(authorized_cents, return_url, cancel_url)
        job = Job(
            id=str(uuid.uuid4()),
            authorized_cents=authorized_cents,
            bill_text=bill_text,
            lines=lines,
            order_id=start.order_id,
            approve_url=start.approve_url,
            authorization_id=start.authorization_id,
        )
        self._jobs[job.id] = job
        self._by_order[job.order_id] = job.id
        return job

    def get(self, job_id: str) -> Job:
        return self._jobs[job_id]

    def complete_order(self, order_id: str) -> Job:
        job = self._jobs[self._by_order[order_id]]
        job.authorization_id = self._payments.complete_cap(order_id)
        return job

    def set_consent(self, job_id: str, index: int, consented: bool) -> Job:
        job = self._jobs[job_id]
        if job.captured:
            raise QuoteError("already captured")
        line = job.lines[index]
        job.lines[index] = Line(line.name, line.amount_cents, consented)
        return job

    def capture(self, job_id: str) -> CaptureResult:
        job = self._jobs[job_id]
        if not job.authorization_id:
            raise QuoteError("cap is not authorized yet")
        quote = Quote(job.authorized_cents, list(job.lines))
        amount = quote.capture_cents()
        cap_id = self._payments.capture(job.authorization_id, amount)
        job.captured = True
        job.capture_id = cap_id
        return CaptureResult(
            capture_id=cap_id,
            authorization_id=job.authorization_id,
            capture_cents=amount,
            uncaptured_cents=quote.uncaptured_cents(),
        )
