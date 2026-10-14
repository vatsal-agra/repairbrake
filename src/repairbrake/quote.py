from dataclasses import dataclass


class QuoteError(ValueError):
    pass


@dataclass(frozen=True)
class Line:
    name: str
    amount_cents: int
    consented: bool


@dataclass(frozen=True)
class Quote:
    authorized_cents: int
    lines: list[Line]

    def capture_cents(self) -> int:
        total = sum(line.amount_cents for line in self.lines if line.consented)
        if total > self.authorized_cents:
            raise QuoteError(
                f"consented capture {total} exceeds authorized cap {self.authorized_cents}"
            )
        return total

    def uncaptured_cents(self) -> int:
        return sum(line.amount_cents for line in self.lines if not line.consented)
