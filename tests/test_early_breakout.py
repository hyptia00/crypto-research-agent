import pandas as pd
from scanner.early_breakout import analyze


def frame(n=100):
    close = pd.Series(range(n), dtype=float) + 100
    return pd.DataFrame({'open': close-0.5, 'high': close+1, 'low': close-1, 'close': close, 'volume': [100.0]*n})


def test_no_crash_on_valid_frames():
    frames = {'4h': frame(), '1h': frame(), '15m': frame()}
    result = analyze('TESTUSDT', frames)
    assert isinstance(result, list)


def test_missing_frame_returns_empty():
    assert analyze('TESTUSDT', {'4h': frame(), '1h': frame()}) == []
