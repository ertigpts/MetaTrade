import json
import os
import hashlib
import secrets
import threading
import time
from collections import defaultdict, deque
from functools import wraps
from hmac import compare_digest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import requests
from dotenv import load_dotenv
from flask import Flask, abort, jsonify, redirect, render_template, request, session, url_for
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from technical_indicators import calculate_macd, calculate_rsi
from analytics_engine import (
    calculate_atr,
    close_volatility,
    multi_timeframe_alignment,
    run_backtest,
    run_ohlc_backtest,
)
from mt5_connector import MT5Connector, MT5ConnectorError
from trading_engine import SignalSettings, TradingRuleError, build_risk_plan, generate_signal
from storage import (
    add_journal_entry,
    finalize_order_execution,
    init_database,
    list_analyses,
    list_journal,
    list_order_executions,
    reserve_order_execution,
    save_analysis,
    save_signal_event,
    signal_exists,
)

APP_ROOT = os.path.dirname(os.path.abspath(__file__))


def _repo_env_path():
    for parent in (Path(__file__).resolve().parent, *Path(__file__).resolve().parents):
        candidate = parent / ".env"
        if candidate.exists():
            return candidate
    return Path(APP_ROOT) / ".env"


load_dotenv(_repo_env_path(), override=False)

app = Flask(__name__)
init_database()


IS_PRODUCTION = os.getenv("APP_ENV", "").lower() == "production" or os.getenv("FLASK_ENV", "").lower() == "production"
FLASK_SECRET_KEY = os.getenv("TAHLIL_SECRET_KEY") or os.getenv("FLASK_SECRET_KEY", "")
if IS_PRODUCTION and not FLASK_SECRET_KEY:
    raise RuntimeError("FLASK_SECRET_KEY must be set in production.")

app.secret_key = FLASK_SECRET_KEY or "tradeai-dev-secret-key"
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=IS_PRODUCTION,
    PERMANENT_SESSION_LIFETIME=60 * 60 * 24 * 14,
    MAX_CONTENT_LENGTH=512 * 1024,
)

_RATE_BUCKETS = defaultdict(deque)
_RATE_LOCK = threading.Lock()


def rate_limit(max_requests, window_seconds):
    """Process-local abuse protection; the reverse proxy can enforce a second layer."""
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            key = f"{view.__name__}:{_client_ip()}"
            now = time.monotonic()
            with _RATE_LOCK:
                bucket = _RATE_BUCKETS[key]
                while bucket and now - bucket[0] > window_seconds:
                    bucket.popleft()
                if len(bucket) >= max_requests:
                    retry_after = max(1, int(window_seconds - (now - bucket[0])))
                    response = jsonify({"error": "Too many requests. Please try again shortly."})
                    response.headers["Retry-After"] = str(retry_after)
                    return response, 429
                bucket.append(now)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def _csrf_token():
    if not session.get("csrf_token"):
        session["csrf_token"] = secrets.token_urlsafe(24)
    return session["csrf_token"]


def _require_csrf():
    provided = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token")
    if not provided or not compare_digest(str(provided), str(session.get("csrf_token", ""))):
        abort(403)


def _owner_id():
    if session.get("logged_in") and session.get("username"):
        return f"user:{session['username']}"
    if not session.get("visitor_id"):
        session["visitor_id"] = secrets.token_urlsafe(18)
    return f"guest:{session['visitor_id']}"


@app.after_request
def _security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    if IS_PRODUCTION:
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response

DEFAULT_OPENAI_MODEL = os.getenv("TAHLIL_AI_MODEL") or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = os.getenv("TAHLIL_AI_BASE_URL") or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
TWELVEDATA_URL = "https://api.twelvedata.com/time_series"
YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
BUSINESSQUANT_CALENDAR_URL = "https://data.businessquant.com/calendar/economic"

# مهم‌ترین انتشارهای کلان آمریکا برای دلار و طلا. این API زمان دقیق یا پیش‌بینی
# اجماع را برنمی‌گرداند، بنابراین داده‌ها فقط برای هشدار ریسک روز انتشار هستند.
MAJOR_US_MACRO_CODES = {
    "E:USCPI.YOY",
    "E:USCPICORE.YOY",
    "E:USCPI.MOM",
    "E:USPPI.YOY",
    "E:USPAYROLL.MOM",
    "E:USUNEMP",
    "E:USCLAIMS",
    "E:USRETAIL.MOM",
    "E:USGDP.QOQ",
    "E:USPCEPI.YOY",
    "E:USPCEPICORE.YOY",
    "E:USFFR",
}
_MACRO_CACHE = {"expires_at": 0.0, "value": None}
_MACRO_CACHE_LOCK = threading.Lock()

LOGIN_ENV_KEYS = [
    ("TAHLIL_APP_USERNAME", "TAHLIL_APP_PASSWORD"),
    ("TAHLIL_APP_USERNAME_2", "TAHLIL_APP_PASSWORD_2"),
    ("TAHLIL_APP_USERNAME_3", "TAHLIL_APP_PASSWORD_3"),
    ("TAHLIL_APP_USERNAME_4", "TAHLIL_APP_PASSWORD_4"),
    ("APP_USERNAME", "APP_PASSWORD"),
    ("APP_USERNAME_2", "APP_PASSWORD_2"),
    ("APP_USERNAME_3", "APP_PASSWORD_3"),
    ("APP_USERNAME_4", "APP_PASSWORD_4"),
]
CONFIGURED_USERS = [
    (os.getenv(username_key, "").strip(), os.getenv(password_key, ""))
    for username_key, password_key in LOGIN_ENV_KEYS
]

if IS_PRODUCTION and not any(username and password for username, password in CONFIGURED_USERS):
    raise RuntimeError("At least one APP_USERNAME/APP_PASSWORD pair must be set in production.")


def _valid_login(username, password):
    for configured_username, configured_password in CONFIGURED_USERS:
        if not configured_username or not configured_password:
            continue
        if compare_digest(username, configured_username) and compare_digest(password, configured_password):
            return True
    return False


# تعداد تحلیلِ رایگانِ مهمان (بدون ورود). نسخه محلی شمارش را فقط در session
# همین برنامه نگه می‌دارد و به سرویس یا دیتابیس خارجی وابسته نیست.
GUEST_FREE_ANALYSES = int(os.getenv("TAHLIL_GUEST_FREE_ANALYSES", "2"))


def _client_ip():
    """Read proxy headers only when the deployment explicitly trusts its proxy."""
    trust_proxy = os.getenv("TAHLIL_TRUST_PROXY", "").lower() in {"1", "true", "yes"}
    forwarded = request.headers.get("X-Forwarded-For", "") or request.headers.get("X-Real-IP", "")
    if trust_proxy and forwarded:
        candidate = forwarded.split(",")[0].strip()
        if candidate:
            return candidate[:64]
    return request.remote_addr or "unknown"


def _guest_analyses_used():
    return int(session.get("guest_analyses", 0) or 0)


def _analysis_quota_exceeded():
    """برای کاربرِ واردنشده، اگر سهمیه‌ی تحلیل رایگان (بر پایه‌ی IP) تمام شده باشد True می‌دهد."""
    if session.get("logged_in"):
        return False
    return _guest_analyses_used() >= GUEST_FREE_ANALYSES


def _register_guest_analysis():
    """یک تحلیل موفق مهمان را فقط در session محلی ثبت می‌کند."""
    if session.get("logged_in"):
        return
    session["guest_analyses"] = int(session.get("guest_analyses", 0) or 0) + 1


def _login_required_response():
    return jsonify({
        "error": "تحلیل‌های رایگان شما تمام شد. برای ادامه می‌توانید همین‌جا در چت سفارش دهید تا تیم ما درباره‌ی دسترسی و قیمت با شما تماس بگیرد؛ یا اگر اشتراک دارید وارد شوید.",
        "quota_exhausted": True,
        "open_chat": True,
        "login_url": url_for("login"),
        "remaining": 0,
    }), 402


def _resolve_openai_url():
    endpoint = (os.getenv("TAHLIL_AI_ENDPOINT") or os.getenv("OPENAI_ENDPOINT") or "").strip()
    if endpoint:
        return endpoint
    base = (
        os.getenv("TAHLIL_AI_BASE_URL")
        or os.getenv("OPENAI_BASE_URL")
        or OPENAI_BASE_URL
        or "https://api.openai.com/v1"
    ).strip().rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    return f"{base}/chat/completions"


def _build_retry_session():
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=0.8,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session_client = requests.Session()
    session_client.mount("https://", adapter)
    session_client.mount("http://", adapter)
    session_client.headers.update(
        {
            "Accept": "application/json",
            "User-Agent": "TradeAI/1.0 (+https://liara.ir)",
        }
    )
    return session_client


def _fetch_twelvedata_time_series(symbol, interval, outputsize, api_key):
    with _build_retry_session() as session_client:
        response = session_client.get(
            TWELVEDATA_URL,
            params={
                "symbol": symbol,
                "interval": interval,
                "outputsize": outputsize,
                "apikey": api_key,
            },
            timeout=(8, 30),
        )
        response.raise_for_status()
        return response.json()


