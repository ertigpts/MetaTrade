"""Deterministic market intelligence that can constrain, never loosen, risk."""

from __future__ import annotations

import math
from typing import Any

import numpy as np


def _finite(values):
    return np.asarray(values, dtype=np.float64)[np.isfinite(values)]


def classify_market_regime(highs, lows, closes) -> dict[str, Any]:
    """Classify trend/range/volatile from closed bars without future data."""
    close = _finite(closes)
    high = _finite(highs)
    low = _finite(lows)
    if min(len(close), len(high), len(low)) < 120:
        return {
            "regime": "uncertain", "confidence": 0, "risk_multiplier": 0.25,
            "reason": "insufficient_closed_bars", "deterministic": True,
        }
    close, high, low = close[-500:], high[-500:], low[-500:]
    returns = np.diff(close) / close[:-1]
    true_ranges = np.maximum.reduce((
        high[1:] - low[1:], np.abs(high[1:] - close[:-1]),
        np.abs(low[1:] - close[:-1]),
    ))
    recent_atr_pct = float(np.mean(true_ranges[-20:]) / close[-1])
    baseline_atr_pct = float(np.median([
        np.mean(true_ranges[index - 20:index]) / close[index]
        for index in range(120, len(close), 10)
        if close[index] > 0
    ]))
    volatility_ratio = recent_atr_pct / baseline_atr_pct if baseline_atr_pct > 0 else math.inf
    window = 20
    path = float(np.sum(np.abs(np.diff(close[-(window + 1):]))))
    efficiency = abs(float(close[-1] - close[-(window + 1)])) / path if path > 0 else 0.0
    fast = float(np.mean(close[-12:]))
    slow = float(np.mean(close[-48:]))
    trend_gap_bps = abs(fast - slow) / close[-1] * 10_000
    direction = "up" if fast > slow else ("down" if fast < slow else "flat")
    if volatility_ratio >= 1.8:
        regime, confidence, risk_multiplier = "volatile", min(95, int(65 + (volatility_ratio - 1.8) * 20)), 0.25
    elif efficiency >= 0.32 and trend_gap_bps >= 4:
        regime, confidence, risk_multiplier = "trend", min(92, int(55 + efficiency * 60)), 1.0
    elif efficiency <= 0.18 and trend_gap_bps <= 5:
        regime, confidence, risk_multiplier = "range", min(88, int(70 + (0.18 - efficiency) * 80)), 0.6
    else:
        regime, confidence, risk_multiplier = "uncertain", 50, 0.25
    return {
        "regime": regime, "direction": direction, "confidence": confidence,
        "risk_multiplier": risk_multiplier, "deterministic": True,
        "metrics": {
            "efficiency_ratio": round(efficiency, 4),
            "trend_gap_bps": round(trend_gap_bps, 2),
            "atr_pct": round(recent_atr_pct * 100, 4),
            "volatility_ratio": round(volatility_ratio, 3),
            "recent_return_std_pct": round(float(np.std(returns[-40:])) * 100, 4),
        },
    }


def detect_market_drift(closes) -> dict[str, Any]:
    """Compare recent closed-bar return distribution with an older baseline."""
    close = _finite(closes)
    if len(close) < 260:
        return {"level": "unknown", "block_new_entries": False, "risk_multiplier": 0.5,
                "reason": "insufficient_history"}
    returns = np.diff(close) / close[:-1]
    recent = returns[-80:]
    baseline = returns[-260:-80]
    baseline_std = float(np.std(baseline))
    recent_std = float(np.std(recent))
    volatility_ratio = recent_std / baseline_std if baseline_std > 0 else math.inf
    mean_shift_z = abs(float(np.mean(recent) - np.mean(baseline))) / (
        baseline_std / math.sqrt(len(recent))
    ) if baseline_std > 0 else math.inf
    if volatility_ratio >= 2.2 or volatility_ratio <= 0.4 or mean_shift_z >= 3.5:
        level, multiplier, block = "high", 0.25, True
    elif volatility_ratio >= 1.5 or volatility_ratio <= 0.6 or mean_shift_z >= 2.0:
        level, multiplier, block = "medium", 0.5, False
    else:
        level, multiplier, block = "low", 1.0, False
    return {
        "level": level, "block_new_entries": block, "risk_multiplier": multiplier,
        "metrics": {"volatility_ratio": round(volatility_ratio, 3),
                    "mean_shift_z": round(mean_shift_z, 3)},
        "reason": "closed_bar_distribution_shift" if level != "low" else "stable_distribution",
    }


def strategy_regime_risk(strategy_family: str, regime: str) -> float:
    """Return only a risk reduction; no regime can increase profile risk."""
    family = str(strategy_family or "").lower()
    regime = str(regime or "uncertain").lower()
    if regime in {"volatile", "uncertain"}:
        return 0.25
    if family == "bollinger_reversion":
        return 1.0 if regime == "range" else 0.5
    if family in {"ema_pullback", "regime_ema_pullback", "ema_trend_breakout", "donchian_breakout"}:
        return 1.0 if regime == "trend" else 0.5
    return 0.5


def route_timeframe(symbol: str, regime: dict[str, Any]) -> dict[str, Any]:
    """Recommend only registered research routes; HOLD remains a valid route."""
    normalized = str(symbol or "").upper().replace("/", "").replace(" ", "")
    state = regime.get("regime")
    if state in {"volatile", "uncertain"}:
        return {"recommended_interval": None, "decision": "HOLD", "reason": f"{state}_regime"}
    if normalized == "XAUUSD" and state == "trend":
        return {"recommended_interval": "4h", "decision": "ROUTE", "reason": "qualified_gold_trend_profile"}
    if normalized == "XAUUSD" and state == "range":
        return {"recommended_interval": "15min", "decision": "RESEARCH_ROUTE",
                "reason": "experimental_fast_observation_only"}
    return {"recommended_interval": "4h", "decision": "RESEARCH_ROUTE",
            "reason": "no_qualified_alternative"}


def performance_drift(chronological: dict[str, Any]) -> dict[str, Any]:
    folds = chronological.get("folds") or []
    eligible = [item for item in folds if int(item.get("trade_count") or 0) >= 8]
    if len(eligible) < 3:
        return {"level": "unknown", "reason": "insufficient_folds", "block_new_entries": False}
    negative = sum(float(item.get("total_return_pct") or 0) <= 0 or
                   float(item.get("profit_factor") or 0) < 1 for item in eligible)
    recent = eligible[-1]
    recent_bad = float(recent.get("total_return_pct") or 0) <= 0 or float(recent.get("profit_factor") or 0) < 1
    level = "high" if recent_bad and negative >= 2 else ("medium" if negative >= 2 else "low")
    return {"level": level, "negative_folds": negative, "eligible_folds": len(eligible),
            "block_new_entries": level == "high", "reason": "rolling_fold_instability"}
