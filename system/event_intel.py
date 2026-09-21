from __future__ import annotations

import json
import os
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Iterable

import requests

from .models import Event


CRYPTO_TERMS = {"btc": "BTC", "bitcoin": "BTC", "eth": "ETH", "ethereum": "ETH", "fed": "FED", "fomc": "FED", "etf": "ETF", "sec": "SEC", "binance": "BINANCE", "bybit": "BYBIT", "okx": "OKX"}


def _score(text: str, symbol: str) -> tuple[float, float, list[str]]:
    low = text.lower()
    asset = symbol.replace("USDT", "").lower()
    tags = [v for k, v in CRYPTO_TERMS.items() if k in low]
    if asset in low and asset.upper() not in tags:
        tags.append(asset.upper())
    positive = ("approval", "approved", "inflow", "adoption", "partnership", "launch", "bullish")
    negative = ("hack", "ban", "lawsuit", "outflow", "liquidation", "exploit", "bearish")
    p = sum(x in low for x in positive)
    n = sum(x in low for x in negative)
    sentiment = max(-1.0, min(1.0, (p - n) / 3.0))
    relevance = min(1.0, 0.25 + (0.25 if asset in low else 0) + min(len(tags), 3) * 0.12 + min(abs(sentiment), 1) * 0.15)
    return relevance, sentiment, tags


class EventIntel:
    def __init__(self, enabled: bool = True, timeout: int = 12) -> None:
        self.enabled = enabled
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "Lilith-Trading-Intelligence/0.1"

    def doctor(self) -> dict:
        if not self.enabled:
            return {"enabled": False}
        try:
            p = subprocess.run(["agent-reach", "doctor", "--json"], capture_output=True, text=True, timeout=self.timeout)
            if p.returncode != 0:
                return {"installed": False, "error": p.stderr[-500:]}
            return {"installed": True, "doctor": json.loads(p.stdout)}
        except Exception as exc:
            return {"installed": False, "error": str(exc)}

    def _command(self, argv: list[str]) -> str:
        try:
            p = subprocess.run(argv, capture_output=True, text=True, timeout=self.timeout)
            if p.returncode == 0 and p.stdout.strip():
                return p.stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            pass
        return ""

    def search_web(self, query: str, limit: int = 5) -> list[Event]:
        out = self._command(["mcporter", "call", "exa.web_search_exa", f"query={query}", f"numResults={limit}"])
        if not out:
            return []
        relevance, sentiment, tags = _score(out, query.replace("USDT", ""))
        return [Event("exa", query, None, datetime.now(timezone.utc), out[:12000], relevance, sentiment, tags)]

    def read_rss(self, feeds: Iterable[str], symbol: str, limit: int = 10) -> list[Event]:
        events: list[Event] = []
        for url in feeds:
            try:
                root = ET.fromstring(self.session.get(url, timeout=self.timeout).text)
                items = root.findall(".//item") or root.findall(".//entry")
                for item in items[:limit]:
                    title = (item.findtext("title") or "").strip()
                    link = item.findtext("link") or ""
                    text = " ".join((item.findtext(x) or "") for x in ("description", "summary"))
                    relevance, sentiment, tags = _score(f"{title} {text}", symbol)
                    events.append(Event("rss", title, link, datetime.now(timezone.utc), text[:5000], relevance, sentiment, tags))
            except Exception:
                continue
        return sorted(events, key=lambda e: e.relevance, reverse=True)[:limit]

    def collect(self, symbol: str, limit: int = 10) -> list[Event]:
        if not self.enabled:
            return []
        query = f"{symbol.replace('USDT', '')} crypto market breaking news OI funding ETF Fed"
        events = self.search_web(query, max(3, limit // 2))
        feeds = [
            "https://www.coindesk.com/arc/outboundfeeds/rss/",
            "https://cointelegraph.com/rss",
        ]
        events.extend(self.read_rss(feeds, symbol, limit))
        unique: dict[tuple[str, str], Event] = {}
        for e in events:
            unique[(e.source, e.title)] = e
        return sorted(unique.values(), key=lambda e: e.relevance, reverse=True)[:limit]
