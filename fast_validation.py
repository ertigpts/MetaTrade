"""Fast, order-free validation of the frozen demo strategy registry."""

from __future__ import annotations

from typing import Any

from analytics_engine import monte_carlo_trade_risk
from mt5_connector import MT5Connector
from market_intelligence import performance_drift
from strategy_profiles import PROFILES
from strategy_research import (
    _chronological_robustness, _compact, _historical_spread_bps,
    _passes, _run, _slice_payload, _stress_test,
)


VISIBLE_PROFILES = (
    ("XAUUSD", "4h"), ("XAUUSD", "15min"), ("EURUSD", "4h"),
    ("GBPUSD", "4h"), ("USDJPY", "4h"),
)


def _parameters(profile) -> dict[str, Any]:
    return {
        "strategy_family": profile.strategy_family,
        "strategy_options": profile.strategy_options,
        "rsi_period": profile.rsi_period, "macd_short": profile.macd_short,
        "macd_long": profile.macd_long, "macd_signal": profile.macd_signal,
        "holding_bars": profile.holding_bars,
        "atr_stop_multiple": profile.atr_stop_multiple,
        "reward_risk": profile.reward_risk,
    }


def run_fast_validation(candles: int = 5_000) -> dict[str, Any]:
    """Replay frozen profiles without optimizing on validation/test data."""
    candles = min(max(int(candles), 1_000), 10_000)
    report: dict[str, Any] = {
        "ok": True, "execution_mode": "research_only", "orders_sent": 0,
        "candles_requested": candles, "profiles": [],
    }
    connector = MT5Connector()
    with connector.session(require_demo=True) as (active, status):
        report["account_mode"] = status.get("account", {}).get("trade_mode")
        for key in VISIBLE_PROFILES:
            profile = PROFILES[key]
            try:
                payload = active.fetch_candles(
                    profile.symbol, profile.interval, candles, include_incomplete=False
                )
                length = len(payload["prices"])
                train_end, validation_end = int(length * 0.60), int(length * 0.80)
                params = _parameters(profile)
                spread_bps = _historical_spread_bps(payload)
                train = _run(_slice_payload(payload, 0, train_end), params, spread_bps)
                validation = _run(_slice_payload(payload, train_end, validation_end), params, spread_bps)
                test_segment = _slice_payload(payload, validation_end, length)
                test = _run(test_segment, params, spread_bps)
                stress = _stress_test(test_segment, params, spread_bps)
                monte_carlo = monte_carlo_trade_risk(test.get("trades") or [], simulations=2_000)
                chronological = _chronological_robustness(payload, params, spread_bps)
                checks = {
                    "historical_integrity": bool(payload.get("quality", {}).get("historical_integrity")),
                    "train_validation_test": _passes(train, validation, test),
                    "double_cost_stress": int(stress.get("trade_count") or 0) >= 8
                    and float(stress.get("total_return_pct") or 0) > 0
                    and float(stress.get("profit_factor") or 0) >= 1.05,
                    "monte_carlo": bool(monte_carlo.get("available"))
                    and float(monte_carlo.get("probability_profitable_pct") or 0) >= 70
                    and float((monte_carlo.get("ending_return_pct") or {}).get("p05") or -100) > -5,
                    "chronological_robustness": bool(chronological.get("passed")),
                }
                weights = {
                    "historical_integrity": 1.5, "train_validation_test": 3.0,
                    "double_cost_stress": 2.0, "monte_carlo": 1.5,
                    "chronological_robustness": 2.0,
                }
                score = sum(weights[name] for name, passed in checks.items() if passed)
                report["profiles"].append({
                    "symbol": payload["symbol"], "interval": profile.interval,
                    "strategy_family": profile.strategy_family, "parameters": params,
                    "research_qualified_registry": profile.research_qualified,
                    "forward_demo_enabled": profile.forward_demo_enabled,
                    "fresh_validation_qualified": all(checks.values()),
                    "acceptance_score": round(score, 1),
                    "acceptance_score_is_profit_probability": False,
                    "checks": checks, "quality": payload.get("quality"),
                    "train": _compact(train), "validation": _compact(validation),
                    "test": _compact(test), "stress_test": stress,
                    "monte_carlo": monte_carlo,
                    "chronological_robustness": chronological,
                    "performance_drift": performance_drift(chronological),
                })
            except Exception as exc:
                report["profiles"].append({
                    "symbol": profile.symbol, "interval": profile.interval,
                    "fresh_validation_qualified": False, "acceptance_score": 0.0,
                    "error": str(exc)[:300],
                })
    report["qualified_count"] = sum(
        bool(item.get("fresh_validation_qualified")) for item in report["profiles"]
    )
    return report