def _fetch_businessquant_calendar(api_key, start_date=None, horizon_days=7):
    """Fetch and normalize the date-level US macro context used by AI analysis."""
    start_date = start_date or datetime.now(timezone.utc).date()
    if isinstance(start_date, datetime):
        start_date = start_date.date()
    if not isinstance(start_date, date):
        raise ValueError("start_date must be a date.")
    horizon_days = max(1, min(int(horizon_days), 14))
    end_date = start_date + timedelta(days=horizon_days)

    with _build_retry_session() as session_client:
        response = session_client.get(
            BUSINESSQUANT_CALENDAR_URL,
            params={
                "from_date": start_date.isoformat(),
                "till_date": end_date.isoformat(),
                "api_key": api_key,
            },
            timeout=(5, 15),
        )
        response.raise_for_status()
        payload = response.json()

    rows = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise ValueError("BusinessQuant returned an invalid calendar response.")

    events = []
    for row in rows:
        if not isinstance(row, dict) or str(row.get("code") or "").upper() not in MAJOR_US_MACRO_CODES:
            continue
        release_date = str(row.get("next_release") or "").strip()
        try:
            days_until = (date.fromisoformat(release_date) - start_date).days
        except ValueError:
            continue
        if days_until < 0 or days_until > horizon_days:
            continue
        events.append(
            {
                "code": str(row.get("code") or "")[:40],
                "name": str(row.get("name") or "Economic release")[:120],
                "category": str(row.get("category") or "")[:60],
                "release_date": release_date,
                "days_until": days_until,
                "latest_value": row.get("latest_value"),
                "prior_value": row.get("prior_value"),
            }
        )

    events.sort(key=lambda item: (item["release_date"], item["name"]))
    high_risk_dates = sorted({item["release_date"] for item in events})
    return {
        "available": True,
        "source": "BusinessQuant",
        "coverage": "United States economic releases",
        "as_of": datetime.now(timezone.utc).isoformat(),
        "horizon_days": horizon_days,
        "event_count": len(events),
        "high_risk_dates": high_risk_dates,
        "events": events[:12],
        "precision": "date_only",
        "limitations": (
            "Release dates only; exact time, impact rating, consensus forecast, and breaking-news headlines are unavailable."
        ),
    }


def _get_macro_context():
    """Return cached macro context; a provider outage must never break technical analysis."""
    api_key = (
        os.getenv("TAHLIL_BUSINESSQUANT_API_KEY")
        or os.getenv("BUSINESSQUANT_API_KEY")
        or ""
    ).strip()
    if not api_key:
        return {
            "available": False,
            "source": "BusinessQuant",
            "event_count": 0,
            "events": [],
            "reason": "not_configured",
        }

    now = time.monotonic()
    with _MACRO_CACHE_LOCK:
        cached = _MACRO_CACHE.get("value")
        if cached is not None and now < float(_MACRO_CACHE.get("expires_at") or 0):
            return cached

    try:
        context = _fetch_businessquant_calendar(api_key)
        ttl = 15 * 60
    except (requests.RequestException, ValueError, TypeError):
        context = {
            "available": False,
            "source": "BusinessQuant",
            "event_count": 0,
            "events": [],
            "reason": "provider_unavailable",
        }
        ttl = 60

    with _MACRO_CACHE_LOCK:
        _MACRO_CACHE["value"] = context
        _MACRO_CACHE["expires_at"] = time.monotonic() + ttl
    return context


def _demo_execution_enabled():
    return (
        os.getenv("TAHLIL_TRADING_MODE", "signal_only").strip().lower() == "demo_confirmed"
        and os.getenv("TAHLIL_MT5_ALLOW_DEMO_ORDERS", "0").strip().lower() in {"1", "true", "yes", "on"}
    )


def _macro_trade_gate(context, holding_hours=48):
    """Conservative date-level news gate; unknown calendar state fails closed."""
    if not isinstance(context, dict) or not context.get("available"):
        return {
            "clear": False,
            "reason": "تقویم اقتصادی در دسترس نیست؛ معامله دمو تا بازیابی خبر متوقف است.",
            "precision": "unavailable",
        }
    today = datetime.now(timezone.utc).date()
    days = max(1, int(np.ceil(max(float(holding_hours), 1.0) / 24.0)))
    protected_dates = {(today + timedelta(days=offset)).isoformat() for offset in range(days + 1)}
    collisions = [
        event for event in context.get("events") or []
        if str(event.get("release_date") or "") in protected_dates
    ]
    if collisions:
        names = "، ".join(str(item.get("name") or item.get("code") or "خبر مهم") for item in collisions[:3])
        return {
            "clear": False,
            "reason": f"در بازه نگهداری خبر کلان مهم وجود دارد: {names}",
            "precision": context.get("precision", "date_only"),
            "events": collisions[:6],
        }
    return {
        "clear": True,
        "reason": "در بازه نگهداری، رویداد کلان ثبت‌شده‌ای دیده نشد.",
        "precision": context.get("precision", "date_only"),
        "events": [],
    }


def _true_timeframe_confirmation(summaries, candidate):
    """Score real H1/H4/D1 summaries; this is not the old same-series slope proxy."""
    candidate = str(candidate or "").upper()
    weights = {"H1": 25, "H4": 45, "D1": 30}
    scores = {}
    confirmations = 0
    contradictions = 0
    total = 0.0
    for name, weight in weights.items():
        summary = summaries.get(name) or {}
        action = str(summary.get("action_bias") or "").lower()
        macd = str(summary.get("macd_bias") or "").lower()
        buy_score = float(summary.get("buy_score") or 0)
        sell_score = float(summary.get("sell_score") or 0)
        directional_gap = buy_score - sell_score
        if candidate == "BUY":
            agrees = "buy" in action or (macd == "bullish" and directional_gap > 0)
            conflicts = "sell" in action or (macd == "bearish" and directional_gap < -5)
        else:
            agrees = "sell" in action or (macd == "bearish" and directional_gap < 0)
            conflicts = "buy" in action or (macd == "bullish" and directional_gap > 5)
        local = 100 if agrees else (0 if conflicts else 50)
        confirmations += int(agrees)
        contradictions += int(conflicts)
        total += local * weight / 100
        scores[name] = {
            "score": local,
            "action_bias": summary.get("action_bias"),
            "macd_bias": summary.get("macd_bias"),
            "rsi": summary.get("latest_rsi"),
        }
    aligned = candidate in {"BUY", "SELL"} and confirmations >= 2 and contradictions == 0 and scores.get("H4", {}).get("score") == 100
    return {
        "aligned": aligned,
        "score": int(round(total)),
        "candidate": candidate,
        "confirmations": confirmations,
        "contradictions": contradictions,
        "timeframes": scores,
        "source": "real_mt5_H1_H4_D1",
    }


def _validate_trade_ai_assessment(value, candidate):
    if not isinstance(value, dict):
        raise ValueError("AI trade assessment must be an object.")
    decision = str(value.get("decision") or "").strip().lower()
    direction = str(value.get("direction") or "").strip().upper()
    if decision not in {"approve", "veto", "uncertain"}:
        raise ValueError("AI decision is invalid.")
    if direction not in {"BUY", "SELL", "HOLD"}:
        raise ValueError("AI direction is invalid.")
    try:
        confidence = int(_clamp(int(value.get("confidence")), 0, 100))
        risk_multiplier = float(_clamp(float(value.get("risk_multiplier")), 0.25, 1.0))
    except (TypeError, ValueError) as exc:
        raise ValueError("AI numeric fields are invalid.") from exc
    if decision == "approve" and direction != candidate:
        decision = "veto"
    reasons = value.get("reasons") or []
    invalidators = value.get("invalidators") or []
    if not isinstance(reasons, list) or not isinstance(invalidators, list):
        raise ValueError("AI reason fields must be arrays.")
    return {
        "decision": decision,
        "direction": direction,
        "confidence": confidence,
        "risk_multiplier": risk_multiplier,
        "regime": str(value.get("regime") or "uncertain")[:40],
        "news_risk": str(value.get("news_risk") or "unknown")[:20],
        "reasons": [str(item)[:300] for item in reasons[:4]],
        "invalidators": [str(item)[:300] for item in invalidators[:4]],
        "model": DEFAULT_OPENAI_MODEL,
    }


def _call_trade_ai_assessment(snapshot, candidate):
    """AI is a bounded second opinion: it can veto/reduce risk, never bypass hard gates."""
    api_key, model, endpoint = _ai_config_chat()
    if not api_key:
        return {
            "decision": "uncertain", "direction": "HOLD", "confidence": 0,
            "risk_multiplier": 0.25, "regime": "unavailable", "news_risk": "unknown",
            "reasons": ["کلید AI تنظیم نشده است."], "invalidators": [], "model": model,
        }
    schema = {
        "decision": "approve|veto|uncertain",
        "direction": "BUY|SELL|HOLD",
        "confidence": "integer 0..100",
        "risk_multiplier": "number 0.25..1.0; only reduce risk",
        "regime": "trend|range|volatile|uncertain",
        "news_risk": "low|medium|high|unknown",
        "reasons": ["string"],
        "invalidators": ["string"],
    }
    messages = [
        {
            "role": "system",
            "content": (
                "You are the conservative AI risk gate for a DEMO-only XAUUSD H4 system. "
                "Return one JSON object only. Never calculate or change entry, stop, target or volume. "
                "Approve only when the supplied deterministic candidate, real H1/H4/D1 evidence, data quality, "
                "market freshness and macro context agree. Otherwise veto or mark uncertain. "
                "You may only reduce risk with risk_multiplier; never increase it. Do not infer news direction."
            ),
        },
        {
            "role": "user",
            "content": json.dumps({"candidate": candidate, "snapshot": snapshot, "output_schema": schema}, ensure_ascii=False),
        },
    ]
    retry = Retry(
        total=1, connect=1, read=1, status=1, backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504), allowed_methods=frozenset(["POST"]), raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    try:
        with requests.Session() as client:
            client.mount("https://", adapter)
            response = client.post(
                endpoint,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "Accept": "application/json"},
                json={
                    "model": model,
                    "temperature": 0,
                    "max_tokens": 700,
                    "response_format": {"type": "json_object"},
                    "messages": messages,
                },
                timeout=(8, 45),
            )
            response.raise_for_status()
            payload = response.json()
        parsed = _parse_ai_json(_extract_ai_content(payload))
        assessment = _validate_trade_ai_assessment(parsed, candidate)
        assessment["model"] = model
        return assessment
    except (requests.RequestException, ValueError, TypeError):
        return {
            "decision": "uncertain", "direction": "HOLD", "confidence": 0,
            "risk_multiplier": 0.25, "regime": "unavailable", "news_risk": "unknown",
            "reasons": ["پاسخ ساختاریافته AI در دسترس نبود؛ معامله متوقف شد."],
            "invalidators": [], "model": model,
        }


