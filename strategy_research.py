"""Read-only MT5 walk-forward research for the demo challenge.

This module never sends orders.  It selects parameters on the oldest 60% of
closed candles, checks them on the next 20%, and reports the untouched final
20% separately so an attractive training result cannot unlock trading alone.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import statistics
from typing import Any

from analytics_engine import run_ohlc_backtest
from mt5_connector import MT5Connector


DEFAULT_SYMBOLS = ("EUR/USD", "GBP/USD", "USD/JPY", "XAU/USD")
DEFAULT_INTERVALS = ("15min", "30min", "1h", "4h")


def _parameter_grid():
    macd_options = ((8, 21, 5), (12, 26, 9), (16, 32, 9))
    return itertools.product(
        (9, 14, 21),
        macd_options,
        (3, 6, 12),
        (1.0, 1.5, 2.0),
        (1.5, 2.0, 2.5),
    )


def _slice_payload(payload: dict[str, Any], start: int, end: int):
    return {
        "opens": payload["opens"][start:end],
        "highs": payload["highs"][start:end],
        "lows": payload["lows"][start:end],
        "closes": payload["prices"][start:end],
        "timestamps": payload["labels"][start:end],
    }


def _historical_spread_bps(payload: dict[str, Any]) -> float:
    point = float(payload.get("market", {}).get("point") or 0)
    rows = payload.get("candles") or []
    estimates = [
        float(row.get("spread") or 0) * point / float(row["close"]) * 10_000
        for row in rows
        if point > 0 and float(row.get("close") or 0) > 0
    ]
    # Never assume friction below 1 bps when broker history omits spread.
    return round(max(1.0, statistics.median(estimates) if estimates else 0.0), 4)


def _run(segment: dict[str, Any], parameters: dict[str, Any], spread_bps: float):
    return run_ohlc_backtest(
        segment["opens"],
        segment["highs"],
        segment["lows"],
        segment["closes"],
        timestamps=segment["timestamps"],
        **parameters,
        risk_percent=0.1,
        spread_bps=spread_bps,
        commission_bps_per_side=0.2,
        slippage_bps_per_side=0.3,
        max_drawdown_pct=50,
        max_daily_loss_pct=1.0,
        max_trades_per_day=3,
        max_consecutive_losses=2,
        loss_cooldown_bars=3,
    )


def _score(result: dict[str, Any]) -> float:
    if result["trade_count"] < 25:
        return -math.inf
    profit_factor = float(result.get("profit_factor") or 0)
    sharpe = float(result.get("sharpe") or 0)
    return (
        float(result["total_return_pct"])
        - (0.75 * float(result["max_drawdown_pct"]))
        + (3 * min(profit_factor, 3))
        + min(sharpe, 3)
    )


def _compact(result: dict[str, Any]) -> dict[str, Any]:
    return {
        key: result.get(key)
        for key in (
            "trade_count",
            "win_rate",
            "total_return_pct",
            "profit_factor",
            "expectancy_pct",
            "max_drawdown_pct",
            "sharpe",
            "halted_reason",
            "cooldown_count",
        )
    }


def _passes(train: dict[str, Any], validation: dict[str, Any], test: dict[str, Any]) -> bool:
    return all(
        (
            train["trade_count"] >= 25,
            validation["trade_count"] >= 8,
            test["trade_count"] >= 8,
            float(train["total_return_pct"]) > 0,
            float(validation["total_return_pct"]) > 0,
            float(test["total_return_pct"]) > 0,
            float(train.get("profit_factor") or 0) >= 1.10,
            float(validation.get("profit_factor") or 0) >= 1.10,
            float(test.get("profit_factor") or 0) >= 1.10,
            float(validation["max_drawdown_pct"]) <= 8,
            float(test["max_drawdown_pct"]) <= 8,
        )
    )


def research_market(payload: dict[str, Any]) -> dict[str, Any]:
    length = len(payload["prices"])
    train_end = int(length * 0.60)
    validation_end = int(length * 0.80)
    segments = {
        "train": _slice_payload(payload, 0, train_end),
        "validation": _slice_payload(payload, train_end, validation_end),
        "test": _slice_payload(payload, validation_end, length),
    }
    spread_bps = _historical_spread_bps(payload)

    best_parameters = None
    best_train = None
    best_score = -math.inf
    for rsi_period, macd, holding_bars, atr_multiple, reward_risk in _parameter_grid():
        parameters = {
            "rsi_period": rsi_period,
            "macd_short": macd[0],
            "macd_long": macd[1],
            "macd_signal": macd[2],
            "holding_bars": holding_bars,
            "atr_stop_multiple": atr_multiple,
            "reward_risk": reward_risk,
        }
        result = _run(segments["train"], parameters, spread_bps)
        score = _score(result)
        if score > best_score:
            best_score = score
            best_parameters = parameters
            best_train = result

    if best_parameters is None or best_train is None:
        return {"qualified": False, "reason": "no_train_candidate"}

    validation = _run(segments["validation"], best_parameters, spread_bps)
    test = _run(segments["test"], best_parameters, spread_bps)
    data_quality = payload.get("quality") or {}
    return {
        "qualified": bool(
            data_quality.get("historical_integrity", data_quality.get("safe_for_signal"))
        ) and _passes(best_train, validation, test),
        "candles": length,
        "spread_bps_used": spread_bps,
        "data_quality": data_quality,
        "parameters": best_parameters,
        "train": _compact(best_train),
        "validation": _compact(validation),
        "test": _compact(test),
    }


def run_research(symbols=DEFAULT_SYMBOLS, intervals=DEFAULT_INTERVALS, candles=5_000):
    report: dict[str, Any] = {"execution_mode": "research_only", "markets": []}
    connector = MT5Connector()
    with connector.session(require_demo=True) as (active, _):
        for symbol in symbols:
            for interval in intervals:
                try:
                    payload = active.fetch_candles(symbol, interval, candles)
                    result = research_market(payload)
                    report["markets"].append(
                        {"symbol": payload["symbol"], "interval": interval, **result}
                    )
                except Exception as exc:  # Keep one unavailable market from ending the study.
                    report["markets"].append(
                        {"symbol": symbol, "interval": interval, "qualified": False, "error": str(exc)}
                    )
    report["qualified_count"] = sum(bool(item.get("qualified")) for item in report["markets"])
    report["orders_sent"] = 0
    return report


def main():
    parser = argparse.ArgumentParser(description="Read-only MT5 walk-forward research")
    parser.add_argument("--candles", type=int, default=5_000)
    parser.add_argument("--symbols", nargs="+", default=list(DEFAULT_SYMBOLS))
    parser.add_argument("--intervals", nargs="+", default=list(DEFAULT_INTERVALS))
    args = parser.parse_args()
    print(json.dumps(run_research(args.symbols, args.intervals, args.candles), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
