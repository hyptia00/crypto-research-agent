from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Alert:
    level: str
    symbol: str
    kind: str
    message: str
    data: dict[str, Any]


def detect_alerts(symbol: str, market: dict[str, Any], analysis: dict[str, Any], threshold: float = 70.0) -> list[Alert]:
    alerts: list[Alert] = []
    score = float(analysis.get("score", 50))
    if score >= threshold or score <= 100 - threshold:
        alerts.append(Alert("HIGH", symbol, "setup", f"{analysis.get('direction')} setup score {score:.1f}", analysis))
    if abs(float(market.get("oi_change_pct", 0))) >= 2:
        alerts.append(Alert("HIGH", symbol, "oi_anomaly", f"OI changed {market['oi_change_pct']:.2f}%", market))
    if abs(float(market.get("cvd_delta", 0))) > 0 and abs(float(market.get("cvd_delta_z", 0))) >= 2:
        alerts.append(Alert("HIGH", symbol, "cvd_anomaly", f"CVD delta anomaly {market['cvd_delta']:.2f}", market))
    if abs(float(market.get("orderbook_imbalance", 0))) >= 0.30:
        alerts.append(Alert("MEDIUM", symbol, "orderbook_imbalance", f"Orderbook imbalance {market['orderbook_imbalance']:.2f}", market))
    if market.get("liquidations", 0) and float(market["liquidations"]) > 0:
        alerts.append(Alert("HIGH", symbol, "liquidation_cluster", f"Liquidation notional {market['liquidations']:.0f}", market))
    return alerts
