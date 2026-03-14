"""
Atomic factor operators for panel DataFrames (rows=dates, cols=tickers).
"""

import numpy as np
import pandas as pd


def ts_mean(df: pd.DataFrame, window: int) -> pd.DataFrame:
    return df.rolling(window=window, min_periods=1).mean()


def ts_std(df: pd.DataFrame, window: int) -> pd.DataFrame:
    return df.rolling(window=window, min_periods=1).std()


def ts_max(df: pd.DataFrame, window: int) -> pd.DataFrame:
    return df.rolling(window=window, min_periods=1).max()


def ts_min(df: pd.DataFrame, window: int) -> pd.DataFrame:
    return df.rolling(window=window, min_periods=1).min()


def delta(df: pd.DataFrame, period: int) -> pd.DataFrame:
    return df - df.shift(period)


def delay(df: pd.DataFrame, period: int) -> pd.DataFrame:
    return df.shift(period)


def rank(df: pd.DataFrame) -> pd.DataFrame:
    return df.rank(axis=1, pct=True, method="average")


def zscore(df: pd.DataFrame) -> pd.DataFrame:
    mean = df.mean(axis=1, skipna=True)
    std = df.std(axis=1, skipna=True)
    std = std.replace(0, np.nan)
    return (df.sub(mean, axis=0)).div(std, axis=0)


def log(df: pd.DataFrame) -> pd.DataFrame:
    return np.log(df.replace(0, np.nan).clip(lower=1e-10))


def abs_val(df: pd.DataFrame) -> pd.DataFrame:
    return df.abs()


def sign(df: pd.DataFrame) -> pd.DataFrame:
    return np.sign(df)


def max_val(df: pd.DataFrame, bound: float) -> pd.DataFrame:
    """Element-wise max: max(df, bound). For RSI-like factors."""
    return np.maximum(df, bound)


def min_val(df: pd.DataFrame, bound: float) -> pd.DataFrame:
    """Element-wise min: min(df, bound). For RSI-like factors."""
    return np.minimum(df, bound)


OPERATORS = {
    "ts_mean": ts_mean,
    "ts_std": ts_std,
    "ts_max": ts_max,
    "ts_min": ts_min,
    "delta": delta,
    "delay": delay,
    "rank": rank,
    "zscore": zscore,
    "log": log,
    "abs_val": abs_val,
    "sign": sign,
    "max_val": max_val,
    "min_val": min_val,
}

OPERATOR_DOCS = """
Available factor operators (use in expressions like rank(ts_mean(returns, 10))):

Time-series: ts_mean(df, window), ts_std(df, window), ts_max(df, window), ts_min(df, window),
  delta(df, period), delay(df, period)

Cross-sectional: rank(df), zscore(df)

Element-wise: log(df), abs_val(df), sign(df), max_val(df, bound), min_val(df, bound)

Variables: close, open, high, low, volume, returns
"""
