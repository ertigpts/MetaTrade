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
                "TAHLIL_AI_MODEL": "test-model",
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
