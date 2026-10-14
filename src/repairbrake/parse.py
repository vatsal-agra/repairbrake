from __future__ import annotations

import re

from repairbrake.quote import Line

_MONEY = re.compile(r"\$\s*(?P<dollars>\d{1,6}(?:,\d{3})*)(?:\.(?P<cents>\d{2}))?")
_NOISE = re.compile(
    r"\b(i also put a|i put a|i also|also|put a|on)\b",
    re.I,
)


def _cents(dollars: str, cents: str | None) -> int:
    return int(dollars.replace(",", "")) * 100 + int(cents or "0")


def _label(raw: str) -> str:
    text = _NOISE.sub(" ", raw)
    text = re.sub(r"[\s,;:.-]+", " ", text).strip().lower()
    return text or "item"


def parse_bill(text: str) -> list[Line]:
    """Split a spoken or typed bill into unconsented lines. Human confirms later."""
    lines: list[Line] = []
    prev = 0
    for m in _MONEY.finditer(text):
        lines.append(Line(_label(text[prev:m.start()]), _cents(m.group("dollars"), m.group("cents")), False))
        prev = m.end()
    return lines
