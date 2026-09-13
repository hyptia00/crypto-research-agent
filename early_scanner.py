import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from market.data_engine import discover_usdt_markets, get_multi_timeframe_data
from scanner.early_breakout import analyze


def scan(limit=10, min_volume=10_000_000, workers=4):
    markets = discover_usdt_markets(min_volume_usdt=min_volume, limit=limit)

    def one(item):
        symbol = item["symbol"]
        frames = get_multi_timeframe_data(
            symbol, timeframes=["4h", "1h", "15m"], limit=200
        )
        return analyze(symbol, frames)

    out = []
    with ThreadPoolExecutor(max_workers=max(1, int(workers))) as pool:
        futures = [pool.submit(one, item) for item in markets]
        for future in as_completed(futures):
            try:
                out.extend(future.result())
            except Exception as exc:
                print(f"SCAN ERROR: {exc}")

    return sorted(out, key=lambda x: (x["score"], x["confidence"]), reverse=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Early breakout information scanner")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--min-volume", type=float, default=10_000_000)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    print(json.dumps(scan(args.limit, args.min_volume, args.workers), ensure_ascii=False, indent=2))
