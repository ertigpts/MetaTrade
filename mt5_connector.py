"""Safe MetaTrader 5 access for the local TradeAI application.

The official MetaTrader5 wheel is Windows-only and talks to an installed
terminal.  Importing this module must remain safe on the Linux web deployment,
so the dependency is optional until a connector method is called.
"""

from __future__ import annotations

import importlib
import os
import threading
import time
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


try:  # The production web image is Linux and intentionally has no MT5 wheel.
    import MetaTrader5 as _mt5
except ImportError:  # pragma: no cover - exercised through dependency injection.
    _mt5 = None


def _load_mt5_module():
    """Retry the optional import when a mounted app is loaded before venv paths settle."""
    global _mt5
    if _mt5 is not None:
        return _mt5
    try:
        _mt5 = importlib.import_module("MetaTrader5")
    except ImportError:
        return None
    return _mt5


MT5_LOCK = threading.RLock()

TIMEFRAME_NAMES = {
    "1min": "TIMEFRAME_M1",
    "m1": "TIMEFRAME_M1",
    "5min": "TIMEFRAME_M5",
    "m5": "TIMEFRAME_M5",
    "15min": "TIMEFRAME_M15",
    "m15": "TIMEFRAME_M15",
    "30min": "TIMEFRAME_M30",
    "m30": "TIMEFRAME_M30",
    "1h": "TIMEFRAME_H1",
    "h1": "TIMEFRAME_H1",
    "4h": "TIMEFRAME_H4",
    "h4": "TIMEFRAME_H4",
    "1day": "TIMEFRAME_D1",
    "d1": "TIMEFRAME_D1",
}

TIMEFRAME_SECONDS = {
    "1min": 60,
    "m1": 60,
    "5min": 300,
    "m5": 300,
    "15min": 900,
    "m15": 900,
    "30min": 1800,
    "m30": 1800,
    "1h": 3600,
    "h1": 3600,
    "4h": 14_400,
    "h4": 14_400,
    "1day": 86_400,
    "d1": 86_400,
}


class MT5ConnectorError(RuntimeError):
    """A sanitized operational error safe to return to the local UI."""


def _namedtuple_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if hasattr(value, "_asdict"):
        return dict(value._asdict())
    if isinstance(value, dict):
        return dict(value)
    return {
        name: getattr(value, name)
        for name in dir(value)
        if not name.startswith("_") and not callable(getattr(value, name))
    }


def _masked_login(login: Any) -> str:
    value = str(login or "")
    if not value:
        return ""
    return ("*" * max(0, len(value) - 4)) + value[-4:]


def _expected_market_closure(previous_time: int, current_time: int, seconds: int, recurring: bool) -> bool:
    """Separate scheduled market closures from genuinely missing candle data."""
    previous = datetime.fromtimestamp(previous_time, tz=timezone.utc)
    current = datetime.fromtimestamp(current_time, tz=timezone.utc)
    if current.weekday() == 0 and seconds <= (4 * 86_400):
        return True
    if recurring and seconds <= (4 * 60 * 60):
        return True
    year_end = (
        (previous.month == 12 and previous.day >= 24)
        or (current.month == 12 and current.day >= 24)
        or (previous.month == 1 and previous.day <= 2)
        or (current.month == 1 and current.day <= 2)
    )
    if year_end and seconds <= (4 * 86_400):
        return True
    july_holiday = previous.month == 7 and previous.day in {3, 4}
    return july_holiday and seconds <= 86_400