def _to_yahoo_forex_symbol(symbol):
    normalized = symbol.strip().upper().replace(" ", "")
    aliases = {
        "EUR/USD": "EURUSD=X",
        "GBP/USD": "GBPUSD=X",
        "AUD/USD": "AUDUSD=X",
        "NZD/USD": "NZDUSD=X",
        "USD/JPY": "JPY=X",
        "USD/CHF": "CHF=X",
        "USD/CAD": "CAD=X",
    }
    if normalized in aliases:
        return aliases[normalized]
    if "/" in normalized:
        return normalized.replace("/", "") + "=X"
    if normalized.endswith("=X"):
        return normalized
    return normalized + "=X"


def _yahoo_interval_config(interval, outputsize):
    if interval == "15min":
        return "15m", "60d", 1
    if interval == "4h":
        return "1h", "6mo", 4
    if interval == "1day":
        return "1d", "2y", 1
    return "60m", "60d", 1


def _fetch_yahoo_forex_prices(symbol, interval, outputsize):
    yahoo_symbol = _to_yahoo_forex_symbol(symbol)
    yahoo_interval, yahoo_range, step = _yahoo_interval_config(interval, outputsize)

    with _build_retry_session() as session_client:
        response = session_client.get(
            YAHOO_CHART_URL.format(symbol=yahoo_symbol),
            params={
                "interval": yahoo_interval,
                "range": yahoo_range,
            },
            timeout=(8, 30),
        )
        response.raise_for_status()
        payload = response.json()

    result = (payload.get("chart", {}).get("result") or [None])[0]
    if not result:
        raise ValueError("Yahoo Finance did not return price data.")

    timestamps = result.get("timestamp") or []
    quote = ((result.get("indicators") or {}).get("quote") or [None])[0] or {}
    closes = quote.get("close") or []
    highs = quote.get("high") or []
    lows = quote.get("low") or []

    rows = []
    for timestamp, high, low, close in zip(timestamps, highs, lows, closes):
        if close is None or high is None or low is None:
            continue
        rows.append(
            (
                datetime.fromtimestamp(timestamp, timezone.utc).isoformat(),
                float(high),
                float(low),
                float(close),
            )
        )

    if step > 1:
        aggregated = []
        for start in range(0, len(rows), step):
            group = rows[start : start + step]
            if len(group) != step:
                continue
            aggregated.append(
                (
                    group[-1][0],
                    max(item[1] for item in group),
                    min(item[2] for item in group),
                    group[-1][3],
                )
            )
        rows = aggregated

    rows = rows[-outputsize:]
    if len(rows) < 30:
        raise ValueError("Yahoo Finance returned insufficient data points.")

    labels, high_values, low_values, prices = zip(*rows)
    return {
        "symbol": symbol,
        "interval": interval,
        "prices": list(prices),
        "highs": list(high_values),
        "lows": list(low_values),
        "labels": list(labels),
        "provider": "Yahoo Finance",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def _last_non_nan(values):
    for value in reversed(values):
        if value is not None and not np.isnan(value):
            return float(value)
    return None


def _safe_float(value):
    if value is None:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    if np.isnan(value) or np.isinf(value):
        return None
    return value


def _mean_abs_recent(values, window=20):
    clean = [_safe_float(value) for value in values]
    clean = [value for value in clean if value is not None]
    if not clean:
        return 0.0
    recent = clean[-window:]
    return float(np.mean(np.abs(recent)))


def _clamp(value, low, high):
    return max(low, min(high, value))


def _compute_signal_summary(prices, rsi_values, macd_values, use_rsi=True, use_macd=True, use_tdigm=False, tdigm_value=1.0):
    rsi_list = rsi_values.tolist()
    macd_line = macd_values["MACD"].tolist()
    signal_line = macd_values["Signal Line"].tolist()
    histogram = macd_values["Histogram"].tolist()

    latest_price = float(prices[-1])
    latest_rsi = _last_non_nan(rsi_list)
    latest_macd = _last_non_nan(macd_line)
    latest_signal = _last_non_nan(signal_line)
    latest_hist = _last_non_nan(histogram)

    if not use_rsi:
        latest_rsi = None
    if not use_macd:
        latest_macd = None
        latest_signal = None
        latest_hist = None

    rsi_state = "Disabled"
    if use_rsi and latest_rsi is not None:
        if latest_rsi >= 70:
            rsi_state = "Overbought"
        elif latest_rsi <= 30:
            rsi_state = "Oversold"
        else:
            rsi_state = "Neutral"

    macd_bias = "Disabled"
    if use_macd and latest_macd is not None and latest_signal is not None:
        if latest_macd > latest_signal:
            macd_bias = "Bullish"
        elif latest_macd < latest_signal:
            macd_bias = "Bearish"
        else:
            macd_bias = "Neutral"

    cross_signal = "Disabled"
    if use_macd and len(macd_line) >= 2 and len(signal_line) >= 2:
        prev_macd = _safe_float(macd_line[-2])
        prev_signal = _safe_float(signal_line[-2])
        if all(v is not None for v in [prev_macd, prev_signal, latest_macd, latest_signal]):
            cross_signal = "None"
            if prev_macd <= prev_signal and latest_macd > latest_signal:
                cross_signal = "Bullish cross"
            elif prev_macd >= prev_signal and latest_macd < latest_signal:
                cross_signal = "Bearish cross"

    price_moves = np.diff(np.asarray(prices, dtype=np.float64))
    avg_price_move = float(np.mean(np.abs(price_moves[-20:]))) if len(price_moves) else 0.0
    recent_window = min(10, len(prices) - 1)
    recent_price_change = float(prices[-1] - prices[-1 - recent_window]) if recent_window > 0 else 0.0
    trend_scale = max(avg_price_move * max(1, recent_window), abs(latest_price) * 0.0001, 1e-9)
    trend_strength = _clamp(abs(recent_price_change) / trend_scale * 10, 0, 12)

    hist_scale = max(_mean_abs_recent(histogram, window=20), avg_price_move * 0.1, abs(latest_price) * 0.00001, 1e-9)
    macd_gap = None
    macd_strength = 0.0
    hist_strength = 0.0
    hist_slope = None
    prev_hist = _safe_float(histogram[-2]) if len(histogram) >= 2 else None
    if use_macd and latest_macd is not None and latest_signal is not None:
        macd_gap = latest_macd - latest_signal
        macd_strength = _clamp(abs(macd_gap) / hist_scale * 10, 0, 24)
    if use_macd and latest_hist is not None:
        hist_strength = _clamp(abs(latest_hist) / hist_scale * 6, 0, 8)
    if use_macd and latest_hist is not None and prev_hist is not None:
        hist_slope = latest_hist - prev_hist

    buy_score = 0.0
    sell_score = 0.0
    signal_factors = []

    if use_macd and macd_gap is not None:
        if macd_gap > 0:
            buy_score += macd_strength
            signal_factors.append(f"MACD is above signal by {macd_gap:.6f}.")
        elif macd_gap < 0:
            sell_score += macd_strength
            signal_factors.append(f"MACD is below signal by {abs(macd_gap):.6f}.")

    if use_macd and latest_hist is not None:
        if latest_hist > 0:
            buy_score += hist_strength
            signal_factors.append("MACD histogram is positive.")
        elif latest_hist < 0:
            sell_score += hist_strength
            signal_factors.append("MACD histogram is negative.")

    if hist_slope is not None:
        slope_strength = _clamp(abs(hist_slope) / hist_scale * 4, 0, 6)
        if hist_slope > 0:
            buy_score += slope_strength
            signal_factors.append("MACD histogram is improving.")
        elif hist_slope < 0:
            sell_score += slope_strength
            signal_factors.append("MACD histogram is weakening.")

    if cross_signal == "Bullish cross":
        buy_score += 12
        signal_factors.append("Fresh bullish MACD cross.")
    elif cross_signal == "Bearish cross":
        sell_score += 12
        signal_factors.append("Fresh bearish MACD cross.")

    if recent_price_change > 0:
        buy_score += trend_strength
        signal_factors.append("Recent price movement is upward.")
    elif recent_price_change < 0:
        sell_score += trend_strength
        signal_factors.append("Recent price movement is downward.")

    if use_rsi and latest_rsi is not None:
        if 52 <= latest_rsi <= 68:
            buy_score += _clamp((latest_rsi - 52) / 16 * 8, 2, 8)
            signal_factors.append("RSI supports bullish momentum without being overbought.")
        elif 32 <= latest_rsi <= 48:
            sell_score += _clamp((48 - latest_rsi) / 16 * 8, 2, 8)
            signal_factors.append("RSI supports bearish momentum without being oversold.")
        elif latest_rsi >= 70:
            buy_score -= 12
            sell_score += 4
            signal_factors.append("RSI is overbought, reducing buy quality.")
        elif latest_rsi <= 30:
            sell_score -= 12
            buy_score += 4
            signal_factors.append("RSI is oversold, reducing sell quality.")

    if use_tdigm and tdigm_value > 0:
        signal_factors.append(
            "Experimental TDIGM confirmation was recorded but does not change the deterministic score."
        )

    buy_score = max(0.0, buy_score)
    sell_score = max(0.0, sell_score)

    action_bias = "Wait"
    top_score = max(buy_score, sell_score)
    score_gap = abs(buy_score - sell_score)
    if top_score >= 12 and score_gap >= 5:
        if buy_score > sell_score:
            action_bias = "Cautious buy" if cross_signal == "Bullish cross" else "Buy bias"
        else:
            action_bias = "Cautious sell" if cross_signal == "Bearish cross" else "Sell bias"
    elif use_tdigm and tdigm_value > 0:
        action_bias = "Active watch (TDIGM)"

    agreement_bonus = _clamp(score_gap / 2, 0, 10)
    conflict_penalty = _clamp(min(buy_score, sell_score) / 2, 0, 12)
    signal_strength = int(round(38 + (top_score * 1.25) + agreement_bonus - conflict_penalty))
    if action_bias == "Wait":
        signal_strength = int(round(_clamp(35 + top_score * 0.6 - conflict_penalty, 30, 58)))
    signal_strength = int(_clamp(signal_strength, 30, 88))

    risk_level = "Medium"
    if signal_strength >= 72:
        risk_level = "Low to medium"
    elif signal_strength <= 48 or action_bias == "Wait":
        risk_level = "High"

    return {
        "latest_price": latest_price,
        "latest_rsi": latest_rsi,
        "rsi_state": rsi_state,
        "latest_macd": latest_macd,
        "latest_signal": latest_signal,
        "latest_histogram": latest_hist,
        "macd_bias": macd_bias,
        "cross_signal": cross_signal,
        "action_bias": action_bias,
        # Backwards-compatible alias; this is indicator agreement, not win probability.
        "confidence": signal_strength,
        "signal_strength": signal_strength,
        "signal_strength_label": "Indicator agreement score",
        "buy_score": round(buy_score, 2),
        "sell_score": round(sell_score, 2),
        "trend_strength": round(trend_strength, 2),
        "macd_strength": round(macd_strength, 2),
        "signal_factors": signal_factors[:6],
        "risk_level": risk_level,
        "note": (
            "Signal strength measures indicator agreement; it is not a probability of profit. "
            "This output is an analysis tool only."
        ),
    }


def _parse_prices_or_raise(prices):
    if prices is None:
        raise ValueError("Prices are required.")

    if not isinstance(prices, list) or len(prices) < 30:
        raise ValueError("At least 30 prices are required for reliable MACD/RSI analysis.")

    try:
        arr = np.asarray(prices, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ValueError("Prices must contain only numeric values.") from exc

    if np.isnan(arr).any() or np.isinf(arr).any():
        raise ValueError("Prices cannot contain NaN or infinite values.")

    return arr.tolist()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
@rate_limit(12, 300)
def login():
    if request.method == "GET":
        if session.get("logged_in"):
            return redirect(url_for("dashboard"))
        return render_template("login.html", csrf_token=_csrf_token())

    _require_csrf()

    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""

    if _valid_login(username, password):
        session["logged_in"] = True
        session["username"] = username
        session.permanent = True
        return redirect(url_for("dashboard"))

    return render_template("login.html", error="Invalid username or password.", csrf_token=_csrf_token())


@app.route("/logout", methods=["POST"])
def logout():
    _require_csrf()
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard")
def dashboard():
    # مهمان‌ها هم به داشبورد دسترسی دارند؛ محدودیت روی تعداد تحلیل اعمال می‌شود نه ورود.
    return render_template(
        "dashboard.html",
        username=session.get("username", "مهمان"),
        logged_in=bool(session.get("logged_in")),
        csrf_token=_csrf_token(),
    )


def _mt5_login_required():
    if session.get("logged_in"):
        return None
    return jsonify({
        "error": "برای دسترسی به اتصال محلی MT5 ابتدا وارد حساب TradeAI شوید.",
        "login_required": True,
        "login_url": url_for("login"),
    }), 401


@app.route("/mt5/status", methods=["GET"])
@rate_limit(20, 60)
def mt5_status():
    login_error = _mt5_login_required()
    if login_error:
        return login_error
    connector = MT5Connector()
    try:
        with connector.session(require_demo=True) as (_, status):
            portfolio = connector.portfolio_snapshot(days=7)
            return jsonify({
                "ok": True,
                **status,
                "portfolio": portfolio,
                "execution_enabled": _demo_execution_enabled(),
                "execution_mode": "demo_confirmed" if _demo_execution_enabled() else "signal_only",
            })
    except MT5ConnectorError as exc:
        return jsonify({
            "ok": False,
            "available": connector.available,
            "connected": False,
            "execution_mode": "signal_only",
            "error": str(exc),
        }), 503


@app.route("/mt5/market-data", methods=["POST"])
@rate_limit(30, 60)
def mt5_market_data():
    login_error = _mt5_login_required()
    if login_error:
        return login_error
    _require_csrf()
    data = request.get_json(silent=True) or {}
    symbol = str(data.get("symbol") or "EUR/USD").strip()[:32]
    interval = str(data.get("interval") or "15min").strip()[:16]
    try:
        count = int(data.get("outputsize") or 300)
    except (TypeError, ValueError):
        return jsonify({"error": "تعداد کندل معتبر نیست."}), 400
    # Incomplete candles are deliberately excluded from every signal path.
    connector = MT5Connector()
    try:
        with connector.session(require_demo=True) as (_, status):
            payload = connector.fetch_candles(
                symbol,
                interval,
                count=count,
                include_incomplete=False,
            )
        return jsonify({
            "ok": True,
            "account": status["account"],
            "terminal_trade_allowed": status.get("terminal_trade_allowed", False),
            "execution_mode": "demo_confirmed" if _demo_execution_enabled() else "signal_only",
            **payload,
        })
    except (MT5ConnectorError, TypeError, ValueError) as exc:
        return jsonify({"ok": False, "error": str(exc)}), 503


@app.route("/mt5/signal-preview", methods=["POST"])
@rate_limit(20, 60)
def mt5_signal_preview():
    login_error = _mt5_login_required()
    if login_error:
        return login_error
    _require_csrf()
    data = request.get_json(silent=True) or {}
    symbol = str(data.get("symbol") or "XAU/USD").strip()[:32]
    interval = str(data.get("interval") or "4h").strip().lower()[:16]
    try:
        normalized_symbol = symbol.upper().replace("/", "").replace(" ", "")
        if normalized_symbol != "XAUUSD" or interval not in {"4h", "h4"}:
            raise TradingRuleError("موتور معامله فعلاً فقط برای XAU/USD در تایم‌فریم H4 تأیید شده است.")
        count = min(max(int(data.get("outputsize") or 500), 200), 1_000)
        settings = SignalSettings(
            minimum_strength=int(data.get("minimum_strength") or 70),
            maximum_spread_pips=float(data.get("maximum_spread_pips") or 2.0),
            maximum_spread_bps=float(data.get("maximum_spread_bps") or 3.0),
            risk_percent=float(data.get("risk_percent") or 0.1),
            maximum_volume=float(data.get("maximum_volume") or 0.1),
            atr_stop_multiple=float(data.get("atr_stop_multiple") or 1.0),
            reward_risk=float(data.get("reward_risk") or 2.5),
            maximum_daily_loss_percent=float(data.get("maximum_daily_loss_percent") or 1.0),
            maximum_open_positions=int(data.get("maximum_open_positions") or 1),
            maximum_consecutive_losses=int(data.get("maximum_consecutive_losses") or 2),
            loss_cooldown_hours=int(data.get("loss_cooldown_hours") or 12),
            maximum_daily_trades=int(data.get("maximum_daily_trades") or 3),
            ai_minimum_confidence=int(data.get("ai_minimum_confidence") or 70),
            require_ai_confirmation=True,
        ).validated()
        rsi_period = int(data.get("rsi_period") or 21)
        macd_short = int(data.get("macd_short_period") or 8)
        macd_long = int(data.get("macd_long_period") or 21)
        macd_signal = int(data.get("macd_signal_period") or 5)
        if not 2 <= rsi_period <= 100:
            raise ValueError("RSI period must be between 2 and 100.")
        if not (2 <= macd_short < macd_long <= 200):
            raise ValueError("MACD periods must satisfy 2 <= short < long <= 200.")
        if not 2 <= macd_signal <= 100:
            raise ValueError("MACD signal period must be between 2 and 100.")

        connector = MT5Connector()
        with connector.session(require_demo=True) as (_, status):
            timeframe_data = {
                "H1": connector.fetch_candles(symbol, "1h", count=300, include_incomplete=False),
                "H4": connector.fetch_candles(symbol, "4h", count=count, include_incomplete=False),
                "D1": connector.fetch_candles(symbol, "1day", count=250, include_incomplete=False),
            }
            portfolio = connector.portfolio_snapshot(days=7)

        summaries = {}
        for timeframe_name, payload in timeframe_data.items():
            timeframe_prices = payload["prices"]
            timeframe_rsi = calculate_rsi(timeframe_prices, period=rsi_period)
            timeframe_macd = calculate_macd(
                timeframe_prices,
                short_period=macd_short,
                long_period=macd_long,
                signal_period=macd_signal,
            )
            summaries[timeframe_name] = _compute_signal_summary(timeframe_prices, timeframe_rsi, timeframe_macd)

        market_data = timeframe_data["H4"]
        prices = market_data["prices"]
        summary = summaries["H4"]
        atr_values = calculate_atr(
            market_data["highs"], market_data["lows"], prices, period=14
        )
        summary["latest_atr"] = _last_non_nan(atr_values.tolist())
        summary["volatility_source"] = "ATR"
        candidate = "BUY" if "buy" in str(summary.get("action_bias") or "").lower() else (
            "SELL" if "sell" in str(summary.get("action_bias") or "").lower() else "HOLD"
        )
        timeframe_confirmation = _true_timeframe_confirmation(summaries, candidate)
        summary["timeframe_alignment"] = timeframe_confirmation
        macro_context = _get_macro_context()
        macro_gate = _macro_trade_gate(macro_context, holding_hours=24)

        hard_ready_for_ai = all([
            candidate in {"BUY", "SELL"},
            market_data["quality"].get("safe_for_signal"),
            market_data["market"].get("market_open"),
            status.get("connected"),
            status.get("terminal_trade_allowed"),
            status.get("account", {}).get("trade_allowed"),
            status.get("account", {}).get("expert_allowed"),
            timeframe_confirmation.get("aligned"),
            macro_gate.get("clear"),
        ])
        if hard_ready_for_ai:
            ai_snapshot = {
                "symbol": market_data["symbol"],
                "primary_timeframe": "H4",
                "h4_summary": summary,
                "real_timeframes": timeframe_confirmation,
                "market": {
                    key: market_data["market"].get(key)
                    for key in ("bid", "ask", "spread_bps", "tick_age_seconds", "market_open")
                },
                "data_quality": market_data["quality"],
                "portfolio": portfolio,
                "macro_gate": macro_gate,
                "recent_h4_ohlc": market_data["candles"][-20:],
            }
            ai_assessment = _call_trade_ai_assessment(ai_snapshot, candidate)
        else:
            ai_assessment = {
                "decision": "uncertain", "direction": "HOLD", "confidence": 0,
                "risk_multiplier": 0.25, "regime": "blocked", "news_risk": "unknown",
                "reasons": ["یک یا چند قفل قطعی پیش از فراخوانی AI رد شده است."],
                "invalidators": [], "model": DEFAULT_OPENAI_MODEL,
            }

        initial = generate_signal(
            summary,
            market_data["market"],
            market_data["quality"],
            symbol=market_data["symbol"],
            interval=interval,
            candle_time=market_data["labels"][-1],
            settings=settings,
            account_status=status,
            portfolio=portfolio,
            timeframe_confirmation=timeframe_confirmation,
            macro_gate=macro_gate,
            ai_assessment=ai_assessment,
        )
        duplicate = signal_exists(_owner_id(), initial["signal_key"])
        signal = generate_signal(
            summary,
            market_data["market"],
            market_data["quality"],
            symbol=market_data["symbol"],
            interval=interval,
            candle_time=market_data["labels"][-1],
            settings=settings,
            duplicate=duplicate,
            account_status=status,
            portfolio=portfolio,
            timeframe_confirmation=timeframe_confirmation,
            macro_gate=macro_gate,
            ai_assessment=ai_assessment,
        )

        risk_plan = None
        broker_check = None
        execution_token = None
        if signal["signal"] in {"BUY", "SELL"}:
            risk_plan = build_risk_plan(
                signal["signal"], summary, market_data["market"], status["account"], settings,
                risk_multiplier=ai_assessment.get("risk_multiplier", 0.25),
            )
            signal["risk_plan"] = risk_plan
            with connector.session(require_demo=True):
                broker_check = connector.check_demo_order(market_data["symbol"], signal["signal"], risk_plan)
            if _demo_execution_enabled():
                execution_token = secrets.token_urlsafe(32)
                session["pending_demo_order"] = {
                    "token": execution_token,
                    "expires_at": int(time.time()) + 300,
                    "signal_key": signal["signal_key"],
                    "symbol": market_data["symbol"],
                    "direction": signal["signal"],
                    "plan": risk_plan,
                    "settings": {
                        "maximum_open_positions": settings.maximum_open_positions,
                        "maximum_daily_loss_percent": settings.maximum_daily_loss_percent,
                        "maximum_consecutive_losses": settings.maximum_consecutive_losses,
                        "loss_cooldown_hours": settings.loss_cooldown_hours,
                        "maximum_daily_trades": settings.maximum_daily_trades,
                    },
                    "signal": signal,
                }

        return jsonify({
            "ok": True,
            "signal": signal,
            "risk_plan": risk_plan,
            "summary": summary,
            "market": market_data["market"],
            "quality": market_data["quality"],
            "account": status["account"],
            "terminal_trade_allowed": status.get("terminal_trade_allowed", False),
            "portfolio": portfolio,
            "ai_assessment": ai_assessment,
            "timeframe_confirmation": timeframe_confirmation,
            "macro_gate": macro_gate,
            "broker_check": broker_check,
            "execution_mode": "demo_confirmed" if _demo_execution_enabled() else "signal_only",
            "execution_enabled": _demo_execution_enabled(),
            "execution_ready": bool(execution_token),
            "execution_token": execution_token,
            "execution_expires_seconds": 300 if execution_token else None,
            "order_sent": False,
            "strategy_parameters": {
                "rsi_period": rsi_period,
                "macd_short": macd_short,
                "macd_long": macd_long,
                "macd_signal": macd_signal,
                "atr_stop_multiple": settings.atr_stop_multiple,
                "reward_risk": settings.reward_risk,
            },
        })
    except (MT5ConnectorError, TradingRuleError, TypeError, ValueError) as exc:
        return jsonify({"ok": False, "error": str(exc), "order_sent": False}), 400


@app.route("/mt5/execute-demo", methods=["POST"])
@rate_limit(4, 60)
def mt5_execute_demo():
    login_error = _mt5_login_required()
    if login_error:
        return login_error
    _require_csrf()
    data = request.get_json(silent=True) or {}
    if not _demo_execution_enabled():
        return jsonify({"ok": False, "error": "ارسال سفارش دمو در تنظیمات فعال نیست."}), 403
    if str(data.get("confirmation") or "").strip().upper() != "DEMO":
        return jsonify({"ok": False, "error": "برای ارسال باید عبارت DEMO را تأیید کنید."}), 400
    pending = session.get("pending_demo_order") or {}
    provided_token = str(data.get("execution_token") or "")
    if not pending or int(pending.get("expires_at") or 0) < int(time.time()):
        session.pop("pending_demo_order", None)
        return jsonify({"ok": False, "error": "مهلت تأیید تمام شده است؛ دوباره تحلیل بگیرید."}), 409
    if not provided_token or not compare_digest(provided_token, str(pending.get("token") or "")):
        return jsonify({"ok": False, "error": "توکن تأیید سفارش معتبر نیست."}), 403

    owner_id = _owner_id()
    signal_key = str(pending.get("signal_key") or "")
    if signal_exists(owner_id, signal_key):
        session.pop("pending_demo_order", None)
        return jsonify({"ok": False, "error": "این سیگنال قبلاً اجرا شده است."}), 409
    token_hash = hashlib.sha256(provided_token.encode("utf-8")).hexdigest()
    reservation_payload = {
        "symbol": pending.get("symbol"), "direction": pending.get("direction"),
        "plan": pending.get("plan"), "created_from": "ai_confirmed_preview",
    }
    if not reserve_order_execution(owner_id, signal_key, token_hash, reservation_payload):
        session.pop("pending_demo_order", None)
        return jsonify({"ok": False, "error": "این سفارش قبلاً رزرو یا اجرا شده است؛ وضعیت MT5 را بررسی کنید."}), 409

    session.pop("pending_demo_order", None)
    try:
        connector = MT5Connector()
        with connector.session(require_demo=True) as (_, status):
            portfolio = connector.portfolio_snapshot(days=7)
            limits = pending.get("settings") or {}
            account = status.get("account") or {}
            if not all([status.get("connected"), status.get("terminal_trade_allowed"), account.get("trade_allowed"), account.get("expert_allowed")]):
                raise TradingRuleError("اجازه معامله در ترمینال یا حساب فعال نیست.")
            if int(portfolio.get("open_position_count") or 0) >= int(limits.get("maximum_open_positions") or 1):
                raise TradingRuleError("حداکثر پوزیشن باز پر شده است.")
            if int(portfolio.get("daily_trade_count") or 0) >= int(limits.get("maximum_daily_trades") or 3):
                raise TradingRuleError("سقف معامله روزانه پر شده است.")
            equity = float(account.get("equity") or 0)
            daily_loss = abs(min(0.0, float(portfolio.get("daily_realized_net") or 0))) / equity * 100 if equity > 0 else 100
            if daily_loss >= float(limits.get("maximum_daily_loss_percent") or 1):
                raise TradingRuleError("سقف زیان روزانه فعال شده است.")
            if int(portfolio.get("consecutive_losses") or 0) >= int(limits.get("maximum_consecutive_losses") or 2):
                latest_loss = portfolio.get("latest_loss_time_utc")
                try:
                    latest_loss_time = datetime.fromisoformat(str(latest_loss).replace("Z", "+00:00"))
                    if latest_loss_time.tzinfo is None:
                        latest_loss_time = latest_loss_time.replace(tzinfo=timezone.utc)
                    cooldown_until = latest_loss_time + timedelta(hours=int(limits.get("loss_cooldown_hours") or 12))
                except (TypeError, ValueError):
                    cooldown_until = datetime.max.replace(tzinfo=timezone.utc)
                if datetime.now(timezone.utc) < cooldown_until:
                    raise TradingRuleError(f"توقف موقت زیان‌های متوالی تا {cooldown_until.isoformat()} فعال است.")
            result = connector.send_demo_order(
                str(pending.get("symbol") or "XAUUSD"),
                str(pending.get("direction") or ""),
                pending.get("plan") or {},
            )
        finalize_order_execution(owner_id, signal_key, "sent", result)
        signal_payload = pending.get("signal") or {}
        save_signal_event(owner_id, signal_payload)
        plan = pending.get("plan") or {}
        add_journal_entry(owner_id, {
            "symbol": str(pending.get("symbol") or "XAUUSD"),
            "direction": str(pending.get("direction") or "").lower(),
            "entry_price": result.get("price") or plan.get("entry"),
            "stop_loss": plan.get("stop_loss"),
            "take_profit": plan.get("take_profit"),
            "status": "open",
            "notes": f"MT5 demo order={result.get('order')} deal={result.get('deal')} volume={result.get('volume')}",
        })
        return jsonify({"ok": True, "order_sent": True, "result": result})
    except (MT5ConnectorError, TradingRuleError, TypeError, ValueError) as exc:
        finalize_order_execution(owner_id, signal_key, "blocked_or_unknown", {"error": str(exc)})
        return jsonify({
            "ok": False,
            "error": f"سفارش ارسال نشد یا نتیجه قطعی نیست: {exc} وضعیت Orders/Positions متاتریدر را قبل از تلاش مجدد بررسی کنید.",
            "order_sent": False,
        }), 409


@app.route("/mt5/executions", methods=["GET"])
@rate_limit(20, 60)
def mt5_executions():
    login_error = _mt5_login_required()
    if login_error:
        return login_error
    return jsonify({"ok": True, "items": list_order_executions(_owner_id(), limit=30)})


@app.route("/fetch_forex_prices", methods=["POST"])
@rate_limit(30, 60)
def fetch_forex_prices():
    # دریافت قیمت، مرحله‌ی مقدماتیِ تحلیل است و برای مهمان هم آزاد است.
    data = request.get_json(silent=True) or {}
    symbol = (data.get("symbol") or "EUR/USD").strip()
    interval = (data.get("interval") or "1h").strip()
    try:
        outputsize = int(data.get("outputsize") or 150)
    except (TypeError, ValueError):
        return jsonify({"error": "Output size must be a valid number."}), 400

    api_key = (
        data.get("provider_api_key")
        or os.getenv("TAHLIL_TWELVEDATA_API_KEY")
        or os.getenv("TWELVEDATA_API_KEY")
        or ""
    ).strip()

    payload = None
    twelvedata_error = None
    try:
        if api_key:
            payload = _fetch_twelvedata_time_series(symbol, interval, outputsize, api_key)
    except requests.RequestException as exc:
        twelvedata_error = str(exc)
    except ValueError:
        twelvedata_error = "TwelveData response was not valid JSON."

    if payload is None:
        try:
            return jsonify(_fetch_yahoo_forex_prices(symbol, interval, outputsize))
        except (requests.RequestException, ValueError) as exc:
            return jsonify(
                {
                    "error": (
                        "Could not connect to price data services. "
                        "If this is running on Liara, check outbound server access to TwelveData/Yahoo Finance "
                        "or enter prices manually."
                    ),
                    "details": {
                        "twelvedata": twelvedata_error or "TwelveData API key is not configured.",
                        "fallback": str(exc),
                    },
                }
            ), 502

    if payload.get("status") == "error":
        try:
            return jsonify(_fetch_yahoo_forex_prices(symbol, interval, outputsize))
        except (requests.RequestException, ValueError):
            return jsonify({"error": payload.get("message", "Failed to fetch forex prices.")}), 400

    rows = payload.get("values") or []
    if not rows:
        return jsonify({"error": "No price data returned from provider."}), 400

    rows = list(reversed(rows))
    prices = []
    highs = []
    lows = []
    labels = []

    for row in rows:
        try:
            prices.append(float(row["close"]))
            highs.append(float(row.get("high", row["close"])))
            lows.append(float(row.get("low", row["close"])))
            labels.append(row.get("datetime", ""))
        except (KeyError, TypeError, ValueError):
            continue

    if len(prices) < 30:
        return jsonify({"error": "Provider returned insufficient data points."}), 400

    return jsonify(
        {
            "symbol": symbol,
            "interval": interval,
            "prices": prices,
            "highs": highs,
            "lows": lows,
            "labels": labels,
            "provider": "TwelveData",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    )


@app.route("/calculate_indicators", methods=["POST"])
@rate_limit(60, 60)
def calculate_indicators():
    _require_csrf()
    # محاسبه‌ی اندیکاتور هم بخشی از آماده‌سازیِ تحلیل است و برای مهمان آزاد است.
    data = request.get_json(silent=True) or {}

    try:
        prices = _parse_prices_or_raise(data.get("prices"))
        use_rsi = bool(data.get("use_rsi", True))
        use_macd = bool(data.get("use_macd", True))
        use_macd_long = bool(data.get("use_macd_long", True))
        use_macd_signal = bool(data.get("use_macd_signal", True))
        use_tdigm = bool(data.get("use_tdigm", False))
        rsi_period = int(data.get("rsi_period", 14))
        macd_short_period = int(data.get("macd_short_period", 12))
        macd_long_period = int(data.get("macd_long_period", 26))
        macd_signal_period = int(data.get("macd_signal_period", 9))
        tdigm_value = float(data.get("tdigm_value", 1.0))
        symbol = str(data.get("symbol") or "Manual").strip().upper()[:24]
        interval = str(data.get("interval") or "custom").strip()[:16]

        if not use_macd_long:
            macd_long_period = 26
        if not use_macd_signal:
            macd_signal_period = 9

        rsi_values = calculate_rsi(prices, period=rsi_period) if use_rsi else calculate_rsi(prices, period=14) * 0
        macd_values = calculate_macd(
            prices,
            short_period=macd_short_period,
            long_period=macd_long_period,
            signal_period=macd_signal_period,
        ) if use_macd else calculate_macd(prices, short_period=12, long_period=26, signal_period=9) * 0
        summary = _compute_signal_summary(
            prices,
            rsi_values,
            macd_values,
            use_rsi=use_rsi,
            use_macd=use_macd,
            use_tdigm=use_tdigm,
            tdigm_value=tdigm_value,
        )
        highs = data.get("highs")
        lows = data.get("lows")
        if isinstance(highs, list) and isinstance(lows, list) and len(highs) == len(prices) == len(lows):
            atr_values = calculate_atr(highs, lows, prices, period=14)
            summary["volatility_source"] = "ATR"
        else:
            atr_values = close_volatility(prices, period=14)
            summary["volatility_source"] = "Close-to-close ATR proxy"
        summary["latest_atr"] = _last_non_nan(atr_values.tolist())
        summary["timeframe_alignment"] = multi_timeframe_alignment(prices)
        history_id = save_analysis(_owner_id(), symbol, interval, summary)
    except (TypeError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(
        {
            "prices": prices,
            "RSI": rsi_values.fillna(0).tolist(),
            "MACD": macd_values.fillna(0).to_dict(orient="list"),
            "ATR": atr_values.fillna(0).tolist(),
            "summary": summary,
            "history_id": history_id,
        }
    )


@app.route("/backtest", methods=["POST"])
@rate_limit(20, 60)
def backtest():
    _require_csrf()
    data = request.get_json(silent=True) or {}
    try:
        prices = _parse_prices_or_raise(data.get("prices"))
        common = {
            "rsi_period": int(data.get("rsi_period", 14)),
            "macd_short": int(data.get("macd_short_period", 12)),
            "macd_long": int(data.get("macd_long_period", 26)),
            "macd_signal": int(data.get("macd_signal_period", 9)),
            "holding_bars": int(data.get("holding_bars", 6)),
        }
        opens = data.get("opens")
        highs = data.get("highs")
        lows = data.get("lows")
        if all(isinstance(values, list) and len(values) == len(prices) for values in (opens, highs, lows)):
            legacy_fee = float(data.get("fee_bps", 2))
            result = run_ohlc_backtest(
                opens,
                highs,
                lows,
                prices,
                timestamps=data.get("timestamps"),
                **common,
                atr_stop_multiple=float(data.get("atr_stop_multiple", 1.5)),
                reward_risk=float(data.get("reward_risk", 2.0)),
                risk_percent=float(data.get("risk_percent", 0.5)),
                spread_bps=float(data.get("spread_bps", legacy_fee * 2)),
                commission_bps_per_side=float(data.get("commission_bps_per_side", 0)),
                slippage_bps_per_side=float(data.get("slippage_bps_per_side", 0.2)),
                max_drawdown_pct=float(data.get("max_drawdown_pct", 10)),
                max_daily_loss_pct=float(data.get("max_daily_loss_pct", 3)),
                max_trades_per_day=int(data.get("max_trades_per_day", 5)),
                max_consecutive_losses=int(data.get("max_consecutive_losses", 3)),
            )
        else:
            result = run_backtest(prices, **common, fee_bps=float(data.get("fee_bps", 2)))
    except (TypeError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(result)


@app.route("/history", methods=["GET"])
@rate_limit(60, 60)
def history():
    return jsonify({"items": list_analyses(_owner_id(), limit=30)})


@app.route("/journal", methods=["GET", "POST"])
@rate_limit(60, 60)
def journal():
    owner_id = _owner_id()
    if request.method == "GET":
        return jsonify({"items": list_journal(owner_id, limit=50)})

    _require_csrf()
    data = request.get_json(silent=True) or {}
    symbol = str(data.get("symbol") or "").strip().upper()[:24]
    direction = str(data.get("direction") or "").strip().lower()
    status = str(data.get("status") or "open").strip().lower()
    if not symbol:
        return jsonify({"error": "Symbol is required."}), 400
    if direction not in {"buy", "sell"}:
        return jsonify({"error": "Direction must be buy or sell."}), 400
    if status not in {"open", "won", "lost", "cancelled"}:
        return jsonify({"error": "Invalid journal status."}), 400

    cleaned = {
        "symbol": symbol,
        "direction": direction,
        "status": status,
        "notes": str(data.get("notes") or "").strip()[:1000],
    }
    for key in ("entry_price", "exit_price", "stop_loss", "take_profit"):
        value = data.get(key)
        if value in (None, ""):
            cleaned[key] = None
            continue
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return jsonify({"error": f"{key} must be numeric."}), 400
        if not np.isfinite(parsed) or parsed <= 0:
            return jsonify({"error": f"{key} must be a positive number."}), 400
        cleaned[key] = parsed
    entry_id = add_journal_entry(owner_id, cleaned)
    return jsonify({"ok": True, "id": entry_id}), 201


def _parse_ai_json(content):
    """خروجی مدل را به JSON تبدیل می‌کند؛ نسبت به code-fence و متنِ اضافه مقاوم است."""
    if not content:
        return None
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                value = item.get("text") or item.get("content") or item.get("value")
                if value:
                    parts.append(str(value))
        content = "\n".join(parts)
    if isinstance(content, dict):
        return content
    if not isinstance(content, str):
        content = str(content)
    text = content.strip()
    if text.startswith("```"):
        # حذف ``` و ```json ابتدا/انتها
        text = text.strip("`").strip()
        if text[:4].lower() == "json":
            text = text[4:].strip()
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        pass
    # اگر متنِ توضیحی دور JSON بود، اولین بلوکِ {...} را استخراج کن
    import re
    match = re.search(r"\{.*\}", text, re.S)
    if match:
        try:
            return json.loads(match.group(0))
        except (ValueError, TypeError):
            return None
    return None


def _extract_ai_content(payload):
    """Support common OpenAI-compatible response variants used by gateway providers."""
    if not isinstance(payload, dict):
        return None
    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        choice = choices[0] or {}
        if isinstance(choice, dict):
            message = choice.get("message") or {}
            if isinstance(message, dict) and message.get("content") is not None:
                return message.get("content")
            if choice.get("text") is not None:
                return choice.get("text")
    if payload.get("output_text") is not None:
        return payload.get("output_text")
    output = payload.get("output")
    if isinstance(output, list):
        parts = []
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("text"):
                        parts.append(str(part["text"]))
        if parts:
            return "\n".join(parts)
    return None


def _repair_ai_analysis(url, headers, model, content, output_schema):
    """One bounded repair attempt for malformed provider JSON."""
    try:
        response = requests.post(
            url,
            headers=headers,
            json={
                "model": model,
                "temperature": 0,
                "max_tokens": 1200,
                "response_format": {"type": "json_object"},
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Repair the supplied response into one valid JSON object. "
                            "Return JSON only, include every schema field, and do not add facts."
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "schema": output_schema,
                                "malformed_response": str(content or "")[:6000],
                            },
                            ensure_ascii=False,
                        ),
                    },
                ],
            },
            timeout=45,
        )
        response.raise_for_status()
        payload = response.json()
        repaired = _parse_ai_json(_extract_ai_content(payload))
        if repaired is None:
            return None, payload.get("usage")
        return _validate_ai_analysis(repaired), payload.get("usage")
    except (requests.RequestException, ValueError, TypeError):
        return None, None


def _validate_ai_analysis(value):
    """Return a safe, normalized AI interpretation or raise ValueError."""
    if not isinstance(value, dict):
        raise ValueError("AI analysis must be an object.")
    required_text = (
        "market_state",
        "profile_used",
        "action_bias",
        "execution_type",
        "liquidity_note",
        "entry_idea",
        "stop_loss_idea",
        "take_profit_idea",
    )
    normalized = {}
    for key in required_text:
        text = str(value.get(key) or "").strip()
        if not text:
            raise ValueError(f"AI analysis is missing {key}.")
        normalized[key] = text[:800]
    try:
        normalized["confidence"] = int(_clamp(int(value.get("confidence")), 0, 100))
        normalized["holding_time_minutes"] = int(_clamp(int(value.get("holding_time_minutes")), 0, 43200))
    except (TypeError, ValueError) as exc:
        raise ValueError("AI analysis returned invalid numeric fields.") from exc
    for key, maximum in (("why", 6), ("risk_warnings", 6), ("nds_checklist", 6)):
        raw = value.get(key) or []
        if not isinstance(raw, list):
            raise ValueError(f"AI analysis field {key} must be a list.")
        normalized[key] = [str(item).strip()[:500] for item in raw[:maximum] if str(item).strip()]
    return normalized


@app.route("/analyze_with_ai", methods=["POST"])
@rate_limit(8, 60)
def analyze_with_ai():
    _require_csrf()
    # مهمان ۲ تحلیل رایگان دارد؛ از تحلیل سوم به بعد باید وارد شود.
    if _analysis_quota_exceeded():
        return _login_required_response()

    data = request.get_json(silent=True) or {}
    raw_summary = data.get("summary") or {}
    if not isinstance(raw_summary, dict):
        return jsonify({"error": "Invalid analysis summary."}), 400
    allowed_summary_keys = {
        "latest_price", "latest_rsi", "rsi_state", "latest_macd", "latest_signal",
        "latest_histogram", "macd_bias", "cross_signal", "action_bias",
        "signal_strength", "buy_score", "sell_score", "trend_strength",
        "macd_strength", "signal_factors", "risk_level", "latest_atr",
        "volatility_source", "timeframe_alignment",
    }
    summary = {key: raw_summary[key] for key in allowed_summary_keys if key in raw_summary}
    recent_prices = data.get("recent_prices") or []
    try:
        recent_prices = _parse_prices_or_raise(recent_prices)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    trade_profile = (data.get("trade_profile") or "scalp").strip().lower()
    symbol = str(data.get("symbol") or "Unknown").strip().upper()[:24]
    interval = str(data.get("interval") or "custom").strip()[:16]
    language = (data.get("language") or "English").strip()
    if language.lower() in {"fa", "farsi", "persian"}:
        language = "Persian"
    else:
        language = "English"
    try:
        custom_max_holding_minutes = int(data.get("custom_max_holding_minutes") or 0)
    except (TypeError, ValueError):
        custom_max_holding_minutes = 0

    configured_api_key = (
        os.getenv("TAHLIL_AI_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or ""
    ).strip()
    openai_api_key = configured_api_key or (str(data.get("openai_api_key") or "").strip() if not IS_PRODUCTION else "")
    model = DEFAULT_OPENAI_MODEL

    if not openai_api_key:
        return jsonify({"error": "AI provider API key is required."}), 400

    trade_profiles = {
        "scalp": {
            "mode": "scalping",
            "execution_priority": "high_volume_fast_execution",
            "max_holding_minutes": 30,
            "prefer_liquid_sessions": True,
            "style_notes": "very short holding, fast execution, tight stop-loss",
        },
        "day": {
            "mode": "day_trading",
            "execution_priority": "balanced_speed_precision",
            "max_holding_minutes": 480,
            "prefer_liquid_sessions": True,
            "style_notes": "intra-day opportunities, medium stop-loss, no overnight hold",
        },
        "swing": {
            "mode": "swing_trading",
            "execution_priority": "precision_over_speed",
            "max_holding_minutes": 4320,
            "prefer_liquid_sessions": False,
            "style_notes": "multi-session move, wider stop-loss, trend continuation",
        },
        "nds": {
            "mode": "nds",
            "execution_priority": "speed_with_confirmation",
            "max_holding_minutes": 60,
            "prefer_liquid_sessions": True,
            "style_notes": "multi-condition fast confirmation with strict invalidation",
        },
    }
    if trade_profile not in trade_profiles:
        return jsonify({"error": "Invalid trading profile."}), 400
    style = trade_profiles[trade_profile]
    if custom_max_holding_minutes > 0:
        style = {**style, "max_holding_minutes": custom_max_holding_minutes}

    macro_context = _get_macro_context()

    system_prompt = (
        "You are a forex trading assistant for high-liquidity forex pairs. "
        "Output only valid JSON. Do not guarantee profit. "
        "Align recommendations with the provided trading profile, "
        "risk control, and clear invalidation levels."
    )

    user_prompt = {
        "task": "Generate a trading interpretation from indicator summary based on the selected trading profile.",
        "language": language,
        "trading_profile": trade_profile,
        "trading_style": style,
        "input": {
            "symbol": symbol,
            "interval": interval,
            "summary": summary,
            "recent_prices": recent_prices[-30:],
            "us_macro_calendar": macro_context,
        },
        "requirements": [
            "Fully adapt analysis to the selected profile (scalp/day/swing/nds).",
            "Entry idea must be actionable for that profile's execution speed.",
            "Risk must be strict and proportional to the selected profile.",
            "For nds profile, include a short checklist of condition confirmations.",
            "If confidence is low, explicitly recommend no-trade.",
            "Use the US macro calendar as risk context, especially for USD pairs and XAUUSD.",
            "Upcoming releases without forecast/actual values are not directional evidence; never infer bullish or bearish impact from their date alone.",
            "When a listed release date overlaps the proposed holding period, mention event risk in liquidity_note or risk_warnings.",
            "Calendar precision is date-only. Never invent an exact release time, impact rating, consensus forecast, or news headline.",
            "If macro calendar available is false, continue with technical analysis and disclose that macro confirmation was unavailable.",
            f"Write every user-facing field in {language}.",
            "Keep wording concise and practical for rapid decision making.",
        ],
        "output_schema": {
            "market_state": "string",
            "profile_used": "string (scalp|day|swing|nds)",
            "action_bias": "string",
            "confidence": "integer 0-100",
            "execution_type": "string (market|limit|no-trade)",
            "holding_time_minutes": "integer",
            "liquidity_note": "string",
            "entry_idea": "string",
            "stop_loss_idea": "string",
            "take_profit_idea": "string",
            "nds_checklist": ["string", "string", "string"],
            "why": ["string", "string", "string"],
            "risk_warnings": ["string", "string"],
        },
    }

    url = _resolve_openai_url()
    ai_headers = {
        "Authorization": f"Bearer {openai_api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            url,
            headers=ai_headers,
            json={
                "model": model,
                "temperature": 0.2,
                "max_tokens": 1200,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(user_prompt, ensure_ascii=False)},
                ],
            },
            timeout=45,
        )
    except requests.RequestException:
        return jsonify({"error": "Failed to connect to the configured AI provider."}), 502

    if response.status_code >= 400:
        try:
            error_payload = response.json()
            message = error_payload.get("error", {}).get("message", "OpenAI request failed.")
        except ValueError:
            message = "AI provider request failed."
        return jsonify({"error": message}), 400

    try:
        payload = response.json()
    except ValueError:
        return jsonify({"error": "Invalid response format from the configured AI provider.", "retryable": True}), 502

    content = _extract_ai_content(payload)
    if content is None:
        return jsonify(
            {
                "error": "AI provider returned an empty response. Please run the analysis again.",
                "retryable": True,
            }
        ), 502

    analysis = _parse_ai_json(content)
    repair_usage = None
    if analysis is not None:
        try:
            analysis = _validate_ai_analysis(analysis)
        except ValueError:
            analysis = None
    if analysis is None:
        analysis, repair_usage = _repair_ai_analysis(
            url,
            ai_headers,
            model,
            content,
            user_prompt["output_schema"],
        )
    if analysis is None:
        return jsonify(
            {
                "error": "AI response could not be normalized. Please run the analysis again.",
                "retryable": True,
            }
        ), 502

    # تحلیلِ موفق را در سهمیه‌ی مهمان ثبت کن (کاربرِ واردشده شمارش نمی‌شود).
    _register_guest_analysis()

    return jsonify(
        {
            "model": model,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "analysis": analysis,
            "macro_context": macro_context,
            "disclaimer": "This analysis is not guaranteed investment advice and must be used with risk management.",
            "guest_remaining": max(GUEST_FREE_ANALYSES - _guest_analyses_used(), 0) if not session.get("logged_in") else None,
        }
    )


