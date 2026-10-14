"""RED-first: quote consent math. Capture cannot exceed the authorized quote."""

from repairbrake.quote import Line, Quote, QuoteError


def test_capture_is_sum_of_consented_lines_only():
    q = Quote(
        authorized_cents=13800,
        lines=[
            Line("tube", 2800, consented=True),
            Line("wheel", 11000, consented=False),
        ],
    )
    assert q.capture_cents() == 2800
    assert q.uncaptured_cents() == 11000


def test_capture_must_not_exceed_authorized_cap():
    q = Quote(
        authorized_cents=2800,
        lines=[
            Line("tube", 2800, consented=True),
            Line("wheel", 11000, consented=True),
        ],
    )
    try:
        q.capture_cents()
        raise AssertionError("expected QuoteError")
    except QuoteError as e:
        assert "exceeds" in str(e).lower()


def test_empty_consent_captures_zero():
    q = Quote(
        authorized_cents=13800,
        lines=[Line("tube", 2800, consented=False)],
    )
    assert q.capture_cents() == 0
    assert q.uncaptured_cents() == 2800
