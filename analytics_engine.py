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


def _family_signal_series(
    prices, strategy_family, strategy_options, *, timestamps=None, highs=None, lows=None
):
    """Generate causal signals for independently testable strategy families."""
    values = np.asarray(prices, dtype=np.float64)
    options = dict(strategy_options or {})
    family = str(strategy_family or "rsi_macd").lower()
    if family == "rsi_macd":
        return _signal_series(
            values,
            int(options.get("rsi_period", 14)),
            int(options.get("macd_short", 12)),
            int(options.get("macd_long", 26)),
            int(options.get("macd_signal", 9)),
        )

    close = pd.Series(values)
    signals = np.zeros(len(values), dtype=np.int8)
    if family == "ema_pullback":
        fast_period = int(options.get("fast_period", 12))
        slow_period = int(options.get("slow_period", 50))
        if not 2 <= fast_period < slow_period <= 300:
            raise ValueError("EMA periods must satisfy 2 <= fast < slow <= 300.")
        fast = close.ewm(span=fast_period, adjust=False, min_periods=fast_period).mean()
        slow = close.ewm(span=slow_period, adjust=False, min_periods=slow_period).mean()
        buy = (fast > slow) & (close > fast) & (close.shift(1) <= fast.shift(1))
        sell = (fast < slow) & (close < fast) & (close.shift(1) >= fast.shift(1))
        signals[buy.fillna(False).to_numpy()] = 1
        signals[sell.fillna(False).to_numpy()] = -1
        return signals

    if family == "regime_ema_pullback":
        fast_period = int(options.get("fast_period", 13))
        slow_period = int(options.get("slow_period", 55))
        efficiency_window = int(options.get("efficiency_window", 20))
        minimum_efficiency = float(options.get("minimum_efficiency", 0.25))
        volatility_window = int(options.get("volatility_window", 20))
        volatility_baseline = int(options.get("volatility_baseline", 100))
        maximum_volatility_ratio = float(options.get("maximum_volatility_ratio", 1.75))
        if not 2 <= fast_period < slow_period <= 300:
            raise ValueError("Regime EMA periods must satisfy 2 <= fast < slow <= 300.")
        if not 5 <= efficiency_window <= 100 or not 0.05 <= minimum_efficiency <= 0.9:
            raise ValueError("Regime efficiency settings are outside the safe range.")
        if not 10 <= volatility_window < volatility_baseline <= 500:
            raise ValueError("Regime volatility windows are outside the safe range.")
        if not 1.0 <= maximum_volatility_ratio <= 4.0:
            raise ValueError("Regime volatility ratio is outside the safe range.")
        fast = close.ewm(span=fast_period, adjust=False, min_periods=fast_period).mean()
        slow = close.ewm(span=slow_period, adjust=False, min_periods=slow_period).mean()
        path = close.diff().abs().rolling(efficiency_window, min_periods=efficiency_window).sum()
        displacement = (close - close.shift(efficiency_window)).abs()
        efficiency = displacement / path.replace(0, np.nan)
        returns = close.pct_change()
        current_volatility = returns.rolling(volatility_window, min_periods=volatility_window).std()
        baseline_volatility = current_volatility.rolling(
            volatility_baseline, min_periods=volatility_baseline
        ).median()
        volatility_ok = current_volatility <= baseline_volatility * maximum_volatility_ratio
        trend_ok = efficiency >= minimum_efficiency
        buy = (
            (fast > slow) & (slow > slow.shift(4)) & trend_ok & volatility_ok
            & (close > fast) & (close.shift(1) <= fast.shift(1))
        )
        sell = (
            (fast < slow) & (slow < slow.shift(4)) & trend_ok & volatility_ok
            & (close < fast) & (close.shift(1) >= fast.shift(1))
        )
        signals[buy.fillna(False).to_numpy()] = 1
        signals[sell.fillna(False).to_numpy()] = -1
        return signals

    if family == "donchian_breakout":
        lookback = int(options.get("lookback", 40))
        if not 5 <= lookback <= 300:
            raise ValueError("Donchian lookback must be between 5 and 300.")
        previous_high = close.shift(1).rolling(lookback, min_periods=lookback).max()
        previous_low = close.shift(1).rolling(lookback, min_periods=lookback).min()
        signals[(close > previous_high).fillna(False).to_numpy()] = 1
        signals[(close < previous_low).fillna(False).to_numpy()] = -1
        return signals

    if family == "ema_trend_breakout":
        lookback = int(options.get("lookback", 24))
        fast_period = int(options.get("fast_period", 13))
        slow_period = int(options.get("slow_period", 55))
        slope_bars = int(options.get("slope_bars", 6))
        if not 8 <= lookback <= 200:
            raise ValueError("Trend breakout lookback must be between 8 and 200.")
        if not 2 <= fast_period < slow_period <= 300:
            raise ValueError("Trend breakout EMA periods must satisfy 2 <= fast < slow <= 300.")
        if not 2 <= slope_bars <= 50:
            raise ValueError("Trend breakout slope bars must be between 2 and 50.")
        fast = close.ewm(span=fast_period, adjust=False, min_periods=fast_period).mean()
        slow = close.ewm(span=slow_period, adjust=False, min_periods=slow_period).mean()
        previous_high = close.shift(1).rolling(lookback, min_periods=lookback).max()
        previous_low = close.shift(1).rolling(lookback, min_periods=lookback).min()
        slow_slope = slow - slow.shift(slope_bars)
        buy = (close > previous_high) & (fast > slow) & (slow_slope > 0)
        sell = (close < previous_low) & (fast < slow) & (slow_slope < 0)
        # One causal entry at the start of a breakout burst, rather than a new
        # correlated order on every consecutive extreme.
        buy = buy & ~buy.shift(1, fill_value=False)
        sell = sell & ~sell.shift(1, fill_value=False)
        signals[buy.fillna(False).to_numpy()] = 1
        signals[sell.fillna(False).to_numpy()] = -1
        return signals

    if family == "bollinger_reversion":
        period = int(options.get("band_period", 20))
        deviation = float(options.get("band_deviation", 2.0))
        rsi_period = int(options.get("rsi_period", 14))
        threshold = float(options.get("rsi_threshold", 30))
        if not 10 <= period <= 200 or not 1.0 <= deviation <= 4.0 or not 15 <= threshold <= 40:
            raise ValueError("Bollinger reversion parameters are outside the safe range.")
        mean = close.rolling(period, min_periods=period).mean()
        std = close.rolling(period, min_periods=period).std(ddof=0)
        rsi = calculate_rsi(values.tolist(), rsi_period)
        lower = mean - deviation * std
        upper = mean + deviation * std
        signals[((close < lower) & (rsi < threshold)).fillna(False).to_numpy()] = 1
        signals[((close > upper) & (rsi > 100 - threshold)).fillna(False).to_numpy()] = -1
        return signals

    if family == "london_session_breakout":
        if timestamps is None or highs is None or lows is None:
            return signals
        fast_period = int(options.get("fast_period", 13))
        slow_period = int(options.get("slow_period", 55))
        asia_start = int(options.get("asia_start_utc", 0))
        asia_end = int(options.get("asia_end_utc", 7))
        london_start = int(options.get("london_start_utc", 7))
        london_end = int(options.get("london_end_utc", 11))
        buffer_bps = float(options.get("breakout_buffer_bps", 1.0))
        mode = str(options.get("mode", "breakout")).lower()
        session_clock = str(options.get("session_clock", "utc")).lower()
        range_clock = str(options.get("range_clock", "utc")).lower()
        minimum_range_ratio = float(options.get("minimum_asia_range_ratio", 0.4))
        maximum_range_ratio = float(options.get("maximum_asia_range_ratio", 1.5))
        if not 2 <= fast_period < slow_period <= 300:
            raise ValueError("London breakout EMA periods must satisfy 2 <= fast < slow <= 300.")
        if not 0 <= asia_start < asia_end <= 12:
            raise ValueError("Asia-session hours are outside the safe range.")
        if not asia_end <= london_start < london_end <= 18:
            raise ValueError("London-session hours are outside the safe range.")
        if not 0 <= buffer_bps <= 20:
            raise ValueError("London breakout buffer is outside the safe range.")
        if mode not in {"breakout", "false_breakout_fade"}:
            raise ValueError("Unsupported London-session strategy mode.")
        if session_clock not in {"utc", "europe_london"}:
            raise ValueError("Unsupported London-session clock.")
        if range_clock not in {"utc", "europe_london"}:
            raise ValueError("Unsupported range-session clock.")
        if not 0.1 <= minimum_range_ratio < maximum_range_ratio <= 5:
            raise ValueError("Asia-range ratios are outside the safe range.")

        times = pd.to_datetime(list(timestamps), utc=True, errors="coerce")
        high_series = pd.Series(np.asarray(highs, dtype=np.float64))
        low_series = pd.Series(np.asarray(lows, dtype=np.float64))
        hours = pd.Series(times.hour)
        london_times = times.tz_convert("Europe/London")
        london_hours = pd.Series(london_times.hour) if session_clock == "europe_london" else hours
        range_hours = pd.Series(london_times.hour) if range_clock == "europe_london" else hours
        dates = pd.Series(
            london_times.date if range_clock == "europe_london" else times.date
        )
        asia_mask = (range_hours >= asia_start) & (range_hours < asia_end)
        london_mask = (london_hours >= london_start) & (london_hours < london_end)
        asia_high_by_day = high_series.where(asia_mask).groupby(dates).transform("max")
        asia_low_by_day = low_series.where(asia_mask).groupby(dates).transform("min")
        asia_bars_by_day = asia_mask.astype(int).groupby(dates).transform("sum")
        minimum_asia_bars = max(2, int((asia_end - asia_start) * 2))
        asia_range = asia_high_by_day - asia_low_by_day
        daily_ranges = pd.DataFrame({"date": dates, "range": asia_range}).drop_duplicates("date")
        daily_ranges["baseline"] = daily_ranges["range"].shift(1).rolling(20, min_periods=10).median()
        baseline_by_date = daily_ranges.set_index("date")["baseline"]
        range_baseline = dates.map(baseline_by_date)
        range_ratio = asia_range / range_baseline.replace(0, np.nan)
        range_ready = (
            (asia_bars_by_day >= minimum_asia_bars)
            & (range_ratio >= minimum_range_ratio)
            & (range_ratio <= maximum_range_ratio)
        )

        fast = close.ewm(span=fast_period, adjust=False, min_periods=fast_period).mean()
        slow = close.ewm(span=slow_period, adjust=False, min_periods=slow_period).mean()
        upper = asia_high_by_day * (1 + buffer_bps / 10_000)
        lower = asia_low_by_day * (1 - buffer_bps / 10_000)
        if mode == "false_breakout_fade":
            buy = london_mask & range_ready & (close.shift(1) < lower.shift(1)) & (close >= lower)
            sell = london_mask & range_ready & (close.shift(1) > upper.shift(1)) & (close <= upper)
        else:
            buy = london_mask & range_ready & (fast > slow) & (close > upper) & (close.shift(1) <= upper.shift(1))
            sell = london_mask & range_ready & (fast < slow) & (close < lower) & (close.shift(1) >= lower.shift(1))
        signals[buy.fillna(False).to_numpy()] = 1
        signals[sell.fillna(False).to_numpy()] = -1
        return signals

    raise ValueError(f"Unsupported strategy family: {family}")


