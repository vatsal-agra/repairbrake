from repairbrake.parse import parse_bill


def test_splits_tube_and_wheel_voice_note():
    lines = parse_bill("tube $28, I also put a new wheel on, $110")
    assert [(line.name, line.amount_cents, line.consented) for line in lines] == [
        ("tube", 2800, False),
        ("new wheel", 11000, False),
    ]


def test_dollars_and_cents():
    lines = parse_bill("labor $40.50 and parts $9.50")
    assert [line.amount_cents for line in lines] == [4050, 950]


def test_no_amounts_returns_empty():
    assert parse_bill("all good thanks") == []
