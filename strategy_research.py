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
from pathlib import Path
from typing import Any

from analytics_engine import monte_carlo_trade_risk, run_ohlc_backtest
from mt5_connector import MT5Connector


DEFAULT_SYMBOLS = ("EUR/USD", "GBP/USD", "USD/JPY", "XAU/USD")
DEFAULT_INTERVALS = ("15min", "30min", "1h", "4h")


def _parameter_grid():
    common = itertools.product((3, 6, 12), (1.0, 1.5, 2.0), (1.5, 2.0, 2.5))
    for rsi_period, macd, (holding, atr, reward) in itertools.product(
        (9, 14, 21), ((8, 21, 5), (12, 26, 9), (16, 32, 9)), common
    ):
        yield {
            "strategy_family": "rsi_macd",
            "strategy_options": {},
            "rsi_period": rsi_period, "macd_short": macd[0],
            "macd_long": macd[1], "macd_signal": macd[2],
            "holding_bars": holding, "atr_stop_multiple": atr, "reward_risk": reward,
        }
    for fast, slow, holding, atr, reward in itertools.product(
        (8, 13, 21), (34, 55, 89), (3, 6, 12), (1.0, 1.5), (1.5, 2.0, 2.5)
    ):
        if fast >= slow:
            continue
        yield {
            "strategy_family": "ema_pullback",
            "strategy_options": {"fast_period": fast, "slow_period": slow},
            "holding_bars": holding, "atr_stop_multiple": atr, "reward_risk": reward,
        }
    for fast, slow, minimum_efficiency, maximum_volatility_ratio, holding, reward in itertools.product(
        (8, 13, 21), (34, 55, 89), (0.15, 0.25, 0.35),
        (1.25, 1.75), (6, 12), (2.0, 2.5),
    ):
        if fast >= slow:
            continue
        yield {
            "strategy_family": "regime_ema_pullback",
            "strategy_options": {
                "fast_period": fast, "slow_period": slow,
                "efficiency_window": 20,
                "minimum_efficiency": minimum_efficiency,
                "volatility_window": 20, "volatility_baseline": 100,
                "maximum_volatility_ratio": maximum_volatility_ratio,
            },
            "holding_bars": holding, "atr_stop_multiple": 1.5,
            "reward_risk": reward,
        }
    for lookback, holding, atr, reward in itertools.product(
        (20, 40, 80), (6, 12, 24), (1.0, 1.5, 2.0), (1.5, 2.0, 3.0)
    ):
        yield {
            "strategy_family": "donchian_breakout",
            "strategy_options": {"lookback": lookback},
            "holding_bars": holding, "atr_stop_multiple": atr, "reward_risk": reward,
        }
    for lookback, fast, slow, slope_bars, holding, atr, reward in itertools.product(
        (12, 24, 48), (8, 13), (34, 55), (4, 8),
        (6, 12), (1.0, 1.5), (1.5, 2.0, 2.5),
    ):
        if fast >= slow:
            continue
        yield {
            "strategy_family": "ema_trend_breakout",
            "strategy_options": {
                "lookback": lookback, "fast_period": fast,
                "slow_period": slow, "slope_bars": slope_bars,
            },
            "holding_bars": holding, "atr_stop_multiple": atr,
            "reward_risk": reward,
        }
    for rsi_period, threshold, deviation, holding, atr, reward in itertools.product(
        (9, 14), (25, 30, 35), (1.5, 2.0), (3, 6), (1.0, 1.5), (1.0, 1.5)
    ):
        yield {
            "strategy_family": "bollinger_reversion",
            "strategy_options": {
                "rsi_period": rsi_period, "rsi_threshold": threshold,
                "band_period": 20, "band_deviation": deviation,
            },
            "holding_bars": holding, "atr_stop_multiple": atr, "reward_risk": reward,
        }
    for mode, session_clock, maximum_range_ratio, london_start, london_end, fast, slow, buffer_bps, holding, atr, reward in itertools.product(
        ("breakout", "false_breakout_fade"),
        ("utc", "europe_london"), (1.0, 1.5, 2.0),
        (7, 8), (11, 12), (8, 13, 21), (34, 55), (0.0, 1.0, 2.0),
        (4, 8, 12), (1.0, 1.5), (1.5, 2.0, 2.5),
    ):
        if london_end <= london_start or fast >= slow:
            continue
        if mode == "false_breakout_fade" and (fast, slow) != (8, 34):
            continue
        if session_clock == "europe_london" and (london_start, london_end) != (8, 12):
            continue
        yield {
            "strategy_family": "london_session_breakout",
            "strategy_options": {
                "fast_period": fast, "slow_period": slow,
                "asia_start_utc": 0, "asia_end_utc": 7,
                "london_start_utc": london_start, "london_end_utc": london_end,
                "breakout_buffer_bps": buffer_bps, "mode": mode,
                "session_clock": session_clock, "minimum_asia_range_ratio": 0.4,
                "maximum_asia_range_ratio": maximum_range_ratio,
            },
            "holding_bars": holding, "atr_stop_multiple": atr,
            "reward_risk": reward,
        }


