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
    authorization_id: str
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

    def create(self, authorized_cents: int, bill_text: str) -> Job:
        lines = parse_bill(bill_text)
        auth = self._payments.authorize(authorized_cents)
        job = Job(
            id=str(uuid.uuid4()),
            authorized_cents=authorized_cents,
            bill_text=bill_text,
            lines=lines,
            authorization_id=auth,
        )
        self._jobs[job.id] = job
        return job

    def get(self, job_id: str) -> Job:
        return self._jobs[job_id]

    def set_consent(self, job_id: str, index: int, consented: bool) -> Job:
        job = self._jobs[job_id]
        if job.captured:
            raise QuoteError("already captured")
        line = job.lines[index]
        job.lines[index] = Line(line.name, line.amount_cents, consented)
        return job

    def capture(self, job_id: str) -> CaptureResult:
        job = self._jobs[job_id]
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
