from __future__ import annotations

from system.exchanges import make_exchange


def main() -> int:
    statuses = {}
    for name in ("binance", "bybit", "okx"):
        try:
            c = make_exchange(name, timeout=8)
            s = c.snapshot("BTCUSDT", trade_limit=20, depth_limit=5)
            statuses[name] = {"ok": True, "price": s["price"], "oi": s["oi"], "funding": s["funding"]}
        except Exception as exc:
            statuses[name] = {"ok": False, "error": str(exc)}
    print(statuses)
    return 0 if any(v["ok"] for v in statuses.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
