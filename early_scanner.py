import json
from market.data_engine import discover_usdt_markets, get_multi_timeframe_data
from scanner.early_breakout import analyze


def scan(limit=10, min_volume=10000000):
    out = []
    for item in discover_usdt_markets(min_volume_usdt=min_volume, limit=limit):
        symbol = item['symbol']
        frames = get_multi_timeframe_data(symbol, timeframes=['4h','1h','15m'], limit=200)
        out.extend(analyze(symbol, frames))
    return sorted(out, key=lambda x: x['score'], reverse=True)


if __name__ == '__main__':
    print(json.dumps(scan(), ensure_ascii=False, indent=2))