def latest_strategy_signal(
    prices, strategy_family, strategy_options=None, *, timestamps=None, highs=None, lows=None
):
    """Return the latest deterministic family decision for the live closed bar."""
    values = np.asarray(prices, dtype=np.float64)
    if len(values) < 50:
        raise ValueError("At least 50 closed prices are required for a strategy signal.")
    signals = _family_signal_series(
        values, strategy_family, strategy_options or {},
        timestamps=timestamps, highs=highs, lows=lows,
    )
    value = int(signals[-1])
    direction = "BUY" if value > 0 else ("SELL" if value < 0 else "HOLD")
    family = str(strategy_family or "rsi_macd").lower()
    strength = 80 if direction != "HOLD" else 0
    return {
        "action_bias": f"{direction} bias" if direction != "HOLD" else "Wait",
        "signal_strength": strength,
        "signal_strength_label": "Deterministic strategy rule score",
        "strategy_family": family,
        "strategy_options": dict(strategy_options or {}),
        "signal_factors": [
            f"{family} closed-bar rule produced {direction}",
            "Entry is deferred to the next bar/open market quote",
        ] if direction != "HOLD" else [f"{family} has no closed-bar setup"],
    }


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
    strategy_family="rsi_macd",
    strategy_options=None,
):
    """Conservative next-bar OHLC simulation without look-ahead.

    The signal is calculated at a completed bar. Entry happens at the next
    bar's open. If stop and target are both touched inside one bar, stop is
    assumed to happen first because tick ordering is unknown.
    """
    open_values, high_values, low_values, close_values = _validate_ohlc(opens, highs, lows, closes)
    length = len(close_values)
    strategy_options = dict(strategy_options or {})
    if strategy_family == "rsi_macd":
        strategy_options = {
            "rsi_period": rsi_period, "macd_short": macd_short,
            "macd_long": macd_long, "macd_signal": macd_signal,
            **strategy_options,
        }
        strategy_warmup = int(strategy_options["macd_long"]) + int(strategy_options["macd_signal"]) + 5
    elif strategy_family == "ema_pullback":
        strategy_warmup = int(strategy_options.get("slow_period", 50)) + 5
    elif strategy_family == "regime_ema_pullback":
        strategy_warmup = max(
            int(strategy_options.get("slow_period", 55)),
            int(strategy_options.get("volatility_window", 20))
            + int(strategy_options.get("volatility_baseline", 100)),
        ) + 5
    elif strategy_family == "donchian_breakout":
        strategy_warmup = int(strategy_options.get("lookback", 40)) + 5
    elif strategy_family == "ema_trend_breakout":
        strategy_warmup = max(
            int(strategy_options.get("lookback", 24)),
            int(strategy_options.get("slow_period", 55)) + int(strategy_options.get("slope_bars", 6)),
        ) + 5
    elif strategy_family == "bollinger_reversion":
        strategy_warmup = max(int(strategy_options.get("band_period", 20)), int(strategy_options.get("rsi_period", 14))) + 5
    elif strategy_family == "london_session_breakout":
        strategy_warmup = int(strategy_options.get("slow_period", 55)) + 5
    else:
        raise ValueError(f"Unsupported strategy family: {strategy_family}")
    minimum = max(strategy_warmup, atr_period + 5, 45)
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
    signals = _family_signal_series(
        close_values, strategy_family, strategy_options,
        timestamps=timestamp_values, highs=high_values, lows=low_values,
    )

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
            "strategy_family": strategy_family,
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
        "strategy_family": strategy_family,
        "strategy_options": strategy_options,
    }


