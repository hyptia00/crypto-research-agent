from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from system.exchanges import make_exchange


def check(name: str) -> tuple[str, dict]:
    try:
        c = make_exchange(name, timeout=5)
        s = c.snapshot("BTCUSDT", trade_limit=5, depth_limit=5)
        return name, {"ok": True, "price": s["price"], "oi": s["oi"], "funding": s["funding"]}
    except Exception as exc:
        return name, {"ok": False, "error": str(exc)}


def main() -> int:
    statuses = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(check, name) for name in ("binance", "bybit", "okx")]
        for future in as_completed(futures):
            name, status = future.result()
            statuses[name] = status
    print(statuses)
    return 0 if any(v["ok"] for v in statuses.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
