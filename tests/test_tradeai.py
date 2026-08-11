import os
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import storage


TEST_DIR = Path(tempfile.mkdtemp(prefix="tradeai-tests-"))
os.environ["TAHLIL_DATABASE_PATH"] = str(TEST_DIR / "test.sqlite3")
os.environ["TAHLIL_SECRET_KEY"] = "test-secret-key"

from analytics_engine import (
    _signal_at,
    _signal_series,
    calculate_atr,
    multi_timeframe_alignment,
    run_backtest,
    run_ohlc_backtest,
    monte_carlo_trade_risk,
    latest_strategy_signal,
)
from strategy_profiles import get_strategy_profile
from multi_asset_research import _provider_payload
from market_intelligence import (
    classify_market_regime, detect_market_drift, performance_drift,
    route_timeframe, strategy_regime_risk,
)
from app import (
    _ai_config_chat,
    _call_ai_chat,
    _compute_signal_summary,
    _extract_ai_content,
    _fetch_businessquant_calendar,
    _get_macro_context,
    _macro_trade_gate,
    _parse_ai_json,
    _true_timeframe_confirmation,
    _validate_trade_ai_assessment,
    _validate_ai_analysis,
    app,
)
from technical_indicators import calculate_macd, calculate_rsi


def sample_prices(count=180):
    x = np.linspace(0, 12, count)
    return (1.1 + (np.sin(x) * 0.01) + (np.arange(count) * 0.00008)).tolist()


