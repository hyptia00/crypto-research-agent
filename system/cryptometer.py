from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import requests


@dataclass(frozen=True)
class CryptoMeterConfig:
    api_key: str
    base_url: str = "https://api.cryptometer.io"
    timeout_seconds: int = 10
    cache_seconds: int = 300


class CryptoMeterClient:
    """Small, cached CryptoMeter API client. Never logs or exposes the API key."""

    def __init__(self, config: CryptoMeterConfig) -> None:
        self.config = config
        self._cache: dict[tuple[str, tuple[tuple[str, str], ...]], tuple[float, Any]] = {}

    @property
    def enabled(self) -> bool:
        return bool(self.config.api_key)

    @staticmethod
    def _symbol(symbol: str) -> str:
        return symbol.upper().replace("USDT", "").replace("-USDT", "").lower()

    @staticmethod
    def _pair(symbol: str) -> str:
        return f"{CryptoMeterClient._symbol(symbol).upper()}-USDT"

    def _get(self, path: str, params: dict[str, str] | None = None) -> Any:
        if not self.enabled:
            return None
        params = dict(params or {})
        params["api_key"] = self.config.api_key
        key = (path, tuple(sorted((str(k), str(v)) for k, v in params.items() if k != "api_key")))
        now = time.monotonic()
        cached = self._cache.get(key)
        if cached and now - cached[0] < self.config.cache_seconds:
            return cached[1]
        try:
            response = requests.get(
                f"{self.config.base_url.rstrip('/')}/{path.lstrip('/')}",
                params=params,
                timeout=self.config.timeout_seconds,
            )
            if response.status_code in {401, 403, 429}:
                return {"success": "false", "error": True, "status_code": response.status_code}
            response.raise_for_status()
            data = response.json()
            self._cache[key] = (now, data)
            return data
        except (requests.RequestException, ValueError):
            return None

    def rapid_movements(self, symbol: str) -> list[dict[str, Any]]:
        payload = self._get("/rapid-movements-v2/", {"symbol": self._symbol(symbol)})
        return list(payload.get("data", [])) if isinstance(payload, dict) else []

    def ai_screener(self) -> list[dict[str, Any]]:
        payload = self._get("/ai-screener/", {"type": "latest"})
        return list(payload.get("data", [])) if isinstance(payload, dict) else []

    def ai_for_symbol(self, symbol: str) -> dict[str, Any] | None:
        target = self._symbol(symbol).upper()
        rows = [x for x in self.ai_screener() if str(x.get("symbol", "")).upper() == target]
        if not rows:
            return None
        return rows[0]

    def volume_flow(self, timeframe: str = "4h") -> dict[str, Any]:
        payload = self._get("/volume-flow/", {"timeframe": timeframe})
        return payload if isinstance(payload, dict) else {}

    def volume_flow_for_symbol(self, symbol: str, timeframe: str = "4h") -> dict[str, float]:
        data = self.volume_flow(timeframe).get("data", {}) if self.enabled else {}
        target = self._symbol(symbol).upper()
        result = {"inflow": 0.0, "outflow": 0.0, "netflow": 0.0}
        if not isinstance(data, dict):
            return result
        for key, target_value in (("inflow", 1), ("outflow", 1), ("netflow", 1)):
            for row in data.get(key, []) or []:
                if str(row.get("to", "")).upper() == target or str(row.get("from", "")).upper() == target:
                    result[key] += float(row.get("volume", 0) or 0)
        result["netflow"] = result["inflow"] - result["outflow"]
        return result

    def ls_ratio(self, symbol: str, timeframe: str = "4h", exchange: str = "binance_futures") -> dict[str, Any] | None:
        payload = self._get(
            "/ls-ratio/",
            {"e": exchange, "pair": self._pair(symbol).lower(), "timeframe": timeframe},
        )
        rows = payload.get("data", []) if isinstance(payload, dict) else []
        return rows[-1] if rows else None

    def liquidation_data(self, symbol: str) -> dict[str, float]:
        payload = self._get("/liquidation-data-v2/", {"symbol": self._symbol(symbol)})
        rows = payload.get("data", []) if isinstance(payload, dict) else []
        totals = {"longs": 0.0, "shorts": 0.0}
        for row in rows:
            if not isinstance(row, dict):
                continue
            for venue in row.values():
                if isinstance(venue, dict):
                    totals["longs"] += float(venue.get("longs", 0) or 0)
                    totals["shorts"] += float(venue.get("shorts", 0) or 0)
        return totals

    def signal(self, symbol: str) -> dict[str, Any]:
        if not self.enabled:
            return {"enabled": False}
        rapid = self.rapid_movements(symbol)
        ai = self.ai_for_symbol(symbol)
        flow = self.volume_flow_for_symbol(symbol)
        ls = self.ls_ratio(symbol)
        liq = self.liquidation_data(symbol)
        rapid_up = sum(1 for x in rapid if str(x.get("direction", "")).lower() == "up")
        rapid_down = sum(1 for x in rapid if str(x.get("direction", "")).lower() == "down")
        rapid_score = max(-1.0, min(1.0, (rapid_up - rapid_down) / max(1, rapid_up + rapid_down)))
        ai_score = 1.0 if ai and str(ai.get("side", "")).upper() == "BUY" else -1.0 if ai else 0.0
        ls_ratio = float(ls.get("ratio", 0) or 0) if ls else 0.0
        ls_score = max(-1.0, min(1.0, (ls_ratio - 1.0) / max(1.0, ls_ratio + 1.0))) if ls_ratio else 0.0
        flow_score = 1.0 if flow["netflow"] > 0 else -1.0 if flow["netflow"] < 0 else 0.0
        combined = max(-1.0, min(1.0, 0.35 * rapid_score + 0.30 * ai_score + 0.20 * flow_score + 0.15 * ls_score))
        return {
            "enabled": True,
            "score": round(combined, 4),
            "rapid": rapid,
            "ai": ai,
            "volume_flow": flow,
            "ls_ratio": ls,
            "liquidations": liq,
        }
