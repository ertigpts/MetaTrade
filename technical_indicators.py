import numpy as np
import pandas as pd


def _validate_prices(prices):
    if prices is None:
        raise ValueError("Prices are required.")

    if not isinstance(prices, list) or len(prices) == 0:
        raise ValueError("Prices must be a non-empty list of numbers.")

    try:
        prices_array = np.asarray(prices, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ValueError("Prices must contain only numeric values.") from exc

    if np.isnan(prices_array).any() or np.isinf(prices_array).any():
        raise ValueError("Prices cannot contain NaN or infinite values.")

    return prices_array


def calculate_rsi(prices, period=14):
    prices_array = _validate_prices(prices)

    if period <= 0:
        raise ValueError("RSI period must be a positive integer.")

    prices_series = pd.Series(prices_array, dtype="float64")
    delta = prices_series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.where(avg_loss != 0, 100)
    rsi = rsi.where(avg_gain != 0, 0)

    return pd.Series(rsi, name="RSI")


def calculate_macd(prices, short_period=12, long_period=26, signal_period=9):
    prices_array = _validate_prices(prices)

    if short_period <= 0 or long_period <= 0 or signal_period <= 0:
        raise ValueError("MACD periods must be positive integers.")

    if short_period >= long_period:
        raise ValueError("short_period must be less than long_period.")

    prices_series = pd.Series(prices_array, dtype="float64")
    short_ema = prices_series.ewm(span=short_period, min_periods=short_period, adjust=False).mean()
    long_ema = prices_series.ewm(span=long_period, min_periods=long_period, adjust=False).mean()
    macd = short_ema - long_ema
    signal = macd.ewm(span=signal_period, min_periods=signal_period, adjust=False).mean()
    histogram = macd - signal

    return pd.DataFrame(
        {
            "MACD": macd,
            "Signal Line": signal,
            "Histogram": histogram,
        }
    )