def _slice_payload(payload: dict[str, Any], start: int, end: int):
    return {
        "opens": payload["opens"][start:end],
        "highs": payload["highs"][start:end],
        "lows": payload["lows"][start:end],
        "closes": payload["prices"][start:end],
        "timestamps": payload["labels"][start:end],
    }


def _historical_spread_bps(payload: dict[str, Any]) -> float:
    configured = float(payload.get("market", {}).get("research_spread_bps") or 0)
    if configured > 0:
        return round(max(1.0, configured), 4)
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


def _stress_test(segment, parameters, spread_bps):
    """Require the candidate to survive materially worse trading friction."""
    stressed = run_ohlc_backtest(
        segment["opens"], segment["highs"], segment["lows"], segment["closes"],
        timestamps=segment["timestamps"], **parameters, risk_percent=0.1,
        spread_bps=max(2.0, spread_bps * 2), commission_bps_per_side=0.4,
        slippage_bps_per_side=0.6, max_drawdown_pct=50,
        max_daily_loss_pct=1.0, max_trades_per_day=3,
        max_consecutive_losses=2, loss_cooldown_bars=3,
    )
    return _compact(stressed)


def _chronological_robustness(payload, parameters, spread_bps, folds=5):
    """Evaluate one frozen parameter set across separate market periods."""
    length = len(payload["prices"])
    edges = [round(length * index / folds) for index in range(folds + 1)]
    results = []
    for index in range(folds):
        segment = _slice_payload(payload, edges[index], edges[index + 1])
        result = _run(segment, parameters, spread_bps)
        compact = _compact(result)
        compact["fold"] = index + 1
        compact["start"] = segment["timestamps"][0]
        compact["end"] = segment["timestamps"][-1]
        results.append(compact)
    eligible = [item for item in results if int(item.get("trade_count") or 0) >= 8]
    profitable = [
        item for item in eligible
        if float(item.get("total_return_pct") or 0) > 0
        and float(item.get("profit_factor") or 0) >= 1.0
    ]
    return {
        "folds": results,
        "eligible_folds": len(eligible),
        "profitable_folds": len(profitable),
        "passed": len(eligible) == folds and len(profitable) >= math.ceil(folds * 0.60),
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
    for parameters in _parameter_grid():
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
    stressed_test = _stress_test(segments["test"], best_parameters, spread_bps)
    monte_carlo = monte_carlo_trade_risk(test.get("trades") or [], simulations=2_000)
    chronological = _chronological_robustness(payload, best_parameters, spread_bps)
    data_quality = payload.get("quality") or {}
    base_pass = _passes(best_train, validation, test)
    stress_pass = (
        int(stressed_test.get("trade_count") or 0) >= 8
        and float(stressed_test.get("total_return_pct") or 0) > 0
        and float(stressed_test.get("profit_factor") or 0) >= 1.05
    )
    monte_carlo_pass = (
        bool(monte_carlo.get("available"))
        and float(monte_carlo.get("probability_profitable_pct") or 0) >= 70
        and float((monte_carlo.get("ending_return_pct") or {}).get("p05") or -100) > -5
    )
    chronological_pass = bool(chronological.get("passed"))
    return {
        "qualified": bool(
            data_quality.get("historical_integrity", data_quality.get("safe_for_signal"))
        ) and base_pass and stress_pass and monte_carlo_pass and chronological_pass,
        "candles": length,
        "spread_bps_used": spread_bps,
        "data_quality": data_quality,
        "parameters": best_parameters,
        "train": _compact(best_train),
        "validation": _compact(validation),
        "test": _compact(test),
        "stress_test": stressed_test,
        "monte_carlo": monte_carlo,
        "chronological_robustness": chronological,
        "qualification_checks": {
            "base_segments": base_pass,
            "double_cost_stress": stress_pass,
            "monte_carlo": monte_carlo_pass,
            "chronological_robustness": chronological_pass,
        },
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
    parser.add_argument("--output", default="", help="Optional JSON report path")
    args = parser.parse_args()
    rendered = json.dumps(run_research(args.symbols, args.intervals, args.candles), ensure_ascii=False, indent=2)
    if args.output:
        output = Path(args.output).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
