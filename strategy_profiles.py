"""Auditable strategy registry separating research candidates from execution."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class StrategyProfile:
    symbol: str
    interval: str
    primary_timeframe: str
    research_qualified: bool
    forward_demo_enabled: bool
    qualification_note: str
    rsi_period: int
    macd_short: int
    macd_long: int
    macd_signal: int
    holding_bars: int
    atr_stop_multiple: float
    reward_risk: float
    risk_percent: float
    maximum_daily_trades: int
    strategy_family: str = "rsi_macd"
    strategy_options: dict[str, Any] = field(default_factory=dict)
    minimum_strength: int = 70
    maximum_spread_pips: float = 2.0
    maximum_spread_bps: float = 3.0
    maximum_volume: float = 0.1
    maximum_daily_loss_percent: float = 1.0
    maximum_open_positions: int = 1
    maximum_symbol_open_positions: int = 1
    maximum_symbol_daily_trades: int = 1
    maximum_consecutive_losses: int = 2
    loss_cooldown_hours: int = 12
    ai_minimum_confidence: int = 70
    minimum_out_of_sample_trades: int = 100
    minimum_profit_factor: float = 1.15

    def public(self) -> dict[str, Any]:
        return asdict(self)


# H4 passed the 2026-08-09 multi-family 5,000-candle study, all five
# chronological folds, doubled costs and Monte Carlo. H1 remains research-only.
PROFILES = {
    ("XAUUSD", "4h"): StrategyProfile(
        symbol="XAUUSD", interval="4h", primary_timeframe="H4",
        research_qualified=True, forward_demo_enabled=True,
        qualification_note="Donchian H4 passed all historical gates; forward-demo proof is still required.",
        rsi_period=21, macd_short=8, macd_long=21, macd_signal=5,
        holding_bars=12, atr_stop_multiple=2.0, reward_risk=2.0,
        risk_percent=0.1, maximum_daily_trades=20,
        strategy_family="donchian_breakout", strategy_options={"lookback": 20},
        maximum_open_positions=4, maximum_symbol_daily_trades=5,
    ),
    ("XAUUSD", "1h"): StrategyProfile(
        symbol="XAUUSD", interval="1h", primary_timeframe="H1",
        research_qualified=False, forward_demo_enabled=False,
        qualification_note="Research only: H1 missed the Monte Carlo qualification threshold.",
        rsi_period=21, macd_short=12, macd_long=26, macd_signal=9,
        holding_bars=6, atr_stop_multiple=2.0, reward_risk=3.0,
        risk_percent=0.1, maximum_daily_trades=5,
        strategy_family="donchian_breakout", strategy_options={"lookback": 80},
    ),
    ("XAUUSD", "15min"): StrategyProfile(
        symbol="XAUUSD", interval="15min", primary_timeframe="M15",
        research_qualified=False, forward_demo_enabled=True,
        qualification_note=(
            "Experimental forward demo: final test, doubled costs, Monte Carlo and 4/5 folds passed, "
            "but validation and broker-history integrity gates failed."
        ),
        rsi_period=14, macd_short=12, macd_long=26, macd_signal=9,
        holding_bars=6, atr_stop_multiple=1.5, reward_risk=2.5,
        risk_percent=0.1, maximum_daily_trades=20,
        strategy_family="ema_pullback",
        strategy_options={"fast_period": 21, "slow_period": 89},
        minimum_strength=80, ai_minimum_confidence=80, maximum_volume=0.01,
        maximum_daily_loss_percent=0.25, maximum_open_positions=4,
        maximum_symbol_daily_trades=5, maximum_consecutive_losses=2,
        loss_cooldown_hours=12,
    ),
    # The following frozen H4 candidates are deliberately marked experimental.
    # They failed one or more historical qualification gates, but may collect
    # tiny, manually-confirmed forward-demo observations. They are never
    # presented as qualified strategies and cannot be used on a real account.
    ("EURUSD", "4h"): StrategyProfile(
        symbol="EURUSD", interval="4h", primary_timeframe="H4",
        research_qualified=False, forward_demo_enabled=True,
        qualification_note="Experimental forward demo: historical out-of-sample and stress gates failed.",
        rsi_period=21, macd_short=12, macd_long=26, macd_signal=9,
        holding_bars=6, atr_stop_multiple=1.5, reward_risk=1.0,
        risk_percent=0.1, maximum_daily_trades=20,
        strategy_family="bollinger_reversion",
        strategy_options={"rsi_period": 14, "rsi_threshold": 25, "band_period": 20, "band_deviation": 1.5},
        minimum_strength=75, ai_minimum_confidence=75, maximum_volume=0.01,
        maximum_daily_loss_percent=0.5, maximum_open_positions=4,
        maximum_symbol_daily_trades=5,
    ),
    ("GBPUSD", "4h"): StrategyProfile(
        symbol="GBPUSD", interval="4h", primary_timeframe="H4",
        research_qualified=False, forward_demo_enabled=True,
        qualification_note="Experimental forward demo: historical out-of-sample and stress gates failed.",
        rsi_period=21, macd_short=12, macd_long=26, macd_signal=9,
        holding_bars=3, atr_stop_multiple=1.5, reward_risk=1.5,
        risk_percent=0.1, maximum_daily_trades=20,
        strategy_family="bollinger_reversion",
        strategy_options={"rsi_period": 14, "rsi_threshold": 30, "band_period": 20, "band_deviation": 1.5},
        minimum_strength=75, ai_minimum_confidence=75, maximum_volume=0.01,
        maximum_daily_loss_percent=0.5, maximum_open_positions=4,
        maximum_symbol_daily_trades=5,
    ),
    ("USDJPY", "4h"): StrategyProfile(
        symbol="USDJPY", interval="4h", primary_timeframe="H4",
        research_qualified=False, forward_demo_enabled=True,
        qualification_note="Experimental forward demo: validation, out-of-sample and stress gates failed.",
        rsi_period=21, macd_short=12, macd_long=26, macd_signal=9,
        holding_bars=12, atr_stop_multiple=1.5, reward_risk=2.5,
        risk_percent=0.1, maximum_daily_trades=20,
        strategy_family="ema_pullback", strategy_options={"fast_period": 13, "slow_period": 34},
        minimum_strength=75, ai_minimum_confidence=75, maximum_volume=0.01,
        maximum_daily_loss_percent=0.5, maximum_open_positions=4,
        maximum_symbol_daily_trades=5,
    ),
}


def normalize_symbol(value: str) -> str:
    return str(value or "").strip().upper().replace("/", "").replace(" ", "")


def normalize_interval(value: str) -> str:
    normalized = str(value or "").strip().lower()
    return {"h1": "1h", "h4": "4h"}.get(normalized, normalized)


def get_strategy_profile(symbol: str, interval: str) -> StrategyProfile | None:
    return PROFILES.get((normalize_symbol(symbol), normalize_interval(interval)))
