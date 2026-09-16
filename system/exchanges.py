from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import time
import requests


class ExchangeError(RuntimeError):
    pass


@dataclass
class ExchangeClient:
    name: str
    base_url: str
    timeout: int = 10

    def __post_init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Lilith-Trading-Intelligence/0.1"})

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        try:
            r = self.session.get(self.base_url + path, params=params, timeout=self.timeout)
            r.raise_for_status()
            return r.json()
        except Exception as exc:
            raise ExchangeError(f"{self.name} GET {path}: {exc}") from exc

    def candles(self, symbol: str, interval: str = "15m", limit: int = 250) -> list[list[Any]]:
        raise NotImplementedError

    def snapshot(self, symbol: str, trade_limit: int = 1000, depth_limit: int = 50) -> dict[str, Any]:
        raise NotImplementedError


class Binance(ExchangeClient):
    def __init__(self, timeout: int = 10) -> None:
        super().__init__("binance", "https://fapi.binance.com", timeout)

    def candles(self, symbol: str, interval: str = "15m", limit: int = 250) -> list[list[Any]]:
        return self.get("/fapi/v1/klines", {"symbol": symbol, "interval": interval, "limit": limit})

    def snapshot(self, symbol: str, trade_limit: int = 1000, depth_limit: int = 50) -> dict[str, Any]:
        price = self.get("/fapi/v1/ticker/price", {"symbol": symbol})
        oi = self.get("/fapi/v1/openInterest", {"symbol": symbol})
        funding = self.get("/fapi/v1/premiumIndex", {"symbol": symbol})
        depth = self.get("/fapi/v1/depth", {"symbol": symbol, "limit": depth_limit})
        trades = self.get("/fapi/v1/aggTrades", {"symbol": symbol, "limit": min(trade_limit, 1000)})
        liquidations = self.get("/fapi/v1/allForceOrders", {"symbol": symbol, "limit": 100})
        return {"price": float(price["price"]), "oi": float(oi["openInterest"]), "funding": float(funding["lastFundingRate"]), "depth": depth, "trades": trades, "liquidations": liquidations}


class Bybit(ExchangeClient):
    def __init__(self, timeout: int = 10) -> None:
        super().__init__("bybit", "https://api.bybit.com", timeout)

    def candles(self, symbol: str, interval: str = "15m", limit: int = 250) -> list[list[Any]]:
        interval_map = {"1m": "1", "5m": "5", "15m": "15", "1h": "60", "4h": "240"}
        data = self.get("/v5/market/kline", {"category": "linear", "symbol": symbol, "interval": interval_map[interval], "limit": min(limit, 1000)})
        return list(reversed(data["result"]["list"]))

    def snapshot(self, symbol: str, trade_limit: int = 1000, depth_limit: int = 50) -> dict[str, Any]:
        ticker = self.get("/v5/market/tickers", {"category": "linear", "symbol": symbol})["result"]["list"][0]
        oi = self.get("/v5/market/open-interest", {"category": "linear", "symbol": symbol, "intervalTime": "5min", "limit": 1})["result"]["list"][0]
        funding = self.get("/v5/market/funding/history", {"category": "linear", "symbol": symbol, "limit": 1})["result"]["list"][0]
        depth = self.get("/v5/market/orderbook", {"category": "linear", "symbol": symbol, "limit": depth_limit})["result"]
        trades = self.get("/v5/market/recent-trade", {"category": "linear", "symbol": symbol, "limit": min(trade_limit, 1000)})["result"]["list"]
        return {"price": float(ticker["lastPrice"]), "oi": float(oi["openInterest"]), "funding": float(funding["fundingRate"]), "depth": {"bids": depth["b"], "asks": depth["a"]}, "trades": trades, "liquidations": []}


class OKX(ExchangeClient):
    def __init__(self, timeout: int = 10) -> None:
        super().__init__("okx", "https://www.okx.com", timeout)

    @staticmethod
    def inst(symbol: str) -> str:
        return symbol.replace("USDT", "-USDT-SWAP")

    def candles(self, symbol: str, interval: str = "15m", limit: int = 250) -> list[list[Any]]:
        bar = {"1m": "1m", "5m": "5m", "15m": "15m", "1h": "1H", "4h": "4H"}[interval]
        data = self.get("/api/v5/market/candles", {"instId": self.inst(symbol), "bar": bar, "limit": min(limit, 300)})
        return list(reversed(data["data"]))

    def snapshot(self, symbol: str, trade_limit: int = 1000, depth_limit: int = 50) -> dict[str, Any]:
        inst = self.inst(symbol)
        ticker = self.get("/api/v5/market/ticker", {"instId": inst})["data"][0]
        oi = self.get("/api/v5/public/open-interest", {"instType": "SWAP", "instId": inst})["data"][0]
        funding = self.get("/api/v5/public/funding-rate", {"instId": inst})["data"][0]
        depth = self.get("/api/v5/market/books", {"instId": inst, "sz": min(depth_limit, 400)})["data"][0]
        trades = self.get("/api/v5/market/trades", {"instId": inst, "limit": min(trade_limit, 500)})["data"]
        return {"price": float(ticker["last"]), "oi": float(oi["oi"]), "funding": float(funding["fundingRate"]), "depth": {"bids": depth["bids"], "asks": depth["asks"]}, "trades": trades, "liquidations": []}


def make_exchange(name: str, timeout: int = 10) -> ExchangeClient:
    name = name.lower()
    if name == "binance":
        return Binance(timeout)
    if name == "bybit":
        return Bybit(timeout)
    if name == "okx":
        return OKX(timeout)
    raise ValueError(f"unsupported exchange: {name}")


def trade_delta(exchange: str, trades: list[dict[str, Any]]) -> float:
    delta = 0.0
    for t in trades:
        if exchange == "binance":
            qty = float(t.get("q", 0))
            delta += -qty if bool(t.get("m", False)) else qty
        elif exchange == "bybit":
            qty = float(t.get("size", 0))
            delta += qty if str(t.get("side", "Buy")).lower() == "buy" else -qty
        else:
            qty = float(t.get("sz", 0))
            delta += qty if str(t.get("side", "buy")).lower() == "buy" else -qty
    return delta


def depth_imbalance(depth: dict[str, Any]) -> tuple[float, float, float]:
    bids = depth.get("bids", depth.get("b", []))
    asks = depth.get("asks", depth.get("a", []))
    bid = sum(float(x[0]) * float(x[1]) for x in bids)
    ask = sum(float(x[0]) * float(x[1]) for x in asks)
    total = bid + ask
    return bid, ask, ((bid - ask) / total if total else 0.0)
