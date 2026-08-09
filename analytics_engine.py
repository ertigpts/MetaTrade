"""Deterministic analytics used by TradeAI.

The language model is intentionally not involved here.  Everything in this
module can be reproduced from the same market data and parameters.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from technical_indicators import calculate_macd, calculate_rsi


def calculate_atr(highs, lows, closes, period=14):
    if period <= 0:
        raise ValueError("ATR period must be a positive integer.")
    high = pd.Series(np.asarray(highs, dtype=np.float64))
    low = pd.Series(np.asarray(lows, dtype=np.float64))
    close = pd.Series(np.asarray(closes, dtype=np.float64))
    if not (len(high) == len(low) == len(close)):
        raise ValueError("High, low and close arrays must have equal length.")
    if len(close) == 0:
        raise ValueError("Price data is required.")
    previous_close = close.shift(1)
    true_range = pd.concat(
        [(high - low).abs(), (high - previous_close).abs(), (low - previous_close).abs()],
        axis=1,
    ).max(axis=1)
    return true_range.ewm(alpha=1 / period, min_periods=period, adjust=False).mean().rename("ATR")


def close_volatility(closes, period=14):
    """Fallback volatility estimate when the provider supplies closes only."""
    close = pd.Series(np.asarray(closes, dtype=np.float64))
    return close.diff().abs().ewm(alpha=1 / period, min_periods=period, adjust=False).mean().rename("ATR proxy")


def multi_timeframe_alignment(closes):
    """Estimate short/medium/higher trend without pretending sampled closes are OHLC candles."""
    arr = np.asarray(closes, dtype=np.float64)
    if len(arr) < 30:
        return {"short": "neutral", "medium": "neutral", "higher": "neutral", "alignment": "mixed"}

    def slope(window):
        values = arr[-min(window, len(arr)) :]
        x = np.arange(len(values), dtype=np.float64)
        raw = float(np.polyfit(x, values, 1)[0])
        noise = float(np.mean(np.abs(np.diff(values)))) if len(values) > 1 else 0.0
        threshold = max(noise * 0.08, abs(float(values[-1])) * 1e-7)
        if raw > threshold:
            return "bullish"
        if raw < -threshold:
            return "bearish"
        return "neutral"

    result = {"short": slope(12), "medium": slope(30), "higher": slope(60)}
    directional = [value for value in result.values() if value != "neutral"]
    result["alignment"] = directional[0] if directional and len(set(directional)) == 1 else "mixed"
    return result


def _signal_at(prices, index, rsi_period, macd_short, macd_long, macd_signal):
    sample = prices[: index + 1]
    rsi = calculate_rsi(sample.tolist(), rsi_period).iloc[-1]
    macd = calculate_macd(sample.tolist(), macd_short, macd_long, macd_signal).iloc[-1]
    if not np.isfinite(rsi) or not np.isfinite(macd["MACD"]) or not np.isfinite(macd["Signal Line"]):
        return 0
    gap = float(macd["MACD"] - macd["Signal Line"])
    if gap > 0 and 50 <= rsi < 72:
        return 1
    if gap < 0 and 28 < rsi <= 50:
        return -1
    return 0


def _signal_series(prices, rsi_period, macd_short, macd_long, macd_signal):
    """Precompute causal signals once; pandas indicators only use current/past bars."""
    values = np.asarray(prices, dtype=np.float64)
    rsi = calculate_rsi(values.tolist(), rsi_period).to_numpy(dtype=np.float64)
    macd = calculate_macd(
        values.tolist(), macd_short, macd_long, macd_signal
    )
    macd_line = macd["MACD"].to_numpy(dtype=np.float64)
    signal_line = macd["Signal Line"].to_numpy(dtype=np.float64)
    valid = np.isfinite(rsi) & np.isfinite(macd_line) & np.isfinite(signal_line)
    gap = macd_line - signal_line
    signals = np.zeros(len(values), dtype=np.int8)
    signals[valid & (gap > 0) & (rsi >= 50) & (rsi < 72)] = 1
    signals[valid & (gap < 0) & (rsi > 28) & (rsi <= 50)] = -1
    return signals


@dataclass
class Trade:
    direction: str
    entry_index: int
    exit_index: int
    entry: float
    exit: float
    pnl_pct: float
    outcome: str


def _validate_ohlc(opens, highs, lows, closes):
    arrays = [np.asarray(values, dtype=np.float64) for values in (opens, highs, lows, closes)]
    if len({len(values) for values in arrays}) != 1 or not len(arrays[0]):
        raise ValueError("Open, high, low and close arrays must have equal non-zero length.")
    if any(np.isnan(values).any() or np.isinf(values).any() for values in arrays):
        raise ValueError("OHLC values cannot contain NaN or infinity.")
    open_values, high_values, low_values, close_values = arrays
    if (
        np.any(np.minimum.reduce([open_values, high_values, low_values, close_values]) <= 0)
        or np.any(high_values < np.maximum(open_values, close_values))
        or np.any(low_values > np.minimum(open_values, close_values))
    ):
        raise ValueError("OHLC candle structure is invalid.")
    return arrays


def run_ohlc_backtest(
    opens,
    highs,
    lows,
    closes,
    *,
    timestamps=None,
    rsi_period=14,
    macd_short=12,
    macd_long=26,
    macd_signal=9,
    holding_bars=6,
    atr_period=14,
    atr_stop_multiple=1.5,
    reward_risk=2.0,
    risk_percent=0.5,
    spread_bps=1.5,
    commission_bps_per_side=0.0,
    slippage_bps_per_side=0.2,
    max_drawdown_pct=10.0,
    max_daily_loss_pct=3.0,
    max_trades_per_day=5,
    max_consecutive_losses=3,
    loss_cooldown_bars=3,
):
    """Conservative next-bar OHLC simulation without look-ahead.

    The signal is calculated at a completed bar. Entry happens at the next
    bar's open. If stop and target are both touched inside one bar, stop is
    assumed to happen first because tick ordering is unknown.
    """
    open_values, high_values, low_values, close_values = _validate_ohlc(opens, highs, lows, closes)
    length = len(close_values)
    minimum = max(macd_long + macd_signal + 5, atr_period + 5, 45)
    if length < minimum + holding_bars + 1:
        raise ValueError(f"At least {minimum + holding_bars + 1} OHLC candles are required.")
    if not 1 <= holding_bars <= 100:
        raise ValueError("Holding bars must be between 1 and 100.")
    if not 0.1 <= risk_percent <= 2:
        raise ValueError("Risk percent must be between 0.1 and 2.")
    if not 0.5 <= atr_stop_multiple <= 5 or not 1 <= reward_risk <= 5:
        raise ValueError("ATR multiple or reward/risk is outside the safe range.")
    if min(spread_bps, commission_bps_per_side, slippage_bps_per_side) < 0:
        raise ValueError("Trading costs cannot be negative.")
    if not 1 <= max_drawdown_pct <= 50 or not 0.5 <= max_daily_loss_pct <= 20:
        raise ValueError("Loss limits are outside the supported range.")
    if not 1 <= max_trades_per_day <= 100 or not 1 <= max_consecutive_losses <= 20:
        raise ValueError("Trade-count controls are outside the supported range.")
    if not 1 <= int(loss_cooldown_bars) <= 100:
        raise ValueError("Loss cooldown bars must be between 1 and 100.")

    if timestamps is not None and len(timestamps) != length:
        raise ValueError("Timestamps must match the OHLC length.")
    timestamp_values = list(timestamps) if timestamps is not None else [None] * length
    atr_values = calculate_atr(high_values, low_values, close_values, atr_period).to_numpy()
    signals = _signal_series(close_values, rsi_period, macd_short, macd_long, macd_signal)

    equity = 1.0
    peak_equity = equity
    equity_curve = [{"index": 0, "equity": equity}]
    trades = []
    daily_start = {}
    daily_count = {}
    consecutive_losses = 0
    cooldown_until_index = -1
    cooldown_count = 0
    halted_reason = None
    friction = (spread_bps + 2 * commission_bps_per_side + 2 * slippage_bps_per_side) / 10_000
    risk_fraction = risk_percent / 100
    index = minimum - 1

    def day_key(raw, fallback):
        if raw is None:
            return f"bar-{fallback}"
        return str(raw)[:10]

    while index + 1 < length:
        current_drawdown = (peak_equity - equity) / peak_equity * 100 if peak_equity else 0
        if current_drawdown >= max_drawdown_pct:
            halted_reason = "maximum_drawdown"
            break
        if consecutive_losses >= max_consecutive_losses:
            if index < cooldown_until_index:
                index += 1
                continue
            consecutive_losses = 0

        entry_index = index + 1
        day = day_key(timestamp_values[entry_index], entry_index)
        daily_start.setdefault(day, equity)
        daily_count.setdefault(day, 0)
        day_loss = (daily_start[day] - equity) / daily_start[day] * 100 if daily_start[day] else 0
        if day_loss >= max_daily_loss_pct or daily_count[day] >= max_trades_per_day:
            index += 1
            continue

        direction = int(signals[index])
        atr = float(atr_values[index]) if np.isfinite(atr_values[index]) else 0.0
        if direction == 0 or atr <= 0:
            index += 1
            continue

        entry = float(open_values[entry_index])
        stop_distance = atr * atr_stop_multiple
        stop = entry - stop_distance if direction > 0 else entry + stop_distance
        target = entry + stop_distance * reward_risk if direction > 0 else entry - stop_distance * reward_risk
        planned_exit = min(entry_index + holding_bars - 1, length - 1)
        exit_index = planned_exit
        exit_price = float(close_values[planned_exit])
        exit_reason = "time"

        for cursor in range(entry_index, planned_exit + 1):
            hit_stop = low_values[cursor] <= stop if direction > 0 else high_values[cursor] >= stop
            hit_target = high_values[cursor] >= target if direction > 0 else low_values[cursor] <= target
            if hit_stop:
                exit_index = cursor
                exit_price = stop
                exit_reason = "stop" if not hit_target else "stop_first_conservative"
                break
            if hit_target:
                exit_index = cursor
                exit_price = target
                exit_reason = "target"
                break

        stop_fraction = stop_distance / entry
        exposure = min(risk_fraction / stop_fraction, 10.0) if stop_fraction > 0 else 0.0
        gross_move = direction * ((exit_price - entry) / entry)
        net_return = exposure * (gross_move - friction)
        previous_equity = equity
        equity = max(0.0, equity * (1 + net_return))
        peak_equity = max(peak_equity, equity)
        pnl_pct = net_return * 100
        outcome = "win" if pnl_pct > 0 else ("loss" if pnl_pct < 0 else "flat")
        consecutive_losses = consecutive_losses + 1 if outcome == "loss" else 0
        if consecutive_losses >= max_consecutive_losses:
            cooldown_until_index = exit_index + int(loss_cooldown_bars)
            cooldown_count += 1
        daily_count[day] += 1
        trades.append({
            "direction": "buy" if direction > 0 else "sell",
            "signal_index": index,
            "entry_index": entry_index,
            "exit_index": exit_index,
            "entry_time": timestamp_values[entry_index],
            "exit_time": timestamp_values[exit_index],
            "entry": round(entry, 8),
            "stop_loss": round(stop, 8),
            "take_profit": round(target, 8),
            "exit": round(exit_price, 8),
            "exit_reason": exit_reason,
            "exposure": round(exposure, 4),
            "pnl_pct": round(pnl_pct, 4),
            "equity_before": round(previous_equity, 6),
            "equity_after": round(equity, 6),
            "outcome": outcome,
        })
        equity_curve.append({"index": exit_index, "equity": round(equity, 6)})
        index = exit_index + 1

    if not trades:
        return {
            "trade_count": 0,
            "win_rate": None,
            "total_return_pct": 0.0,
            "net_profit_pct": 0.0,
            "profit_factor": None,
            "expectancy_pct": None,
            "max_drawdown_pct": 0.0,
            "sharpe": None,
            "average_win_pct": None,
            "average_loss_pct": None,
            "buy_hold_pct": round((close_values[-1] / close_values[minimum] - 1) * 100, 2),
            "equity_curve": equity_curve,
            "trades": [],
            "halted_reason": halted_reason,
            "cooldown_count": cooldown_count,
            "warning": "No historical setup matched the selected rule.",
            "engine": "ohlc_next_bar_conservative",
        }

    returns = np.asarray([trade["pnl_pct"] / 100 for trade in trades], dtype=np.float64)
    wins = returns[returns > 0]
    losses = returns[returns < 0]
    curve = np.asarray([point["equity"] for point in equity_curve], dtype=np.float64)
    running_max = np.maximum.accumulate(curve)
    drawdowns = (curve - running_max) / running_max
    std = float(np.std(returns, ddof=1)) if len(returns) > 1 else 0.0
    sharpe = float(np.mean(returns) / std * math.sqrt(len(returns))) if std > 0 else None
    loss_sum = abs(float(np.sum(losses)))
    profit_factor = float(np.sum(wins)) / loss_sum if loss_sum > 0 else None
    return {
        "trade_count": len(trades),
        "win_rate": round(float(np.mean(returns > 0) * 100), 2),
        "total_return_pct": round((equity - 1) * 100, 2),
        "net_profit_pct": round((equity - 1) * 100, 2),
        "profit_factor": round(profit_factor, 2) if profit_factor is not None else None,
        "expectancy_pct": round(float(np.mean(returns) * 100), 4),
        "max_drawdown_pct": round(abs(float(np.min(drawdowns))) * 100, 2),
        "sharpe": round(sharpe, 2) if sharpe is not None else None,
        "average_win_pct": round(float(np.mean(wins) * 100), 4) if len(wins) else None,
        "average_loss_pct": round(float(np.mean(losses) * 100), 4) if len(losses) else None,
        "buy_hold_pct": round((close_values[-1] / close_values[minimum] - 1) * 100, 2),
        "equity_curve": equity_curve,
        "trades": trades,
        "halted_reason": halted_reason,
        "cooldown_count": cooldown_count,
        "costs": {
            "spread_bps": spread_bps,
            "commission_bps_per_side": commission_bps_per_side,
            "slippage_bps_per_side": slippage_bps_per_side,
        },
        "warning": "Historical performance is not a promise of future results.",
        "engine": "ohlc_next_bar_conservative",
    }


def run_backtest(
    closes,
    *,
    rsi_period=14,
    macd_short=12,
    macd_long=26,
    macd_signal=9,
    holding_bars=6,
    fee_bps=2.0,
):
    """Walk-forward backtest of the current RSI/MACD rule.

    Signals are calculated using data available at the entry bar only.  A
    fixed holding period keeps the result auditable and avoids hidden
    optimisation.  Fees are charged on entry and exit.
    """
    prices = np.asarray(closes, dtype=np.float64)
    minimum = max(macd_long + macd_signal + 5, 45)
    if len(prices) < minimum + holding_bars:
        raise ValueError(f"At least {minimum + holding_bars} prices are required for backtesting.")
    if holding_bars < 1 or holding_bars > 100:
        raise ValueError("Holding bars must be between 1 and 100.")
    if fee_bps < 0 or fee_bps > 100:
        raise ValueError("Fee must be between 0 and 100 basis points.")

    trades = []
    equity = 1.0
    equity_curve = [equity]
    fee_fraction = fee_bps / 10_000
    signals = _signal_series(prices, rsi_period, macd_short, macd_long, macd_signal)
    index = minimum - 1
    while index + holding_bars < len(prices):
        direction = int(signals[index])
        if direction == 0:
            index += 1
            continue
        exit_index = index + holding_bars
        entry = float(prices[index])
        exit_price = float(prices[exit_index])
        gross = direction * ((exit_price - entry) / entry)
        net = gross - (2 * fee_fraction)
        equity *= 1 + net
        equity_curve.append(equity)
        trades.append(
            Trade(
                direction="buy" if direction > 0 else "sell",
                entry_index=index,
                exit_index=exit_index,
                entry=entry,
                exit=exit_price,
                pnl_pct=net * 100,
                outcome="win" if net > 0 else ("loss" if net < 0 else "flat"),
            )
        )
        index = exit_index + 1

    if not trades:
        return {
            "trade_count": 0,
            "win_rate": None,
            "total_return_pct": 0.0,
            "profit_factor": None,
            "expectancy_pct": None,
            "max_drawdown_pct": 0.0,
            "sharpe": None,
            "trades": [],
            "warning": "No historical setup matched the selected rule.",
        }

    returns = np.asarray([trade.pnl_pct / 100 for trade in trades], dtype=np.float64)
    wins = returns[returns > 0]
    losses = returns[returns < 0]
    curve = np.asarray(equity_curve, dtype=np.float64)
    running_max = np.maximum.accumulate(curve)
    drawdown = (curve - running_max) / running_max
    std = float(np.std(returns, ddof=1)) if len(returns) > 1 else 0.0
    sharpe = float(np.mean(returns) / std * math.sqrt(len(returns))) if std > 0 else None
    loss_sum = abs(float(np.sum(losses)))
    profit_factor = float(np.sum(wins)) / loss_sum if loss_sum > 0 else None

    return {
        "trade_count": len(trades),
        "win_rate": round(float(np.mean(returns > 0) * 100), 2),
        "total_return_pct": round((equity - 1) * 100, 2),
        "profit_factor": round(profit_factor, 2) if profit_factor is not None else None,
        "expectancy_pct": round(float(np.mean(returns) * 100), 4),
        "max_drawdown_pct": round(abs(float(np.min(drawdown))) * 100, 2),
        "sharpe": round(sharpe, 2) if sharpe is not None else None,
        "trades": [trade.__dict__ for trade in trades[-30:]],
        "warning": "Historical performance is not a promise of future results.",
    }
