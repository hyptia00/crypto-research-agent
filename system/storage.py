from __future__ import annotations

import json
import os
import sqlite3
from typing import Any


class Store:
    def __init__(self, path: str) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            exchange TEXT NOT NULL,
            symbol TEXT NOT NULL,
            payload TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            source TEXT NOT NULL,
            title TEXT NOT NULL,
            url TEXT,
            payload TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            symbol TEXT NOT NULL,
            payload TEXT NOT NULL
        );
        """)
        self.conn.commit()

    def add_snapshot(self, ts: str, exchange: str, symbol: str, payload: dict[str, Any]) -> None:
        self.conn.execute("INSERT INTO snapshots(ts,exchange,symbol,payload) VALUES(?,?,?,?)", (ts, exchange, symbol, json.dumps(payload, ensure_ascii=False)))
        self.conn.commit()

    def previous_snapshot(self, exchange: str, symbol: str) -> dict[str, Any] | None:
        row = self.conn.execute("SELECT payload FROM snapshots WHERE exchange=? AND symbol=? ORDER BY id DESC LIMIT 1", (exchange, symbol)).fetchone()
        return json.loads(row[0]) if row else None

    def add_event(self, ts: str, source: str, title: str, url: str | None, payload: dict[str, Any]) -> None:
        self.conn.execute("INSERT INTO events(ts,source,title,url,payload) VALUES(?,?,?,?,?)", (ts, source, title, url, json.dumps(payload, ensure_ascii=False)))
        self.conn.commit()

    def add_analysis(self, ts: str, symbol: str, payload: dict[str, Any]) -> None:
        self.conn.execute("INSERT INTO analyses(ts,symbol,payload) VALUES(?,?,?)", (ts, symbol, json.dumps(payload, ensure_ascii=False)))
        self.conn.commit()
