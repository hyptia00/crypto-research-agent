from __future__ import annotations

import argparse
import json

from system.config import Settings
from system.pipeline import TradingIntelligence


def main() -> None:
    p = argparse.ArgumentParser(description="Lilith Trading Intelligence — analysis only")
    p.add_argument("command", choices=["scan", "doctor", "run"], nargs="?", default="scan")
    p.add_argument("--symbols", default=None, help="Comma-separated symbols")
    args = p.parse_args()
    settings = Settings.from_env()
    if args.symbols:
        settings = Settings(**{**settings.__dict__, "symbols": tuple(x.strip().upper() for x in args.symbols.split(",") if x.strip())})
    system = TradingIntelligence(settings)
    if args.command == "doctor":
        print(json.dumps({"agent_reach": system.events.doctor(), "exchanges": list(system.clients), "execution": "DISABLED"}, ensure_ascii=False, indent=2))
    elif args.command == "run":
        system.run_forever()
    else:
        print(json.dumps(system.scan_once(), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