# ─── چت‌بات آموزشی صفحه ───────────────────────────────────────────────────────
ASSISTANT_SYSTEM_PROMPT = (
    "تو «استاد کاوش» هستی؛ استاد معامله‌گری و مشاور فارسی‌زبان در داشبورد TradeAI. "
    "شخصیتت آرام، باتجربه، صمیمی و در مدیریت ریسک سخت‌گیر است. پاسخ را آموزشی و قابل‌فهم می‌دهی، "
    "کاربر را هیجان‌زده یا به ورود عجولانه تشویق نمی‌کنی و وقتی شواهد کافی نیست، صریحاً پیشنهاد صبر می‌دهی. "
    "به سوال‌های کاربر درباره‌ی همین صفحه پاسخ می‌دهی — معنی و کاربرد اندیکاتورهای انتخاب‌شده "
    "(RSI، MACD و…)، تفسیر داده‌ها و نمودارها، جمع‌بندی تصمیم، و مفاهیم معامله‌گری (اسکالپ/دی‌تریدینگ/سوینگ). "
    "از «اطلاعاتِ صفحه» که در اختیارت گذاشته می‌شود استفاده کن و دقیق و کوتاه جواب بده. "
    "این برنامه محلی و شخصی است؛ اطلاعات تماس، سفارش خرید یا ثبت‌نام از کاربر درخواست نکن. "
    "هیچ تضمینِ سود نده و توصیه‌ی سرمایه‌گذاریِ قطعی نکن. لحن: محترم، کوتاه و فارسی روان (حداکثر ۳ تا ۴ جمله)."
)

