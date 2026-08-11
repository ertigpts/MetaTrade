import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from trading_engine import SignalSettings, TradingRuleError, build_risk_plan, capital_feasibility, generate_signal


def summary():
    return {
        "action_bias": "Buy bias",
        "signal_strength": 72,
        "latest_price": 1.10002,
        "latest_atr": 0.001,
        "signal_factors": ["MACD bullish", "RSI confirms"],
    }


def market():
    return {
        "symbol": "EURUSD",
        "bid": 1.10000,
        "ask": 1.10002,
        "spread_pips": 0.2,
        "spread_bps": 1.8,
        "tradeable": True,
        "point": 0.00001,
        "digits": 5,
        "trade_stops_level": 10,
        "trade_tick_size": 0.00001,
        "trade_tick_value": 1.0,
        "volume_min": 0.01,
        "volume_max": 100.0,
        "volume_step": 0.01,
    }


class TradingEngineTests(unittest.TestCase):
    def test_capital_feasibility_rejects_broker_minimum_above_budget(self):
        result = capital_feasibility(
            {"latest_atr": 42.0},
            {"point": 0.01, "digits": 2, "trade_tick_size": 0.01,
             "trade_tick_value": 0.1, "volume_min": 0.01, "trade_stops_level": 0},
            equity=100, risk_percent=0.1, atr_stop_multiple=1.0,
        )
        self.assertFalse(result["feasible"])
        self.assertGreater(result["minimum_equity_for_profile"], 4_000)

    def test_signal_requires_every_filter(self):
        settings = SignalSettings()
        accepted = generate_signal(
            summary(), market(), {"safe_for_signal": True},
            symbol="EURUSD", interval="15min", candle_time="2026-08-09T10:00:00+00:00",
            settings=settings,
        )
        self.assertEqual(accepted["signal"], "BUY")
        self.assertFalse(accepted["indicator_strength_is_probability"])

        wide_market = {**market(), "spread_pips": 5.0, "spread_bps": 5.0}
        rejected = generate_signal(
            summary(), wide_market, {"safe_for_signal": True},
            symbol="EURUSD", interval="15min", candle_time="2026-08-09T10:00:00+00:00",
            settings=settings,
        )
        self.assertEqual(rejected["signal"], "HOLD")
        self.assertFalse(rejected["filters"]["spread_ok"])

    def test_duplicate_signal_is_held(self):
        signal = generate_signal(
            summary(), market(), {"safe_for_signal": True},
            symbol="EURUSD", interval="15min", candle_time="2026-08-09T10:00:00+00:00",
            settings=SignalSettings(), duplicate=True,
        )
        self.assertEqual(signal["signal"], "HOLD")
        self.assertFalse(signal["filters"]["not_duplicate"])

    def test_unprotected_or_excess_aggregate_risk_blocks_new_signal(self):
        blocked = generate_signal(
            summary(), market(), {"safe_for_signal": True},
            symbol="EURUSD", interval="15min", candle_time="2026-08-09T10:00:00+00:00",
            settings=SignalSettings(maximum_open_positions=3),
            account_status={"connected": True, "terminal_trade_allowed": True,
                            "account": {"trade_allowed": True, "expert_allowed": True, "equity": 10_000}},
            portfolio={"open_position_count": 1, "unprotected_position_count": 1,
                       "aggregate_open_risk": 150},
        )
        self.assertEqual(blocked["signal"], "HOLD")
        self.assertFalse(blocked["filters"]["all_open_positions_protected"])
        self.assertFalse(blocked["filters"]["aggregate_open_risk_limit"])

    def test_symbol_level_limits_block_only_that_market(self):
        blocked = generate_signal(
            summary(), market(), {"safe_for_signal": True},
            symbol="EUR/USD", interval="4h", candle_time="2026-08-09T08:00:00+00:00",
            settings=SignalSettings(maximum_open_positions=4),
            portfolio={
                "open_position_count": 1,
                "open_position_count_by_symbol": {"EURUSD": 1},
                "daily_trade_count_by_symbol": {"EURUSD": 1},
            },
        )
        self.assertEqual(blocked["signal"], "HOLD")
        self.assertFalse(blocked["filters"]["symbol_position_limit"])
        self.assertFalse(blocked["filters"]["symbol_daily_trade_limit"])

    def test_risk_plan_uses_equity_and_floors_volume(self):
        plan = build_risk_plan(
            "BUY", summary(), market(), {"equity": 10_000, "currency": "USD"}, SignalSettings()
        )
        self.assertTrue(plan["validated"])
        self.assertLessEqual(plan["estimated_risk_amount"], plan["risk_amount_limit"])
        self.assertGreaterEqual(plan["volume"], market()["volume_min"])
        self.assertLessEqual(plan["volume"], 0.1)

    def test_risk_above_two_percent_is_rejected(self):
        with self.assertRaises(TradingRuleError):
            SignalSettings(risk_percent=3).validated()

    def test_demo_daily_limit_allows_twenty_but_not_more(self):
        self.assertEqual(SignalSettings(maximum_daily_trades=20).validated().maximum_daily_trades, 20)
        with self.assertRaises(TradingRuleError):
            SignalSettings(maximum_daily_trades=21).validated()

    def test_ai_and_live_safety_gates_fail_closed(self):
        settings = SignalSettings(require_ai_confirmation=True, minimum_strength=70)
        blocked = generate_signal(
            summary(),
            {**market(), "market_open": False, "tick_fresh": False},
            {"safe_for_signal": False},
            symbol="EURUSD", interval="15min", candle_time="2026-08-09T10:00:00+00:00",
            settings=settings,
            account_status={
                "connected": True,
                "terminal_trade_allowed": False,
                "account": {"trade_allowed": True, "expert_allowed": True, "equity": 10_000},
            },
            timeframe_confirmation={"aligned": True, "score": 80},
            macro_gate={"clear": True},
            ai_assessment={"decision": "approve", "direction": "BUY", "confidence": 90},
        )
        self.assertEqual(blocked["signal"], "HOLD")
        self.assertFalse(blocked["filters"]["market_open_and_fresh"])
        self.assertFalse(blocked["filters"]["terminal_and_account_ready"])

    def test_ai_can_only_reduce_position_risk(self):
        plan = build_risk_plan(
            "BUY", summary(), market(), {"equity": 10_000, "currency": "USD"},
            SignalSettings(risk_percent=0.5, maximum_volume=10), risk_multiplier=0.5,
        )
        self.assertEqual(plan["risk_percent_effective"], 0.25)
        self.assertLessEqual(plan["estimated_risk_amount"], 25.0)

    def test_loss_streak_uses_temporary_cooldown(self):
        settings = SignalSettings(maximum_consecutive_losses=2, loss_cooldown_hours=12)
        common = dict(
            summary=summary(), market=market(), quality={"safe_for_signal": True},
            symbol="EURUSD", interval="15min", candle_time="2026-08-09T10:00:00+00:00",
            settings=settings,
        )
        recent = generate_signal(
            **common,
            portfolio={
                "consecutive_losses": 2,
                "latest_loss_time_utc": datetime.now(timezone.utc).isoformat(),
            },
        )
        expired = generate_signal(
            **common,
            portfolio={
                "consecutive_losses": 2,
                "latest_loss_time_utc": (datetime.now(timezone.utc) - timedelta(hours=13)).isoformat(),
            },
        )
        self.assertFalse(recent["filters"]["loss_streak_limit"])
        self.assertTrue(expired["filters"]["loss_streak_limit"])


if __name__ == "__main__":
    unittest.main()
