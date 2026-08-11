"""Provider-backed, order-free research across heterogeneous markets."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from app import _fetch_twelvedata_time_series
from strategy_research import research_market


MARKETS = {
    "XAU/USD": {"asset": "gold", "execution_symbol": "XAUUSD", "spread_bps": 1.0},
    "EUR/USD": {"asset": "forex", "execution_symbol": "EURUSD", "spread_bps": 1.0},
    "GBP/USD": {"asset": "forex", "execution_symbol": "GBPUSD", "spread_bps": 1.0},
    "USD/JPY": {"asset": "forex", "execution_symbol": "USDJPY", "spread_bps": 1.0},
}


def _provider_payload(symbol, interval, candles, api_key):
    raw = _fetch_twelvedata_time_series(symbol, interval, candles, api_key)
    if raw.get("status") == "error":
        raise ValueError(str(raw.get("message") or "Provider rejected the request."))
    unique = {}
    invalid = 0
    for row in raw.get("values") or []:
        try:
            timestamp = str(row["datetime"])
            values = {key: float(row[key]) for key in ("open", "high", "low", "close")}
            if min(values.values()) <= 0 or values["high"] < max(values["open"], values["close"]) or values["low"] > min(values["open"], values["close"]):
                raise ValueError
            unique[timestamp] = values
        except (KeyError, TypeError, ValueError):
            invalid += 1
    rows = [(timestamp, unique[timestamp]) for timestamp in sorted(unique)]
    # The newest provider bar may still be forming; never research on it.
    if rows:
        rows = rows[:-1]
    if len(rows) < 200:
        raise ValueError("Provider returned fewer than 200 closed valid candles.")
    config = MARKETS[symbol]
    return {
        "symbol": symbol,
        "prices": [row[1]["close"] for row in rows],
        "opens": [row[1]["open"] for row in rows],
        "highs": [row[1]["high"] for row in rows],
        "lows": [row[1]["low"] for row in rows],
        "labels": [row[0] for row in rows],
        "candles": [{"time_utc": row[0], **row[1], "spread": 0} for row in rows],
        "market": {"research_spread_bps": config["spread_bps"], "point": 0},
        "quality": {
            "requested": candles, "valid": len(rows), "invalid_removed": invalid,
            "duplicates_removed": max(0, len(raw.get("values") or []) - invalid - len(unique)),
            "gap_count": 0, "historical_integrity": invalid == 0,
            "provider": "TwelveData", "latest_bar_excluded": True,
        },
    }


def run_multi_asset_research(symbols=None, interval="4h", candles=5_000):
    load_dotenv(Path(__file__).resolve().parent / ".env")
    api_key = os.getenv("TWELVEDATA_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("TWELVEDATA_API_KEY is not configured.")
    symbols = list(symbols or MARKETS)
    report = {"execution_mode": "research_only", "interval": interval, "markets": []}
    for symbol in symbols:
        config = MARKETS.get(symbol)
        if not config:
            report["markets"].append({"symbol": symbol, "qualified": False, "error": "unsupported_market"})
            continue
        try:
            payload = _provider_payload(symbol, interval, candles, api_key)
            result = research_market(payload)
            report["markets"].append({
                "symbol": symbol, "asset": config["asset"],
                "execution_symbol": config["execution_symbol"], "interval": interval,
                **result,
            })
        except Exception as exc:
            report["markets"].append({
                "symbol": symbol, "asset": config["asset"], "interval": interval,
                "qualified": False, "error": str(exc)[:300],
            })
    report["qualified_count"] = sum(bool(item.get("qualified")) for item in report["markets"])
    report["orders_sent"] = 0
    return report


def main():
    parser = argparse.ArgumentParser(description="Order-free multi-asset strategy research")
    parser.add_argument("--symbols", nargs="+", default=list(MARKETS))
    parser.add_argument("--interval", default="4h")
    parser.add_argument("--candles", type=int, default=5_000)
    parser.add_argument("--output", default="data/multi-asset-research-latest.json")
    args = parser.parse_args()
    report = run_multi_asset_research(args.symbols, args.interval, args.candles)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