ASSISTANT_FALLBACK = (
    "سلام، من استاد کاوش هستم. می‌توانم اندیکاتورها، نمودارها، مدیریت ریسک و پلن معامله‌تان را بررسی کنم. "
    "وقتی شواهد کافی نباشد پیشنهاد می‌کنم صبر کنید و هیچ سودی را تضمین نمی‌کنم."
)


def _summarize_context(context):
    """ساختِ خلاصه‌ای فشرده از وضعیت صفحه برای دادن به مدل."""
    if not isinstance(context, dict):
        return ""
    parts = []
    if context.get("symbol"):
        parts.append(f"جفت‌ارز: {context.get('symbol')}")
    if context.get("interval"):
        parts.append(f"تایم‌فریم: {context.get('interval')}")
    inds = context.get("indicators")
    if isinstance(inds, list) and inds:
        parts.append("اندیکاتورهای انتخابی: " + "، ".join(str(i) for i in inds))
    if context.get("decision"):
        parts.append(f"جمع‌بندی تصمیم: {context.get('decision')}")
    mentor_modes = {
        "teacher": "آموزش قدم‌به‌قدم",
        "advisor": "مشاوره و تحلیل",
        "reviewer": "بررسی سخت‌گیرانه معامله",
    }
    if context.get("mentor_mode") in mentor_modes:
        parts.append(f"حالت استاد: {mentor_modes[context['mentor_mode']]}")
    summary = context.get("summary")
    if summary:
        parts.append("خلاصه‌ی شاخص‌ها: " + json.dumps(summary, ensure_ascii=False)[:600])
    return "\n".join(parts)


