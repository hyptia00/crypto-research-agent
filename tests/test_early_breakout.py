import pandas as pd
from scanner.early_breakout import analyze


def frame(n=100, trend=1, volume_spike=False):
    close = pd.Series(range(n), dtype=float) + 100
    if trend < 0:
        close = pd.Series(range(n, 0, -1), dtype=float) + 100
    volume = [100.0] * n
    if volume_spike:
        volume[-1] = 250.0
    return pd.DataFrame(
        {
            "open": close - 0.5,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": volume,
        }
    )


def test_no_crash_on_valid_frames():
    frames = {"4h": frame(), "1h": frame(), "15m": frame()}
    result = analyze("TESTUSDT", frames)
    assert isinstance(result, list)


def test_missing_frame_returns_empty():
    assert analyze("TESTUSDT", {"4h": frame(), "1h": frame()}) == []


def test_malformed_frame_returns_empty():
    bad = pd.DataFrame({"close": [1, 2, 3]})
    frames = {"4h": frame(), "1h": frame(), "15m": bad}
    assert analyze("TESTUSDT", frames) == []


def test_score_is_bounded_when_signal_exists():
    frames = {"4h": frame(), "1h": frame(), "15m": frame(volume_spike=True)}
    for item in analyze("TESTUSDT", frames, min_score=0):
        assert 0 <= item["score"] <= 100
        assert 0 <= item["confidence"] <= 95


def test_output_contains_risk_levels():
    frames = {"4h": frame(), "1h": frame(), "15m": frame(volume_spike=True)}
    for item in analyze("TESTUSDT", frames, min_score=0):
        assert item["trigger"] > 0
        assert item["stop"] > 0
        assert item["tp1"] > 0
        assert item["tp2"] > 0
        assert item["rr"] >= 0


def test_short_and_long_frames_do_not_crash():
    for trend in (1, -1):
        frames = {"4h": frame(trend=trend), "1h": frame(trend=trend), "15m": frame(trend=trend)}
        assert isinstance(analyze("TESTUSDT", frames, min_score=0), list)
