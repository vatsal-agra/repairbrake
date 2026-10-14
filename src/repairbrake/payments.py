from __future__ import annotations

from dataclasses import dataclass
import itertools


class Payments:
    def authorize(self, amount_cents: int) -> str:
        raise NotImplementedError

    def capture(self, authorization_id: str, amount_cents: int) -> str:
        raise NotImplementedError


class MockPayments(Payments):
    """Local stand-in until sandbox keys exist. Ids are always MOCK- prefixed."""

    def __init__(self) -> None:
        self._n = itertools.count(1)

    def authorize(self, amount_cents: int) -> str:
        return f"MOCK-AUTH-{amount_cents}-{next(self._n)}"

    def capture(self, authorization_id: str, amount_cents: int) -> str:
        if not authorization_id.startswith("MOCK-AUTH-"):
            raise ValueError("mock adapter only captures MOCK-AUTH ids")
        return f"MOCK-CAP-{amount_cents}-{next(self._n)}"