@app.route("/assistant-chat", methods=["POST"])
@rate_limit(20, 60)
def assistant_chat():
    _require_csrf()

    payload = request.get_json(silent=True) or {}
    raw = payload.get("messages")
    context_text = _summarize_context(payload.get("context"))

    history = []
    if isinstance(raw, list):
        for item in raw[-12:]:
            if isinstance(item, dict) and item.get("role") in ("user", "assistant"):
                content = str(item.get("content", "")).strip()
                if content:
                    history.append({"role": item["role"], "content": content[:1500]})
    if not history:
        return jsonify({"ok": False, "error": "empty"}), 400

    api_key, model, endpoint = _ai_config_chat()
    if not api_key:
        reply = ASSISTANT_FALLBACK
        return jsonify({
            "ok": False,
            "reply": reply,
            "error": "ai_not_configured",
        }), 503
    else:
        sys_prompt = ASSISTANT_SYSTEM_PROMPT
        if context_text:
            sys_prompt += "\n\n[اطلاعاتِ صفحه‌ی فعلی]\n" + context_text
        messages = [{"role": "system", "content": sys_prompt}] + history
        reply = _call_ai_chat(messages, api_key, model, endpoint)
        if not reply:
            return jsonify({
                "ok": False,
                "error": "ai_temporarily_unavailable",
                "message": "استاد کاوش موقتاً به سرویس هوش مصنوعی دسترسی ندارد؛ لطفاً چند لحظه دیگر دوباره تلاش کنید.",
            }), 503

    return jsonify({
        "ok": True,
        "reply": reply or ASSISTANT_FALLBACK,
        "assistant": "ostad-kavosh",
    })


