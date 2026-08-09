import os
import sys
import time
import unittest
from collections import namedtuple
from pathlib import Path
from unittest.mock import patch

import numpy as np


PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from mt5_connector import MT5Connector, MT5ConnectorError, _expected_market_closure


Account = namedtuple(
    "Account",
    "login server company currency trade_mode balance equity margin margin_free leverage trade_allowed trade_expert",
)
Terminal = namedtuple("Terminal", "connected trade_allowed")
Symbol = namedtuple(
    "Symbol",
    "name visible point digits trade_mode volume_min volume_max volume_step trade_stops_level trade_tick_size trade_tick_value",
)
Tick = namedtuple("Tick", "bid ask time")
Check = namedtuple("Check", "retcode comment balance equity margin margin_free margin_level")
Result = namedtuple("Result", "retcode comment order deal volume price")


class FakeMT5:
    ACCOUNT_TRADE_MODE_DEMO = 0
    ACCOUNT_TRADE_MODE_CONTEST = 1
    SYMBOL_TRADE_MODE_DISABLED = 0
    TIMEFRAME_M15 = 15
    TRADE_ACTION_DEAL = 1
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    ORDER_TIME_GTC = 0
    ORDER_FILLING_RETURN = 2
    ORDER_FILLING_IOC = 1
    ORDER_FILLING_FOK = 0
    TRADE_RETCODE_DONE = 10009
    TRADE_RETCODE_PLACED = 10008
    TRADE_RETCODE_DONE_PARTIAL = 10010
    DEAL_ENTRY_OUT = 1
    DEAL_ENTRY_INOUT = 2
    DEAL_ENTRY_OUT_BY = 3

    def __init__(self, trade_mode=0):
        self.trade_mode = trade_mode
        self.copy_start_pos = None
        self.closed = False

    def initialize(self, **kwargs):
        return True

    def shutdown(self):
        self.closed = True

    def last_error(self):
        return 0, "ok"

    def account_info(self):
        return Account(12345678, "Demo-Server", "Broker", "USD", self.trade_mode, 10000, 10000, 0, 10000, 100, True, True)

    def terminal_info(self):
        return Terminal(True, False)

    def symbol_info(self, symbol):
        if symbol != "EURUSD":
            return None
        return Symbol(symbol, True, 0.00001, 5, 4, 0.01, 100.0, 0.01, 10, 0.00001, 1.0)

    def symbol_info_tick(self, symbol):
        return Tick(1.10000, 1.10002, int(time.time()))

    def symbol_select(self, symbol, selected):
        return True

    def symbols_get(self, pattern):
        return []

    def copy_rates_from_pos(self, symbol, timeframe, start_pos, count):
        self.copy_start_pos = start_pos
        dtype = [
            ("time", "i8"), ("open", "f8"), ("high", "f8"), ("low", "f8"),
            ("close", "f8"), ("tick_volume", "i8"), ("spread", "i8"), ("real_volume", "i8"),
        ]
        base = 1_700_000_000
        return np.array([
            (base + index * 900, 1.1, 1.101, 1.099, 1.1002, 100, 2, 0)
            for index in range(max(50, count))
        ], dtype=dtype)

    def positions_get(self):
        return []

    def history_deals_get(self, date_from, date_to):
        return []

    def order_check(self, request):
        return Check(0, "Done", 10000, 10000, 10, 9990, 1000)

    def order_send(self, request):
        return Result(10009, "Done", 123, 456, request["volume"], request["price"])


class MT5ConnectorTests(unittest.TestCase):
    def test_expected_market_closures_do_not_hide_random_gaps(self):
        # Thursday before Good Friday through Monday open.
        self.assertTrue(_expected_market_closure(1_711_656_000, 1_711_929_600, 273_600, False))
        # A recurring short daily metals maintenance break.
        self.assertTrue(_expected_market_closure(1_779_317_100, 1_779_325_200, 8_100, True))
        # A one-off two-hour hole during a normal session remains unsafe.
        self.assertFalse(_expected_market_closure(1_779_317_100, 1_779_324_300, 7_200, False))

    def setUp(self):
        self.terminal_patch = patch.object(Path, "is_file", return_value=True)
        self.terminal_patch.start()

    def tearDown(self):
        self.terminal_patch.stop()

    def test_connect_masks_account_and_requires_demo(self):
        connector = MT5Connector(module=FakeMT5(), terminal_path="terminal64.exe")
        status = connector.connect()
        self.assertEqual(status["account"]["login_masked"], "****5678")
        self.assertEqual(status["account"]["trade_mode"], "demo")
        self.assertIn(status["execution_mode"], {"signal_only", "demo_confirmed"})
        connector.shutdown()

        real = MT5Connector(module=FakeMT5(trade_mode=2), terminal_path="terminal64.exe")
        with self.assertRaises(MT5ConnectorError):
            real.connect(require_demo=True)

    def test_fetch_uses_only_closed_candles(self):
        module = FakeMT5()
        connector = MT5Connector(module=module, terminal_path="terminal64.exe")
        with connector.session() as (active, _):
            payload = active.fetch_candles("EUR/USD", "15min", 60)
        self.assertEqual(module.copy_start_pos, 1)
        self.assertFalse(payload["incomplete_candle_included"])
        self.assertEqual(len(payload["prices"]), 60)
        self.assertTrue(payload["quality"]["safe_for_signal"])
        self.assertTrue(payload["quality"]["historical_integrity"])
        self.assertTrue(payload["market"]["tick_fresh"])

    def test_stale_tick_blocks_signal_quality(self):
        module = FakeMT5()
        module.symbol_info_tick = lambda symbol: Tick(1.10000, 1.10002, 1_700_000_000)
        connector = MT5Connector(module=module, terminal_path="terminal64.exe")
        with connector.session() as (active, _):
            payload = active.fetch_candles("EUR/USD", "15min", 60)
        self.assertFalse(payload["market"]["tick_fresh"])
        self.assertFalse(payload["market"]["market_open"])
        self.assertFalse(payload["quality"]["safe_for_signal"])
        self.assertTrue(payload["quality"]["historical_integrity"])

    def test_demo_order_is_checked_before_send(self):
        module = FakeMT5()
        connector = MT5Connector(module=module, terminal_path="terminal64.exe")
        with connector.session() as (active, _):
            plan = {"entry": 1.10002, "stop_loss": 1.099, "take_profit": 1.102, "volume": 0.01}
            checked = active.check_demo_order("EUR/USD", "BUY", plan)
            sent = active.send_demo_order("EUR/USD", "BUY", plan)
        self.assertTrue(checked["ok"])
        self.assertEqual(checked["check"]["retcode"], 0)
        self.assertEqual(sent["retcode"], 10009)
        self.assertEqual(sent["order"], 123)


if __name__ == "__main__":
    unittest.main()
