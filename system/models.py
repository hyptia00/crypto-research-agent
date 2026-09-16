from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class MarketSnapshot:
    exchange: str
    symbol: str
    timestamp: datetime
    price: float
    oi: float | None = None
    funding: float | None = None
    cvd: float | None = None
    cvd_delta: float | None = None
    volume: float | None = None
    orderbook_imbalance: float | None = None
    bid_depth: float | None = None
    ask_depth: float | None = None
    liquidations: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass
class Event:
    source: str
    title: str
    url: str | None
    published_at: datetime | None
    text: str
    relevance: float = 0.0
    sentiment: float = 0.0
    tags: list[str] = field(default_factory=list)


@dataclass
class AnalysisResult:
    symbol: str
    timestamp: datetime
    direction: str
    score: float
    confidence: float
    status: str
    reasons: list[str]
    invalidation: float | None
    targets: list[float]
    market: dict[str, Any]
    events: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data