def _ai_config_chat():
    # Read configuration on every request so a deployment can rotate keys without
    # baking secrets into the source code.
    api_key = (
        os.getenv("TAHLIL_AI_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or ""
    ).strip()
    model = (os.getenv("TAHLIL_AI_MODEL") or os.getenv("OPENAI_MODEL") or DEFAULT_OPENAI_MODEL).strip()
    explicit_endpoint = (
        os.getenv("TAHLIL_AI_ENDPOINT")
        or os.getenv("OPENAI_ENDPOINT")
        or ""
    ).strip()
    if explicit_endpoint:
        return api_key, model, explicit_endpoint
    base = (os.getenv("TAHLIL_AI_BASE_URL") or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1").strip().rstrip("/")
    endpoint = base if base.endswith("/chat/completions") else f"{base}/chat/completions"
    return api_key, model, endpoint


def _normalize_ai_text(content):
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("text"):
                parts.append(str(item["text"]))
        return "\n".join(parts).strip()
    return ""


def _call_ai_chat(messages, api_key, model, endpoint):
    """Call an OpenAI-compatible chat endpoint with bounded transient retries."""
    retry = Retry(
        total=2,
        connect=2,
        read=2,
        status=2,
        backoff_factor=0.7,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["POST"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    with requests.Session() as session_client:
        session_client.mount("https://", adapter)
        session_client.mount("http://", adapter)
        try:
            response = session_client.post(
                endpoint,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                    "User-Agent": "TradeAI/1.0",
                },
                json={
                    "model": model,
                    "temperature": 0.45,
                    "max_tokens": 600,
                    "messages": messages,
                },
                timeout=(8, 45),
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError):
            return None

    return _normalize_ai_text(_extract_ai_content(payload)) or None


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5001"))
    host = os.getenv("HOST", "127.0.0.1")
    debug = os.getenv("TAHLIL_DEBUG", "0").lower() in {"1", "true", "yes"}
    app.run(host=host, debug=debug, use_reloader=False, port=port)