class AnalyticsTests(unittest.TestCase):
    def test_market_intelligence_only_holds_or_reduces_risk(self):
        trending = np.linspace(100, 130, 300)
        regime = classify_market_regime(trending + 0.2, trending - 0.2, trending)
        self.assertIn(regime["regime"], {"trend", "range", "volatile", "uncertain"})
        self.assertLessEqual(regime["risk_multiplier"], 1.0)
        drift = detect_market_drift(trending)
        self.assertLessEqual(drift["risk_multiplier"], 1.0)
        self.assertLessEqual(strategy_regime_risk("ema_pullback", "volatile"), 0.25)

    def test_performance_drift_flags_repeated_bad_folds(self):
        result = performance_drift({"folds": [
            {"trade_count": 20, "total_return_pct": 1, "profit_factor": 1.2},
            {"trade_count": 20, "total_return_pct": -1, "profit_factor": 0.7},
            {"trade_count": 20, "total_return_pct": -0.5, "profit_factor": 0.8},
        ]})
        self.assertEqual(result["level"], "high")
        self.assertTrue(result["block_new_entries"])

    def test_router_holds_volatile_market_and_routes_gold_trend_to_h4(self):
        self.assertEqual(route_timeframe("XAUUSD", {"regime": "volatile"})["decision"], "HOLD")
        routed = route_timeframe("XAU/USD", {"regime": "trend"})
        self.assertEqual(routed["recommended_interval"], "4h")

    def test_precomputed_signals_match_incremental_calculation(self):
        prices = np.asarray(sample_prices(180), dtype=np.float64)
        signals = _signal_series(prices, 14, 12, 26, 9)
        expected = [
            _signal_at(prices, index, 14, 12, 26, 9)
            for index in range(len(prices))
        ]
        self.assertEqual(signals.tolist(), expected)

    def test_database_falls_back_when_deploy_path_is_not_writable(self):
        blocked_parent = TEST_DIR / "blocked-parent"
        blocked_parent.write_text("not a directory", encoding="utf-8")
        fallback_path = TEST_DIR / "runtime" / "tradeai.sqlite3"

        with (
            patch.object(storage, "_ACTIVE_DATABASE_PATH", None),
            patch.object(
                storage,
                "_database_candidates",
                return_value=[blocked_parent / "tradeai.sqlite3", fallback_path],
            ),
        ):
            db = storage._open_database()
            try:
                self.assertEqual(storage._ACTIVE_DATABASE_PATH, fallback_path)
            finally:
                db.close()

    def test_broker_linked_journal_reconciliation_is_exact(self):
        owner = "user:reconcile-test"
        linked_id = storage.add_journal_entry(owner, {
            "symbol": "XAUUSD", "direction": "buy", "status": "open",
            "entry_price": 2000, "signal_key": "signal-exact",
            "order_ticket": 11, "deal_ticket": 22,
        })
        storage.add_journal_entry(owner, {
            "symbol": "XAUUSD", "direction": "buy", "status": "open",
            "entry_price": 2000, "signal_key": "another-signal",
        })
        changed = storage.reconcile_journal_entry(owner, "signal-exact", {
            "exit_price": 2010, "realized_net": 1.25,
        })
        self.assertTrue(changed)
        rows = {item["id"]: item for item in storage.list_journal(owner)}
        self.assertEqual(rows[linked_id]["status"], "won")
        self.assertEqual(rows[linked_id]["realized_net"], 1.25)
        self.assertEqual(sum(item["status"] == "open" for item in rows.values()), 1)
        performance = storage.journal_performance(owner)
        self.assertEqual(performance["closed_trade_count"], 1)
        self.assertEqual(performance["realized_net"], 1.25)
        self.assertFalse(performance["evidence_sufficient"])

    def test_atr_and_timeframe_alignment(self):
        closes = sample_prices(80)
        highs = [value + 0.001 for value in closes]
        lows = [value - 0.001 for value in closes]
        atr = calculate_atr(highs, lows, closes)
        self.assertGreater(float(atr.dropna().iloc[-1]), 0)
        alignment = multi_timeframe_alignment(closes)
        self.assertIn(alignment["alignment"], {"bullish", "bearish", "mixed"})

    def test_backtest_is_deterministic_and_has_risk_metrics(self):
        result_a = run_backtest(sample_prices(), holding_bars=5, fee_bps=2)
        result_b = run_backtest(sample_prices(), holding_bars=5, fee_bps=2)
        self.assertEqual(result_a, result_b)
        for key in ("trade_count", "win_rate", "profit_factor", "expectancy_pct", "max_drawdown_pct"):
            self.assertIn(key, result_a)

    def test_backtest_rejects_insufficient_data(self):
        with self.assertRaises(ValueError):
            run_backtest(sample_prices(40))

    def test_ohlc_backtest_enters_on_next_bar_and_reports_costs(self):
        closes = sample_prices(220)
        opens = [closes[0], *closes[:-1]]
        highs = [max(open_price, close) + 0.0005 for open_price, close in zip(opens, closes)]
        lows = [min(open_price, close) - 0.0005 for open_price, close in zip(opens, closes)]
        timestamps = [f"2026-01-{1 + index // 24:02d}T{index % 24:02d}:00:00+00:00" for index in range(len(closes))]
        result = run_ohlc_backtest(
            opens, highs, lows, closes, timestamps=timestamps,
            holding_bars=5, spread_bps=1.5, slippage_bps_per_side=0.2,
        )
        self.assertEqual(result["engine"], "ohlc_next_bar_conservative")
        self.assertIn("cooldown_count", result)
        self.assertIn("buy_hold_pct", result)
        self.assertIn("equity_curve", result)
        if result["trades"]:
            first = result["trades"][0]
            self.assertEqual(first["entry_index"], first["signal_index"] + 1)
            self.assertIn(first["exit_reason"], {"stop", "stop_first_conservative", "target", "time"})

    def test_all_strategy_families_are_causal_and_auditable(self):
        closes = sample_prices(260)
        opens = [closes[0], *closes[:-1]]
        highs = [max(a, b) + 0.0005 for a, b in zip(opens, closes)]
        lows = [min(a, b) - 0.0005 for a, b in zip(opens, closes)]
        cases = (
            ("rsi_macd", {}),
            ("ema_pullback", {"fast_period": 8, "slow_period": 34}),
            ("regime_ema_pullback", {
                "fast_period": 13, "slow_period": 55,
                "efficiency_window": 20, "minimum_efficiency": 0.25,
                "volatility_window": 20, "volatility_baseline": 100,
                "maximum_volatility_ratio": 1.75,
            }),
            ("donchian_breakout", {"lookback": 20}),
            ("ema_trend_breakout", {"lookback": 24, "fast_period": 13,
                                     "slow_period": 55, "slope_bars": 6}),
            ("bollinger_reversion", {"band_period": 20, "band_deviation": 1.5,
                                      "rsi_period": 9, "rsi_threshold": 35}),
            ("london_session_breakout", {
                "fast_period": 13, "slow_period": 55,
                "asia_start_utc": 0, "asia_end_utc": 7,
                "london_start_utc": 7, "london_end_utc": 11,
                "breakout_buffer_bps": 1.0,
            }),
        )
        for family, options in cases:
            with self.subTest(family=family):
                result = run_ohlc_backtest(
                    opens, highs, lows, closes, strategy_family=family,
                    strategy_options=options, holding_bars=6,
                )
                self.assertEqual(result["strategy_family"], family)
                for trade in result["trades"]:
                    self.assertEqual(trade["entry_index"], trade["signal_index"] + 1)

    def test_latest_donchian_signal_uses_only_closed_history(self):
        prices = [100.0] * 25 + [101.0]
        result = latest_strategy_signal(prices + [102.0] * 30, "donchian_breakout", {"lookback": 20})
        self.assertIn(result["action_bias"], {"BUY bias", "Wait"})
        breakout = latest_strategy_signal([100.0] * 50 + [101.0], "donchian_breakout", {"lookback": 20})
        self.assertEqual(breakout["action_bias"], "BUY bias")

    def test_monte_carlo_is_deterministic_and_reports_adverse_path(self):
        trades = [{"pnl_pct": 0.2 if index % 3 else -0.1} for index in range(60)]
        first = monte_carlo_trade_risk(trades, simulations=500, seed=7)
        second = monte_carlo_trade_risk(trades, simulations=500, seed=7)
        self.assertEqual(first, second)
        self.assertTrue(first["available"])
        self.assertIn("p95_adverse", first["maximum_drawdown_pct"])

    def test_h1_is_registered_but_not_execution_qualified(self):
        h1 = get_strategy_profile("XAU/USD", "H1")
        h4 = get_strategy_profile("XAUUSD", "4h")
        self.assertIsNotNone(h1)
        self.assertFalse(h1.research_qualified)
        self.assertTrue(h4.research_qualified)

    def test_forex_profiles_are_forward_demo_only(self):
        for symbol in ("EUR/USD", "GBP/USD", "USD/JPY"):
            profile = get_strategy_profile(symbol, "H4")
            self.assertIsNotNone(profile)
            self.assertFalse(profile.research_qualified)
            self.assertTrue(profile.forward_demo_enabled)
            self.assertEqual(profile.maximum_volume, 0.01)
            self.assertEqual(profile.maximum_symbol_daily_trades, 5)

    def test_gold_m15_is_explicitly_experimental(self):
        profile = get_strategy_profile("XAU/USD", "15min")
        self.assertIsNotNone(profile)
        self.assertEqual(profile.primary_timeframe, "M15")
        self.assertFalse(profile.research_qualified)
        self.assertTrue(profile.forward_demo_enabled)
        self.assertEqual(profile.strategy_family, "ema_pullback")

    def test_m15_primary_requires_m15_confirmation(self):
        summaries = {
            "M15": {"action_bias": "Wait", "macd_bias": "Neutral"},
            "H1": {"action_bias": "Buy bias", "macd_bias": "Bullish", "buy_score": 20},
            "H4": {"action_bias": "Buy bias", "macd_bias": "Bullish", "buy_score": 20},
            "D1": {"action_bias": "Buy bias", "macd_bias": "Bullish", "buy_score": 20},
        }
        result = _true_timeframe_confirmation(summaries, "BUY", "M15")
        self.assertFalse(result["aligned"])
        self.assertEqual(result["source"], "real_mt5_M15_H1_H4_D1")

    def test_experimental_tdigm_does_not_inflate_score(self):
        prices = sample_prices(100)
        rsi = calculate_rsi(prices)
        macd = calculate_macd(prices)
        base = _compute_signal_summary(prices, rsi, macd, use_tdigm=False)
        experimental = _compute_signal_summary(prices, rsi, macd, use_tdigm=True, tdigm_value=99)
        self.assertEqual(base["signal_strength"], experimental["signal_strength"])

    def test_ai_schema_is_normalized(self):
        valid = {
            "market_state": "range",
            "profile_used": "scalp",
            "action_bias": "no-trade",
            "confidence": 200,
            "execution_type": "no-trade",
            "holding_time_minutes": 0,
            "liquidity_note": "normal",
            "entry_idea": "none",
            "stop_loss_idea": "none",
            "take_profit_idea": "none",
            "why": ["mixed"],
            "risk_warnings": ["risk"],
            "nds_checklist": [],
        }
        self.assertEqual(_validate_ai_analysis(valid)["confidence"], 100)

    def test_ai_content_variants_are_supported(self):
        list_content = {
            "choices": [{"message": {"content": [{"type": "text", "text": "```json\n{\"ok\": true}\n```"}]}}]
        }
        self.assertEqual(_parse_ai_json(_extract_ai_content(list_content)), {"ok": True})
        responses_content = {
            "output": [{"content": [{"type": "output_text", "text": "{\"ok\": true}"}]}]
        }
        self.assertEqual(_parse_ai_json(_extract_ai_content(responses_content)), {"ok": True})

    def test_trade_ai_cannot_approve_the_opposite_direction(self):
        value = {
            "decision": "approve", "direction": "SELL", "confidence": 95,
            "risk_multiplier": 1.5, "regime": "trend", "news_risk": "low",
            "reasons": ["test"], "invalidators": [],
        }
        result = _validate_trade_ai_assessment(value, "BUY")
        self.assertEqual(result["decision"], "veto")
        self.assertEqual(result["risk_multiplier"], 1.0)

    def test_real_timeframe_alignment_requires_h4_and_two_confirmations(self):
        summaries = {
            "H1": {"action_bias": "Buy bias", "macd_bias": "Bullish", "buy_score": 20, "sell_score": 2},
            "H4": {"action_bias": "Buy bias", "macd_bias": "Bullish", "buy_score": 24, "sell_score": 1},
            "D1": {"action_bias": "Wait", "macd_bias": "Neutral", "buy_score": 5, "sell_score": 5},
        }
        result = _true_timeframe_confirmation(summaries, "BUY")
        self.assertTrue(result["aligned"])
        self.assertEqual(result["source"], "real_mt5_H1_H4_D1")

    def test_h1_primary_must_itself_confirm(self):
        summaries = {
            "H1": {"action_bias": "Wait", "macd_bias": "Neutral", "buy_score": 5, "sell_score": 5},
            "H4": {"action_bias": "Buy bias", "macd_bias": "Bullish", "buy_score": 24, "sell_score": 1},
            "D1": {"action_bias": "Buy bias", "macd_bias": "Bullish", "buy_score": 20, "sell_score": 2},
        }
        result = _true_timeframe_confirmation(summaries, "BUY", "H1")
        self.assertFalse(result["aligned"])
        self.assertEqual(result["primary_timeframe"], "H1")

    def test_unknown_macro_calendar_blocks_trade(self):
        result = _macro_trade_gate({"available": False})
        self.assertFalse(result["clear"])

    @patch("app._build_retry_session")
    def test_businessquant_calendar_keeps_major_date_level_events(self, retry_session):
        response = Mock()
        response.json.return_value = {
            "data": [
                {
                    "code": "E:USCPI.YOY",
                    "name": "Inflation Rate",
                    "category": "Inflation",
                    "next_release": "2026-08-12",
                    "latest_value": 3.1,
                    "prior_value": 3.0,
                },
                {
                    "code": "E:USINVENT",
                    "name": "Business Inventories",
                    "category": "Business",
                    "next_release": "2026-08-14",
                },
            ]
        }
        response.raise_for_status.return_value = None
        session_client = retry_session.return_value.__enter__.return_value
        session_client.get.return_value = response

        result = _fetch_businessquant_calendar("test-key", date(2026, 8, 9), 7)

        self.assertTrue(result["available"])
        self.assertEqual(result["event_count"], 1)
        self.assertEqual(result["events"][0]["code"], "E:USCPI.YOY")
        self.assertEqual(result["precision"], "date_only")
        self.assertNotIn("api_key", str(result))

    @patch("app._build_retry_session")
    def test_twelvedata_http_error_does_not_expose_request_url(self, retry_session):
        response = Mock()
        response.ok = False
        response.status_code = 404
        response.url = "https://api.example.test/data?apikey=secret-value"
        retry_session.return_value.__enter__.return_value.get.return_value = response
        from app import _fetch_twelvedata_time_series
        with self.assertRaises(Exception) as caught:
            _fetch_twelvedata_time_series("BAD", "4h", 100, "secret-value")
        self.assertNotIn("secret-value", str(caught.exception))
        self.assertNotIn("apikey", str(caught.exception))

    @patch("multi_asset_research._fetch_twelvedata_time_series")
    def test_provider_payload_excludes_newest_bar(self, fetch):
        values = []
        for index in range(220):
            close = 100 + index * 0.1
            values.append({
                "datetime": f"2026-01-{1 + index // 24:02d} {index % 24:02d}:00:00",
                "open": str(close - 0.02), "high": str(close + 0.05),
                "low": str(close - 0.05), "close": str(close),
            })
        fetch.return_value = {"status": "ok", "values": list(reversed(values))}
        payload = _provider_payload("XAU/USD", "4h", 220, "key")
        self.assertEqual(len(payload["prices"]), 219)
        self.assertTrue(payload["quality"]["latest_bar_excluded"])

    def test_macro_context_fails_open_without_key(self):
        with patch.dict(os.environ, {"BUSINESSQUANT_API_KEY": "", "TAHLIL_BUSINESSQUANT_API_KEY": ""}):
            result = _get_macro_context()
        self.assertFalse(result["available"])
        self.assertEqual(result["reason"], "not_configured")

    def test_chat_honors_explicit_endpoint(self):
        with patch.dict(
            os.environ,
            {
                "TAHLIL_AI_API_KEY": "test-key",
                "TAHLIL_AI_PRIMARY_MODEL": "test-model",
                "TAHLIL_AI_ENDPOINT": "https://example.test/custom/chat",
            },
        ):
            key, model, endpoint = _ai_config_chat()
        self.assertEqual((key, model, endpoint), ("test-key", "test-model", "https://example.test/custom/chat"))

    @patch("app.requests.Session")
    def test_chat_supports_list_content_and_timeout_tuple(self, session_cls):
        response = Mock()
        response.json.return_value = {
            "choices": [{"message": {"content": [{"type": "text", "text": "پاسخ استاد"}]}}],
            "usage": {},
        }
        response.raise_for_status.return_value = None
        session_client = session_cls.return_value.__enter__.return_value
        session_client.post.return_value = response

        reply = _call_ai_chat(
            [{"role": "user", "content": "سلام"}],
            "test-key",
            "test-model",
            "https://example.test/chat",
        )

        self.assertEqual(reply, "پاسخ استاد")
        self.assertEqual(session_client.post.call_args.kwargs["timeout"], (8, 45))


class ApiTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 200)
        with self.client.session_transaction() as flask_session:
            self.csrf = flask_session["csrf_token"]
        self.headers = {"X-CSRF-Token": self.csrf, "Content-Type": "application/json"}

    def test_calculate_requires_csrf(self):
        response = self.client.post("/calculate_indicators", json={"prices": sample_prices(80)})
        self.assertEqual(response.status_code, 403)

    def test_calculate_persists_history_and_explains_strength(self):
        prices = sample_prices(100)
        response = self.client.post(
            "/calculate_indicators",
            json={
                "prices": prices,
                "highs": [value + 0.001 for value in prices],
                "lows": [value - 0.001 for value in prices],
                "symbol": "EUR/USD",
                "interval": "1h",
            },
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        payload = response.get_json()
        self.assertIn("ATR", payload)
        self.assertIn("signal_strength", payload["summary"])
        self.assertEqual(payload["summary"]["signal_strength_label"], "Indicator agreement score")

        history = self.client.get("/history").get_json()["items"]
        self.assertTrue(history)
        self.assertEqual(history[0]["symbol"], "EUR/USD")

    def test_backtest_endpoint(self):
        response = self.client.post(
            "/backtest",
            json={"prices": sample_prices(), "holding_bars": 5, "fee_bps": 2},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertIn("max_drawdown_pct", response.get_json())

    def test_journal_validation_and_storage(self):
        bad = self.client.post(
            "/journal",
            json={"symbol": "EUR/USD", "direction": "sideways"},
            headers=self.headers,
        )
        self.assertEqual(bad.status_code, 400)
        created = self.client.post(
            "/journal",
            json={
                "symbol": "EUR/USD",
                "direction": "buy",
                "entry_price": 1.1,
                "status": "open",
                "notes": "test",
            },
            headers=self.headers,
        )
        self.assertEqual(created.status_code, 201)
        items = self.client.get("/journal").get_json()["items"]
        self.assertEqual(items[0]["notes"], "test")

    def test_security_headers(self):
        response = self.client.get("/")
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")


if __name__ == "__main__":
    unittest.main()