def monte_carlo_trade_risk(trades, *, simulations=2_000, seed=260809):
    """Bootstrap closed-trade returns to expose path and sequence risk.

    This is deliberately deterministic for auditability. It does not invent a
    forecast: it only reshuffles/resamples the observed net trade returns.
    """
    simulations = int(simulations)
    if not 100 <= simulations <= 50_000:
        raise ValueError("Monte Carlo simulations must be between 100 and 50000.")
    returns = np.asarray(
        [float(item.get("pnl_pct") or 0) / 100 for item in trades], dtype=np.float64
    )
    if len(returns) < 20:
        return {
            "available": False,
            "reason": "at_least_20_trades_required",
            "sample_trades": int(len(returns)),
            "simulations": simulations,
        }

    rng = np.random.default_rng(int(seed))
    sampled = rng.choice(returns, size=(simulations, len(returns)), replace=True)
    curves = np.cumprod(1 + sampled, axis=1)
    peaks = np.maximum.accumulate(curves, axis=1)
    drawdowns = np.min((curves - peaks) / peaks, axis=1)
    ending_returns = curves[:, -1] - 1
    return {
        "available": True,
        "sample_trades": int(len(returns)),
        "simulations": simulations,
        "probability_profitable_pct": round(float(np.mean(ending_returns > 0) * 100), 2),
        "probability_loss_pct": round(float(np.mean(ending_returns < 0) * 100), 2),
        "ending_return_pct": {
            "p05": round(float(np.percentile(ending_returns, 5) * 100), 2),
            "median": round(float(np.percentile(ending_returns, 50) * 100), 2),
            "p95": round(float(np.percentile(ending_returns, 95) * 100), 2),
        },
        "maximum_drawdown_pct": {
            "median": round(abs(float(np.percentile(drawdowns, 50))) * 100, 2),
            "p95_adverse": round(abs(float(np.percentile(drawdowns, 5))) * 100, 2),
        },
        "warning": "Bootstrap results describe uncertainty in the supplied trades, not future performance.",
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
