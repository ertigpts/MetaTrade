"""Deterministic signal, AI confirmation and risk controls for MT5 demo trading."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_DOWN
from typing import Any


class TradingRuleError(ValueError):
    pass


@dataclass(frozen=True)
class SignalSettings:
    minimum_strength: int = 70
    maximum_spread_pips: float = 2.0
    maximum_spread_bps: float = 3.0
    risk_percent: float = 0.1
    maximum_volume: float = 0.1
    atr_stop_multiple: float = 1.5
    reward_risk: float = 2.0
    maximum_daily_loss_percent: float = 1.0
    maximum_open_positions: int = 1
    maximum_symbol_open_positions: int = 1
    maximum_symbol_daily_trades: int = 1
    maximum_consecutive_losses: int = 2
    loss_cooldown_hours: int = 12
    maximum_daily_trades: int = 3
    ai_minimum_confidence: int = 70
    require_ai_confirmation: bool = False

    def validated(self) -> "SignalSettings":
        if not 50 <= int(self.minimum_strength) <= 88:
            raise TradingRuleError("حداقل قدرت سیگنال باید بین ۵۰ و ۸۸ باشد.")
        if not 0.1 <= float(self.maximum_spread_pips) <= 10:
            raise TradingRuleError("حداکثر اسپرد باید بین ۰٫۱ و ۱۰ پیپ باشد.")
        if not 0.1 <= float(self.maximum_spread_bps) <= 20:
            raise TradingRuleError("حداکثر اسپرد باید بین ۰٫۱ و ۲۰ واحد پایه باشد.")
        if not 0.1 <= float(self.risk_percent) <= 2:
            raise TradingRuleError("ریسک هر معامله باید بین ۰٫۱ و ۲ درصد باشد.")
        if not 0.01 <= float(self.maximum_volume) <= 100:
            raise TradingRuleError("سقف حجم باید بین ۰٫۰۱ و ۱۰۰ لات باشد.")
        if not 0.5 <= float(self.atr_stop_multiple) <= 5:
            raise TradingRuleError("ضریب ATR حد ضرر باید بین ۰٫۵ و ۵ باشد.")
        if not 1 <= float(self.reward_risk) <= 5:
            raise TradingRuleError("نسبت سود به ریسک باید بین ۱ و ۵ باشد.")
        if not 0.25 <= float(self.maximum_daily_loss_percent) <= 5:
            raise TradingRuleError("حد زیان روزانه باید بین ۰٫۲۵ و ۵ درصد باشد.")
        if not 1 <= int(self.maximum_open_positions) <= 5:
            raise TradingRuleError("حداکثر پوزیشن باز باید بین ۱ و ۵ باشد.")
        if not 1 <= int(self.maximum_symbol_open_positions) <= 5:
            raise TradingRuleError("سقف پوزیشن باز هر نماد باید بین ۱ و ۵ باشد.")
        if not 1 <= int(self.maximum_symbol_daily_trades) <= 10:
            raise TradingRuleError("سقف معامله روزانه هر نماد باید بین ۱ و ۱۰ باشد.")
        if not 1 <= int(self.maximum_consecutive_losses) <= 10:
            raise TradingRuleError("حد زیان‌های متوالی باید بین ۱ و ۱۰ باشد.")
        if not 4 <= int(self.loss_cooldown_hours) <= 72:
            raise TradingRuleError("توقف بعد از زیان باید بین ۴ و ۷۲ ساعت باشد.")
        if not 1 <= int(self.maximum_daily_trades) <= 20:
            raise TradingRuleError("سقف معامله روزانه باید بین ۱ و ۲۰ باشد.")
        if not 50 <= int(self.ai_minimum_confidence) <= 95:
            raise TradingRuleError("حداقل اطمینان AI باید بین ۵۰ و ۹۵ باشد.")
        return self


def _signal_direction(action_bias: Any) -> str:
    value = str(action_bias or "").lower()
    if "buy" in value:
        return "BUY"
    if "sell" in value:
        return "SELL"
    return "HOLD"


def _signal_key(symbol: str, interval: str, candle_time: str, direction: str) -> str:
    raw = f"{symbol}|{interval}|{candle_time}|{direction}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:32]


def generate_signal(
    summary: dict[str, Any],
    market: dict[str, Any],
    quality: dict[str, Any],
    *,
    symbol: str,
    interval: str,
    candle_time: str,
    settings: SignalSettings,
    duplicate: bool = False,
    account_status: dict[str, Any] | None = None,
    portfolio: dict[str, Any] | None = None,
    timeframe_confirmation: dict[str, Any] | None = None,
    macro_gate: dict[str, Any] | None = None,
    ai_assessment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    settings.validated()
    candidate = _signal_direction(summary.get("action_bias"))
    strength = int(summary.get("signal_strength") or 0)
    spread = market.get("spread_pips")
    spread_bps = market.get("spread_bps")
    spread_ok = (
        float(spread_bps) <= settings.maximum_spread_bps
        if spread_bps is not None
        else spread is not None and float(spread) <= settings.maximum_spread_pips
    )
    account_status = account_status or {}
    account = account_status.get("account") or {}
    portfolio = portfolio or {}
    timeframe_confirmation = timeframe_confirmation or {}
    macro_gate = macro_gate or {}

    terminal_ready = (
        bool(account_status.get("connected"))
        and bool(account_status.get("terminal_trade_allowed"))
        and bool(account.get("trade_allowed"))
        and bool(account.get("expert_allowed"))
    ) if account_status else True
    fresh_market = bool(market.get("market_open")) and bool(market.get("tick_fresh")) if "market_open" in market else True
    position_limit_ok = int(portfolio.get("open_position_count") or 0) < settings.maximum_open_positions
    normalized_symbol = str(symbol or "").upper().replace("/", "").replace(" ", "")
    open_by_symbol = portfolio.get("open_position_count_by_symbol") or {}
    daily_by_symbol = portfolio.get("daily_trade_count_by_symbol") or {}
    symbol_position_limit_ok = int(open_by_symbol.get(normalized_symbol) or 0) < settings.maximum_symbol_open_positions
    symbol_daily_trade_limit_ok = int(daily_by_symbol.get(normalized_symbol) or 0) < settings.maximum_symbol_daily_trades
    equity = float(account.get("equity") or 0)
    daily_net = float(portfolio.get("daily_realized_net") or 0)
    daily_loss_percent = abs(min(0.0, daily_net)) / equity * 100 if equity > 0 else 0.0
    daily_loss_ok = daily_loss_percent < settings.maximum_daily_loss_percent
    unprotected_positions_ok = int(portfolio.get("unprotected_position_count") or 0) == 0
    aggregate_open_risk = float(portfolio.get("aggregate_open_risk") or 0)
    aggregate_open_risk_percent = aggregate_open_risk / equity * 100 if equity > 0 else 0.0
    aggregate_open_risk_ok = aggregate_open_risk_percent < settings.maximum_daily_loss_percent
    loss_streak = int(portfolio.get("consecutive_losses") or 0)
    latest_loss_time = portfolio.get("latest_loss_time_utc")
    cooldown_until = None
    if loss_streak >= settings.maximum_consecutive_losses:
        if latest_loss_time:
            try:
                parsed_loss_time = datetime.fromisoformat(str(latest_loss_time).replace("Z", "+00:00"))
                if parsed_loss_time.tzinfo is None:
                    parsed_loss_time = parsed_loss_time.replace(tzinfo=timezone.utc)
                cooldown_until = parsed_loss_time + timedelta(hours=settings.loss_cooldown_hours)
            except ValueError:
                cooldown_until = datetime.max.replace(tzinfo=timezone.utc)
        else:
            cooldown_until = datetime.max.replace(tzinfo=timezone.utc)
    loss_streak_ok = cooldown_until is None or datetime.now(timezone.utc) >= cooldown_until
    daily_trade_limit_ok = int(portfolio.get("daily_trade_count") or 0) < settings.maximum_daily_trades
    timeframe_ok = bool(timeframe_confirmation.get("aligned")) if timeframe_confirmation else True
    macro_ok = bool(macro_gate.get("clear")) if macro_gate else True

    ai_decision = str((ai_assessment or {}).get("decision") or "").lower()
    ai_direction = str((ai_assessment or {}).get("direction") or "").upper()
    ai_confidence = int((ai_assessment or {}).get("confidence") or 0)
    ai_ok = (
        ai_decision == "approve"
        and ai_direction == candidate
        and ai_confidence >= settings.ai_minimum_confidence
    ) if ai_assessment else not settings.require_ai_confirmation
    mtf_score = int(timeframe_confirmation.get("score") or strength)
    if ai_assessment:
        combined_strength = int(round((strength * 0.65) + (mtf_score * 0.20) + (ai_confidence * 0.15)))
    else:
        combined_strength = strength

    filters = {
        "closed_candle": bool(candle_time),
        "data_quality": bool(quality.get("safe_for_signal")),
        "sufficient_strength": strength >= settings.minimum_strength,
        "combined_strength": combined_strength >= settings.minimum_strength,
        "spread_ok": spread_ok,
        "symbol_tradeable": bool(market.get("tradeable")),
        "market_open_and_fresh": fresh_market,
        "terminal_and_account_ready": terminal_ready,
        "position_limit": position_limit_ok,
        "symbol_position_limit": symbol_position_limit_ok,
        "all_open_positions_protected": unprotected_positions_ok,
        "aggregate_open_risk_limit": aggregate_open_risk_ok,
        "daily_loss_limit": daily_loss_ok,
        "loss_streak_limit": loss_streak_ok,
        "daily_trade_limit": daily_trade_limit_ok,
        "symbol_daily_trade_limit": symbol_daily_trade_limit_ok,
        "true_timeframes_aligned": timeframe_ok,
        "macro_risk_clear": macro_ok,
        "ai_confirmed": ai_ok,
        "directional_setup": candidate in {"BUY", "SELL"},
        "not_duplicate": not duplicate,
    }
    passed = all(filters.values())
    direction = candidate if passed else "HOLD"
    reasons = []
    if candidate == "HOLD":
        reasons.append("موتور RSI/MACD هنوز جهت قابل معامله‌ای تأیید نکرده است.")
    if not filters["sufficient_strength"]:
        reasons.append(f"قدرت شواهد {strength}/100 کمتر از حد {settings.minimum_strength} است.")
    if not filters["spread_ok"]:
        if spread_bps is not None:
            reasons.append(
                f"اسپرد {spread_bps} واحد پایه از حد {settings.maximum_spread_bps} بیشتر است."
            )
        else:
            reasons.append(f"اسپرد {spread if spread is not None else '-'} پیپ خارج از حد مجاز است.")
    if not filters["data_quality"]:
        reasons.append("کیفیت یا پیوستگی کندل‌ها برای سیگنال خودکار کافی نیست.")
    if not filters["symbol_tradeable"]:
        reasons.append("نماد در وضعیت قابل معامله نیست.")
    if not filters["market_open_and_fresh"]:
        reasons.append("بازار بسته است یا Tick لحظه‌ای تازه نیست.")
    if not filters["terminal_and_account_ready"]:
        reasons.append("اجازه معامله در ترمینال، حساب یا Expert Advisor فعال نیست.")
    if not filters["position_limit"]:
        reasons.append("حداکثر تعداد پوزیشن باز پر شده است.")
    if not filters["symbol_position_limit"]:
        reasons.append("سقف پوزیشن باز این نماد پر شده است.")
    if not filters["all_open_positions_protected"]:
        reasons.append("حداقل یک پوزیشن باز بدون حد ضرر قابل محاسبه است؛ سیگنال جدید مسدود شد.")
    if not filters["aggregate_open_risk_limit"]:
        reasons.append("ریسک تجمیعی پوزیشن‌های باز به سقف زیان مجاز رسیده است.")
    if not filters["daily_loss_limit"]:
        reasons.append(f"زیان امروز به سقف {settings.maximum_daily_loss_percent}% رسیده است.")
    if not filters["loss_streak_limit"]:
        reasons.append(f"پس از زیان‌های متوالی تا {cooldown_until.isoformat() if cooldown_until else '-'} توقف موقت فعال است.")
    if not filters["daily_trade_limit"]:
        reasons.append(f"سقف {settings.maximum_daily_trades} معامله دمو در امروز پر شده است.")
    if not filters["symbol_daily_trade_limit"]:
        reasons.append(f"سقف {settings.maximum_symbol_daily_trades} معامله دمو برای این نماد در امروز پر شده است.")
    if not filters["true_timeframes_aligned"]:
        reasons.append("تایم‌فریم‌های واقعی H1، H4 و D1 هم‌جهت نیستند.")
    if not filters["macro_risk_clear"]:
        reasons.append(str(macro_gate.get("reason") or "ریسک خبر مهم برای بازه معامله وجود دارد."))
    if not filters["ai_confirmed"]:
        reasons.append("ارزیابی ساختاریافته AI جهت معامله را با اطمینان کافی تأیید نکرد.")
    if duplicate:
        reasons.append("این کندل قبلاً پردازش شده است و سیگنال تکراری صادر نمی‌شود.")
    if passed:
        factors = [str(item) for item in summary.get("signal_factors") or []]
        reasons.extend(factors[:4])

    key_direction = candidate if candidate in {"BUY", "SELL"} else "HOLD"
    return {
        "signal": direction,
        "candidate": candidate,
        "signal_key": _signal_key(symbol, interval, candle_time, key_direction),
        "symbol": symbol,
        "interval": interval,
        "candle_time": candle_time,
        "price": float(summary.get("latest_price") or 0),
        "indicator_strength": strength,
        "combined_strength": combined_strength,
        "ai_confidence": ai_confidence if ai_assessment else None,
        "cooldown_until": cooldown_until.isoformat() if cooldown_until else None,
        "indicator_strength_is_probability": False,
        "filters": filters,
        "reasons": reasons or ["همه فیلترها عبور کردند."],
        "execution_mode": "demo_confirmed" if passed else "blocked",
    }


def _floor_to_step(value: float, step: float) -> float:
    if step <= 0:
        raise TradingRuleError("گام حجم نماد معتبر نیست.")
    decimal_value = Decimal(str(value))
    decimal_step = Decimal(str(step))
    units = (decimal_value / decimal_step).to_integral_value(rounding=ROUND_DOWN)
    return float(units * decimal_step)


def build_risk_plan(
    direction: str,
    summary: dict[str, Any],
    market: dict[str, Any],
    account: dict[str, Any],
    settings: SignalSettings,
    risk_multiplier: float = 1.0,
) -> dict[str, Any] | None:
    settings.validated()
    if direction not in {"BUY", "SELL"}:
        return None

    entry = float(market.get("ask") if direction == "BUY" else market.get("bid") or 0)
    atr = float(summary.get("latest_atr") or 0)
    point = float(market.get("point") or 0)
    tick_size = float(market.get("trade_tick_size") or 0)
    tick_value = float(market.get("trade_tick_value") or 0)
    stops_level = int(market.get("trade_stops_level") or 0)
    if min(entry, atr, point, tick_size, tick_value) <= 0:
        raise TradingRuleError("اطلاعات قیمت، ATR یا ارزش Tick برای محاسبه ریسک کامل نیست.")

    minimum_stop_distance = max(point * stops_level, point)
    stop_distance = max(atr * settings.atr_stop_multiple, minimum_stop_distance)
    if direction == "BUY":
        stop_loss = entry - stop_distance
        take_profit = entry + (stop_distance * settings.reward_risk)
    else:
        stop_loss = entry + stop_distance
        take_profit = entry - (stop_distance * settings.reward_risk)

    equity = float(account.get("equity") or 0)
    risk_multiplier = max(0.25, min(float(risk_multiplier), 1.0))
    effective_risk_percent = settings.risk_percent * risk_multiplier
    risk_amount = equity * (effective_risk_percent / 100)
    risk_per_lot = (stop_distance / tick_size) * tick_value
    if min(equity, risk_amount, risk_per_lot) <= 0:
        raise TradingRuleError("Equity یا ارزش ریسک نماد معتبر نیست.")
    raw_volume = risk_amount / risk_per_lot
    volume_min = float(market.get("volume_min") or 0)
    volume_max = float(market.get("volume_max") or 0)
    volume_step = float(market.get("volume_step") or 0)
    volume = _floor_to_step(min(raw_volume, volume_max, settings.maximum_volume), volume_step)
    if volume < volume_min:
        raise TradingRuleError(
            "با این Equity و حد ضرر، حجم ایمن از حداقل حجم کارگزاری کمتر است؛ معامله رد شد."
        )

    actual_risk = volume * risk_per_lot
    digits = int(market.get("digits") or 5)
    return {
        "entry": round(entry, digits),
        "stop_loss": round(stop_loss, digits),
        "take_profit": round(take_profit, digits),
        "stop_distance": round(stop_distance, digits),
        "reward_risk": float(settings.reward_risk),
        "risk_percent_requested": float(settings.risk_percent),
        "risk_multiplier": round(risk_multiplier, 3),
        "risk_percent_effective": round(effective_risk_percent, 4),
        "risk_amount_limit": round(risk_amount, 2),
        "volume_raw": round(raw_volume, 6),
        "volume_cap": float(settings.maximum_volume),
        "volume": volume,
        "estimated_risk_amount": round(actual_risk, 2),
        "equity": round(equity, 2),
        "currency": str(account.get("currency") or ""),
        "validated": math.isfinite(volume) and volume >= volume_min and volume <= volume_max,
    }


def capital_feasibility(summary, market, *, equity, risk_percent, atr_stop_multiple, risk_multiplier=1.0):
    """Explain whether broker minimum volume fits the requested risk budget."""
    atr = float(summary.get("latest_atr") or 0)
    point = float(market.get("point") or 0)
    tick_size = float(market.get("trade_tick_size") or 0)
    tick_value = float(market.get("trade_tick_value") or 0)
    volume_min = float(market.get("volume_min") or 0)
    stops_level = int(market.get("trade_stops_level") or 0)
    if min(atr, point, tick_size, tick_value, volume_min, float(equity)) <= 0:
        return {"feasible": False, "reason": "missing_contract_or_account_data"}
    effective_risk_percent = float(risk_percent) * max(0.25, min(float(risk_multiplier), 1.0))
    stop_distance = max(atr * float(atr_stop_multiple), point * max(stops_level, 1))
    risk_per_lot = (stop_distance / tick_size) * tick_value
    minimum_volume_risk = volume_min * risk_per_lot
    risk_budget = float(equity) * effective_risk_percent / 100
    minimum_equity = minimum_volume_risk / (effective_risk_percent / 100)
    return {
        "feasible": risk_budget + 1e-9 >= minimum_volume_risk,
        "equity": round(float(equity), 2),
        "effective_risk_percent": round(effective_risk_percent, 4),
        "risk_budget": round(risk_budget, 2),
        "broker_minimum_volume": volume_min,
        "minimum_volume_risk": round(minimum_volume_risk, 2),
        "minimum_equity_for_profile": round(minimum_equity, 2),
        "stop_distance": round(stop_distance, int(market.get("digits") or 5)),
    }