class MT5Connector:
    """Small synchronized wrapper around the process-global MT5 API."""

    def __init__(self, module=None, terminal_path: str | None = None):
        self.mt5 = module if module is not None else _load_mt5_module()
        self.terminal_path = (
            terminal_path
            or os.getenv("TAHLIL_MT5_TERMINAL_PATH", "").strip()
            or r"C:\Program Files\MetaTrader 5\terminal64.exe"
        )
        self.connected = False

    @property
    def available(self) -> bool:
        return self.mt5 is not None

    def _last_error(self) -> str:
        if not self.available:
            return "MetaTrader5 Python package is not available on this system."
        try:
            code, message = self.mt5.last_error()
            return f"MT5 error {code}: {message}"
        except Exception:
            return "MetaTrader 5 returned an unknown error."

    def connect(self, require_demo: bool = True) -> dict[str, Any]:
        if not self.available:
            raise MT5ConnectorError(
                "اتصال MT5 فقط روی سیستم ویندوزی دارای MetaTrader 5 در دسترس است."
            )

        terminal = Path(self.terminal_path).expanduser()
        if not terminal.is_file():
            raise MT5ConnectorError("فایل terminal64.exe در مسیر تنظیم‌شده پیدا نشد.")

        try:
            timeout = int(os.getenv("TAHLIL_MT5_TIMEOUT_MS", "15000"))
        except ValueError:
            timeout = 15_000
        timeout = min(max(timeout, 1_000), 60_000)

        kwargs: dict[str, Any] = {"path": str(terminal), "timeout": timeout}
        login = os.getenv("TAHLIL_MT5_LOGIN", "").strip()
        password = os.getenv("TAHLIL_MT5_PASSWORD", "")
        server = os.getenv("TAHLIL_MT5_SERVER", "").strip()
        if login:
            try:
                kwargs["login"] = int(login)
            except ValueError as exc:
                raise MT5ConnectorError("شماره حساب MT5 در تنظیمات معتبر نیست.") from exc
        if password:
            kwargs["password"] = password
        if server:
            kwargs["server"] = server

        with MT5_LOCK:
            if not self.mt5.initialize(**kwargs):
                raise MT5ConnectorError(self._last_error())
            self.connected = True
            account = self.mt5.account_info()
            terminal_info = self.mt5.terminal_info()

        if account is None:
            self.shutdown()
            raise MT5ConnectorError("ترمینال باز شد اما حسابی داخل MT5 وارد نشده است.")

        account_data = _namedtuple_dict(account)
        demo_value = getattr(self.mt5, "ACCOUNT_TRADE_MODE_DEMO", 0)
        contest_value = getattr(self.mt5, "ACCOUNT_TRADE_MODE_CONTEST", 1)
        trade_mode_value = account_data.get("trade_mode")
        trade_mode = {
            demo_value: "demo",
            contest_value: "contest",
        }.get(trade_mode_value, "real")
        if require_demo and trade_mode != "demo":
            self.shutdown()
            raise MT5ConnectorError(
                "اتصال رد شد: در این مرحله فقط حساب Demo مجاز است و حساب واقعی قفل است."
            )

        return self._safe_status(account, terminal_info, trade_mode)

    def _safe_status(self, account, terminal_info, trade_mode: str) -> dict[str, Any]:
        account_data = _namedtuple_dict(account)
        terminal_data = _namedtuple_dict(terminal_info)
        return {
            "available": True,
            "connected": bool(terminal_data.get("connected", self.connected)),
            "terminal_trade_allowed": bool(terminal_data.get("trade_allowed", False)),
            "account": {
                "login_masked": _masked_login(account_data.get("login")),
                "server": str(account_data.get("server") or ""),
                "company": str(account_data.get("company") or ""),
                "currency": str(account_data.get("currency") or ""),
                "trade_mode": trade_mode,
                "balance": float(account_data.get("balance") or 0),
                "equity": float(account_data.get("equity") or 0),
                "margin": float(account_data.get("margin") or 0),
                "margin_free": float(account_data.get("margin_free") or 0),
                "leverage": int(account_data.get("leverage") or 0),
                "trade_allowed": bool(account_data.get("trade_allowed", False)),
                "expert_allowed": bool(account_data.get("trade_expert", False)),
            },
            "execution_mode": os.getenv("TAHLIL_TRADING_MODE", "signal_only").strip() or "signal_only",
        }

    def shutdown(self) -> None:
        if not self.available:
            return
        with MT5_LOCK:
            try:
                self.mt5.shutdown()
            finally:
                self.connected = False

    @contextmanager
    def session(self, require_demo: bool = True):
        status = self.connect(require_demo=require_demo)
        try:
            yield self, status
        finally:
            self.shutdown()

    def _resolve_symbol(self, requested: str) -> str:
        symbol = str(requested or "").strip().upper()
        if not symbol:
            raise MT5ConnectorError("نماد الزامی است.")
        candidates = [symbol, symbol.replace("/", ""), symbol.replace(" ", "")]
        with MT5_LOCK:
            for candidate in dict.fromkeys(candidates):
                if self.mt5.symbol_info(candidate) is not None:
                    return candidate
            base = symbol.replace("/", "").replace(" ", "")
            matches = self.mt5.symbols_get(f"*{base}*") or []
        if matches:
            names = sorted(
                (str(item.name) for item in matches if getattr(item, "name", None)),
                key=lambda name: (len(name), name),
            )
            if names:
                return names[0]
        raise MT5ConnectorError(f"نماد {symbol} در کارگزاری فعلی پیدا نشد.")

    def market_snapshot(self, requested_symbol: str) -> dict[str, Any]:
        if not self.connected:
            raise MT5ConnectorError("ابتدا اتصال MT5 را برقرار کنید.")
        symbol = self._resolve_symbol(requested_symbol)
        with MT5_LOCK:
            info = self.mt5.symbol_info(symbol)
            if info is None:
                raise MT5ConnectorError("اطلاعات نماد از MT5 دریافت نشد.")
            if not getattr(info, "visible", False):
                if not self.mt5.symbol_select(symbol, True):
                    raise MT5ConnectorError("افزودن نماد به Market Watch ناموفق بود.")
                info = self.mt5.symbol_info(symbol)
            tick = self.mt5.symbol_info_tick(symbol)
        if tick is None:
            raise MT5ConnectorError("قیمت Bid/Ask نماد دریافت نشد.")

        info_data = _namedtuple_dict(info)
        tick_data = _namedtuple_dict(tick)
        point = float(info_data.get("point") or 0)
        digits = int(info_data.get("digits") or 0)
        pip_size = point * (10 if digits in {3, 5} else 1)
        bid = float(tick_data.get("bid") or 0)
        ask = float(tick_data.get("ask") or 0)
        spread_price = max(0.0, ask - bid)
        spread_points = spread_price / point if point else None
        spread_pips = spread_price / pip_size if pip_size else None
        midpoint = (bid + ask) / 2 if bid > 0 and ask > 0 else 0
        spread_bps = spread_price / midpoint * 10_000 if midpoint else None
        disabled_mode = getattr(self.mt5, "SYMBOL_TRADE_MODE_DISABLED", 0)
        tick_epoch = int(tick_data.get("time") or 0)
        tick_time = datetime.fromtimestamp(tick_epoch, tz=timezone.utc)
        tick_age_seconds = max(0, int((datetime.now(timezone.utc) - tick_time).total_seconds()))
        try:
            maximum_tick_age = int(os.getenv("TAHLIL_MT5_MAX_TICK_AGE_SECONDS", "300"))
        except ValueError:
            maximum_tick_age = 300
        maximum_tick_age = min(max(maximum_tick_age, 30), 3600)
        tick_fresh = tick_epoch > 0 and tick_age_seconds <= maximum_tick_age
        market_open = (
            bid > 0
            and ask > 0
            and ask >= bid
            and tick_fresh
            and int(info_data.get("trade_mode") or 0) != disabled_mode
        )
        return {
            "requested_symbol": requested_symbol,
            "symbol": symbol,
            "bid": bid,
            "ask": ask,
            "spread_points": round(spread_points, 2) if spread_points is not None else None,
            "spread_pips": round(spread_pips, 3) if spread_pips is not None else None,
            "spread_bps": round(spread_bps, 4) if spread_bps is not None else None,
            "point": point,
            "pip_size": pip_size,
            "digits": digits,
            "trade_mode": int(info_data.get("trade_mode") or 0),
            "tradeable": int(info_data.get("trade_mode") or 0) != disabled_mode,
            "market_open": market_open,
            "tick_fresh": tick_fresh,
            "tick_age_seconds": tick_age_seconds,
            "maximum_tick_age_seconds": maximum_tick_age,
            "volume_min": float(info_data.get("volume_min") or 0),
            "volume_max": float(info_data.get("volume_max") or 0),
            "volume_step": float(info_data.get("volume_step") or 0),
            "trade_stops_level": int(info_data.get("trade_stops_level") or 0),
            "trade_tick_size": float(info_data.get("trade_tick_size") or 0),
            "trade_tick_value": float(info_data.get("trade_tick_value") or 0),
            "time_utc": tick_time.isoformat(),
            # Some MT5 servers encode their wall-clock offset in the epoch-like
            # tick value. Expose the raw value so candle boundaries can follow
            # the terminal server rather than the browser clock.
            "time_epoch": tick_epoch,
        }

    def portfolio_snapshot(self, days: int = 7) -> dict[str, Any]:
        """Return a sanitized account-wide risk snapshot for live safety gates."""
        if not self.connected:
            raise MT5ConnectorError("ابتدا اتصال MT5 را برقرار کنید.")
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=min(max(int(days), 1), 30))
        with MT5_LOCK:
            positions = self.mt5.positions_get()
            deals = self.mt5.history_deals_get(start, now)
        if positions is None:
            raise MT5ConnectorError(self._last_error())
        if deals is None:
            deals = []

        safe_positions = []
        open_position_count_by_symbol: dict[str, int] = {}
        aggregate_open_risk = 0.0
        unprotected_position_count = 0
        for raw in positions:
            item = _namedtuple_dict(raw)
            symbol = str(item.get("symbol") or "")
            normalized_symbol = symbol.upper().replace("/", "").replace(" ", "")
            if normalized_symbol:
                open_position_count_by_symbol[normalized_symbol] = open_position_count_by_symbol.get(normalized_symbol, 0) + 1
            open_price = float(item.get("price_open") or 0)
            stop_loss = float(item.get("sl") or 0)
            volume = float(item.get("volume") or 0)
            risk_amount = None
            if symbol and open_price > 0 and stop_loss > 0 and volume > 0:
                with MT5_LOCK:
                    symbol_info = self.mt5.symbol_info(symbol)
                info = _namedtuple_dict(symbol_info)
                tick_size = float(info.get("trade_tick_size") or 0)
                tick_value = float(info.get("trade_tick_value") or 0)
                if tick_size > 0 and tick_value > 0:
                    risk_amount = abs(open_price - stop_loss) / tick_size * tick_value * volume
                    aggregate_open_risk += risk_amount
            if risk_amount is None:
                unprotected_position_count += 1
            safe_positions.append({
                "ticket": int(item.get("ticket") or 0),
                "symbol": symbol,
                "type": int(item.get("type") or 0),
                "volume": volume,
                "price_open": open_price,
                "sl": stop_loss,
                "tp": float(item.get("tp") or 0),
                "profit": float(item.get("profit") or 0),
                "magic": int(item.get("magic") or 0),
                "initial_risk_amount": round(risk_amount, 2) if risk_amount is not None else None,
            })

        exit_values = {
            getattr(self.mt5, "DEAL_ENTRY_OUT", 1),
            getattr(self.mt5, "DEAL_ENTRY_OUT_BY", 3),
            getattr(self.mt5, "DEAL_ENTRY_INOUT", 2),
        }
        entry_values = {getattr(self.mt5, "DEAL_ENTRY_IN", 0)}
        trade_deal_types = {
            getattr(self.mt5, "DEAL_TYPE_BUY", 0),
            getattr(self.mt5, "DEAL_TYPE_SELL", 1),
        }
        closed = []
        daily_net = 0.0
        daily_position_ids = set()
        daily_position_symbols: dict[int, str] = {}
        for raw in deals:
            item = _namedtuple_dict(raw)
            timestamp = int(item.get("time") or 0)
            net = sum(float(item.get(field) or 0) for field in ("profit", "commission", "swap", "fee"))
            if (
                item.get("type") in trade_deal_types
                and timestamp
                and datetime.fromtimestamp(timestamp, tz=timezone.utc).date() == now.date()
            ):
                daily_net += net
                if item.get("entry") in entry_values:
                    position_id = int(item.get("position_id") or item.get("order") or item.get("ticket") or 0)
                    daily_position_ids.add(position_id)
                    daily_position_symbols[position_id] = str(item.get("symbol") or "").upper().replace("/", "").replace(" ", "")
            if item.get("entry") in exit_values:
                closed.append((timestamp, net))
        closed.sort(key=lambda value: value[0], reverse=True)
        consecutive_losses = 0
        for _, net in closed:
            if net < 0:
                consecutive_losses += 1
            elif net > 0:
                break
        latest_loss_timestamp = closed[0][0] if closed and closed[0][1] < 0 else 0
        daily_trade_count_by_symbol: dict[str, int] = {}
        for position_id in daily_position_ids:
            daily_symbol = daily_position_symbols.get(position_id, "")
            if daily_symbol:
                daily_trade_count_by_symbol[daily_symbol] = daily_trade_count_by_symbol.get(daily_symbol, 0) + 1

        return {
            "open_position_count": len(safe_positions),
            "positions": safe_positions,
            "open_position_count_by_symbol": open_position_count_by_symbol,
            "aggregate_open_risk": round(aggregate_open_risk, 2),
            "unprotected_position_count": unprotected_position_count,
            "daily_realized_net": round(daily_net, 2),
            "daily_trade_count": len({value for value in daily_position_ids if value}),
            "daily_trade_count_by_symbol": daily_trade_count_by_symbol,
            "consecutive_losses": consecutive_losses,
            "latest_loss_time_utc": (
                datetime.fromtimestamp(latest_loss_timestamp, tz=timezone.utc).isoformat()
                if latest_loss_timestamp else None
            ),
            "as_of": now.isoformat(),
        }

    def closed_trade_outcomes(self, days: int = 30, magic: int = 260809) -> list[dict[str, Any]]:
        """Return exact closed outcomes for this application's broker magic id."""
        if not self.connected:
            raise MT5ConnectorError("ابتدا اتصال MT5 را برقرار کنید.")
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=min(max(int(days), 1), 90))
        with MT5_LOCK:
            deals = self.mt5.history_deals_get(start, now)
        if deals is None:
            raise MT5ConnectorError(self._last_error())
        entry_in = getattr(self.mt5, "DEAL_ENTRY_IN", 0)
        exits = {
            getattr(self.mt5, "DEAL_ENTRY_OUT", 1),
            getattr(self.mt5, "DEAL_ENTRY_INOUT", 2),
            getattr(self.mt5, "DEAL_ENTRY_OUT_BY", 3),
        }
        grouped: dict[int, list[dict[str, Any]]] = {}
        for raw in deals:
            item = _namedtuple_dict(raw)
            if int(item.get("magic") or 0) != int(magic):
                continue
            position_id = int(item.get("position_id") or 0)
            if position_id:
                grouped.setdefault(position_id, []).append(item)

        outcomes = []
        for position_id, items in grouped.items():
            items.sort(key=lambda item: (int(item.get("time") or 0), int(item.get("ticket") or 0)))
            entries = [item for item in items if item.get("entry") == entry_in]
            closing = [item for item in items if item.get("entry") in exits]
            if not entries or not closing:
                continue
            realized_net = sum(
                sum(float(item.get(field) or 0) for field in ("profit", "commission", "swap", "fee"))
                for item in items
            )
            last_exit = closing[-1]
            outcomes.append({
                "position_id": position_id,
                "symbol": str(entries[0].get("symbol") or last_exit.get("symbol") or ""),
                "entry_deal_tickets": [int(item.get("ticket") or 0) for item in entries],
                "entry_order_tickets": [int(item.get("order") or 0) for item in entries],
                "exit_price": float(last_exit.get("price") or 0),
                "exit_time_utc": datetime.fromtimestamp(
                    int(last_exit.get("time") or 0), tz=timezone.utc
                ).isoformat(),
                "realized_net": round(realized_net, 2),
            })
        return sorted(outcomes, key=lambda item: item["exit_time_utc"], reverse=True)

    def _checked_market_request(
        self,
        requested_symbol: str,
        direction: str,
        plan: dict[str, Any],
        *,
        deviation_points: int = 30,
        magic: int = 260809,
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        """Build and broker-check a demo market request without sending it."""
        if direction not in {"BUY", "SELL"}:
            raise MT5ConnectorError("جهت سفارش معتبر نیست.")
        market = self.market_snapshot(requested_symbol)
        if not market["market_open"]:
            raise MT5ConnectorError("بازار بسته است یا قیمت لحظه‌ای تازه نیست؛ سفارش رد شد.")

        current_price = float(market["ask"] if direction == "BUY" else market["bid"])
        preview_price = float(plan.get("entry") or 0)
        midpoint = max((float(market["bid"]) + float(market["ask"])) / 2, 1e-9)
        drift_bps = abs(current_price - preview_price) / midpoint * 10_000
        try:
            maximum_drift_bps = float(os.getenv("TAHLIL_MT5_MAX_ENTRY_DRIFT_BPS", "5.0"))
        except ValueError:
            maximum_drift_bps = 5.0
        maximum_drift_bps = min(max(maximum_drift_bps, 0.1), 20.0)
        if preview_price <= 0 or drift_bps > maximum_drift_bps:
            raise MT5ConnectorError("قیمت از زمان پیش‌نمایش تغییر کرده است؛ دوباره تحلیل بگیرید.")

        volume = float(plan.get("volume") or 0)
        stop_loss = float(plan.get("stop_loss") or 0)
        take_profit = float(plan.get("take_profit") or 0)
        if min(volume, stop_loss, take_profit) <= 0:
            raise MT5ConnectorError("پلن حجم یا حدهای سفارش ناقص است.")
        if direction == "BUY" and not (stop_loss < current_price < take_profit):
            raise MT5ConnectorError("حد ضرر یا حد سود BUY با قیمت فعلی معتبر نیست.")
        if direction == "SELL" and not (take_profit < current_price < stop_loss):
            raise MT5ConnectorError("حد ضرر یا حد سود SELL با قیمت فعلی معتبر نیست.")

        base_request = {
            "action": getattr(self.mt5, "TRADE_ACTION_DEAL"),
            "symbol": market["symbol"],
            "volume": volume,
            "type": getattr(self.mt5, "ORDER_TYPE_BUY" if direction == "BUY" else "ORDER_TYPE_SELL"),
            "price": current_price,
            "sl": stop_loss,
            "tp": take_profit,
            "deviation": min(max(int(deviation_points), 1), 200),
            "magic": int(magic),
            "comment": "TradeAI demo",
            "type_time": getattr(self.mt5, "ORDER_TIME_GTC"),
        }
        filling_candidates = [
            getattr(self.mt5, "ORDER_FILLING_RETURN", None),
            getattr(self.mt5, "ORDER_FILLING_IOC", None),
            getattr(self.mt5, "ORDER_FILLING_FOK", None),
        ]
        last_check = None
        for filling in dict.fromkeys(value for value in filling_candidates if value is not None):
            request_payload = {**base_request, "type_filling": filling}
            with MT5_LOCK:
                check = self.mt5.order_check(request_payload)
            if check is None:
                continue
            check_data = _namedtuple_dict(check)
            last_check = check_data
            if int(check_data.get("retcode", -1)) == 0:
                return request_payload, check_data, market
        comment = str((last_check or {}).get("comment") or self._last_error())
        raise MT5ConnectorError(f"بررسی کارگزاری سفارش را رد کرد: {comment[:180]}")

    def check_demo_order(self, requested_symbol: str, direction: str, plan: dict[str, Any]) -> dict[str, Any]:
        request_payload, check, market = self._checked_market_request(requested_symbol, direction, plan)
        return {
            "ok": True,
            "check": {key: check.get(key) for key in ("retcode", "comment", "balance", "equity", "margin", "margin_free", "margin_level")},
            "request": {key: request_payload.get(key) for key in ("symbol", "volume", "price", "sl", "tp", "deviation", "magic")},
            "market": market,
        }

    def send_demo_order(self, requested_symbol: str, direction: str, plan: dict[str, Any]) -> dict[str, Any]:
        """Send one checked order. Caller must enforce demo account and explicit confirmation."""
        request_payload, check, market = self._checked_market_request(requested_symbol, direction, plan)
        accepted = {
            getattr(self.mt5, "TRADE_RETCODE_PLACED", 10008),
            getattr(self.mt5, "TRADE_RETCODE_DONE", 10009),
            getattr(self.mt5, "TRADE_RETCODE_DONE_PARTIAL", 10010),
        }
        result_data = {}
        retcode = 0
        for attempt in range(2):
            with MT5_LOCK:
                result = self.mt5.order_send(request_payload)
            if result is None:
                raise MT5ConnectorError(self._last_error())
            result_data = _namedtuple_dict(result)
            retcode = int(result_data.get("retcode") or 0)
            if retcode in accepted:
                break
            # 10031 explicitly means the server did not receive/execute the
            # request because the terminal had no network connection. One
            # fresh check+retry is safe and avoids duplicate execution.
            if retcode == 10031 and attempt == 0:
                time.sleep(0.75)
                request_payload, check, market = self._checked_market_request(
                    requested_symbol, direction, plan
                )
                continue
            break
        if retcode not in accepted:
            raise MT5ConnectorError(
                f"سرور معامله سفارش را نپذیرفت ({retcode}): {str(result_data.get('comment') or '')[:180]}"
            )
        return {
            "ok": True,
            "retcode": retcode,
            "comment": str(result_data.get("comment") or "")[:180],
            "order": int(result_data.get("order") or 0),
            "deal": int(result_data.get("deal") or 0),
            "volume": float(result_data.get("volume") or plan.get("volume") or 0),
            "price": float(result_data.get("price") or market.get("ask") or 0),
            "broker_check": {key: check.get(key) for key in ("retcode", "comment", "margin", "margin_free")},
        }

    def fetch_candles(
        self,
        requested_symbol: str,
        interval: str,
        count: int = 300,
        include_incomplete: bool = False,
    ) -> dict[str, Any]:
        if not self.connected:
            raise MT5ConnectorError("ابتدا اتصال MT5 را برقرار کنید.")
        normalized_interval = str(interval or "").strip().lower()
        timeframe_name = TIMEFRAME_NAMES.get(normalized_interval)
        if not timeframe_name:
            raise MT5ConnectorError("تایم‌فریم MT5 پشتیبانی نمی‌شود.")
        # Execution endpoints impose their own smaller limits. Research needs a
        # longer closed-candle history, especially on M15, to span multiple
        # regimes instead of judging a strategy on only a few recent months.
        count = min(max(int(count), 50), 20_000)
        symbol = self._resolve_symbol(requested_symbol)
        timeframe = getattr(self.mt5, timeframe_name)
        start_pos = 0 if include_incomplete else 1
        with MT5_LOCK:
            rates = self.mt5.copy_rates_from_pos(symbol, timeframe, start_pos, count)
        if rates is None:
            raise MT5ConnectorError(self._last_error())

        unique: dict[int, dict[str, Any]] = {}
        invalid_rows = 0
        for raw in rates:
            row = dict(zip(rates.dtype.names, raw)) if hasattr(rates, "dtype") else _namedtuple_dict(raw)
            try:
                timestamp = int(row["time"])
                open_price = float(row["open"])
                high = float(row["high"])
                low = float(row["low"])
                close = float(row["close"])
                if min(open_price, high, low, close) <= 0 or high < max(open_price, close) or low > min(open_price, close):
                    raise ValueError
            except (KeyError, TypeError, ValueError):
                invalid_rows += 1
                continue
            unique[timestamp] = {
                "time": timestamp,
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "tick_volume": int(row.get("tick_volume") or 0),
                "spread": int(row.get("spread") or 0),
                "real_volume": int(row.get("real_volume") or 0),
            }

        rows = [unique[key] for key in sorted(unique)]
        if len(rows) < 50:
            raise MT5ConnectorError("MT5 تعداد کافی کندل معتبر برنگرداند.")

        expected_seconds = TIMEFRAME_SECONDS[normalized_interval]
        gap_candidates = []
        for previous, current in zip(rows, rows[1:]):
            difference = current["time"] - previous["time"]
            if difference > expected_seconds * 1.5:
                gap_candidates.append(
                    {"after": previous["time"], "before": current["time"], "seconds": difference}
                )

        duration_counts = Counter(item["seconds"] for item in gap_candidates)
        gaps = []
        expected_closures = []
        for item in gap_candidates:
            expected = _expected_market_closure(
                item["after"],
                item["before"],
                item["seconds"],
                recurring=duration_counts[item["seconds"]] >= 3,
            )
            target = expected_closures if expected else gaps
            target.append({"after": item["after"], "seconds": item["seconds"]})

        market = self.market_snapshot(symbol)
        labels = [datetime.fromtimestamp(row["time"], tz=timezone.utc).isoformat() for row in rows]
        return {
            "symbol": symbol,
            "interval": normalized_interval,
            "prices": [row["close"] for row in rows],
            "opens": [row["open"] for row in rows],
            "highs": [row["high"] for row in rows],
            "lows": [row["low"] for row in rows],
            "labels": labels,
            "candles": [{**row, "time_utc": label} for row, label in zip(rows, labels)],
            "provider": "MetaTrader 5",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "incomplete_candle_included": bool(include_incomplete),
            "quality": {
                "requested": count,
                "valid": len(rows),
                "duplicates_removed": max(0, len(rates) - invalid_rows - len(rows)),
                "invalid_removed": invalid_rows,
                "gap_count": len(gaps),
                "gaps": gaps[:10],
                "expected_closure_count": len(expected_closures),
                "historical_integrity": invalid_rows == 0 and not gaps,
                "safe_for_signal": invalid_rows == 0 and not gaps and bool(market.get("market_open")),
            },
            "market": market,
        }
