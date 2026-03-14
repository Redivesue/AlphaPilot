"""
Data loader: download stock data via yfinance with rate limiting, cache, and build panel DataFrames.
"""

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd
import yfinance as yf

from core.config import CACHE_DIR, CACHE_FILE, END_DATE, START_DATE, TICKERS


@dataclass
class DataBundle:
    """Container for panel DataFrames (rows=dates, cols=tickers)."""

    close_df: pd.DataFrame
    open_df: pd.DataFrame
    high_df: pd.DataFrame
    low_df: pd.DataFrame
    volume_df: pd.DataFrame
    returns_df: pd.DataFrame
    forward_returns_df: pd.DataFrame
    forward_period: int


def _download_ticker(ticker: str, start: str, end: str, max_retries: int = 3) -> pd.DataFrame:
    """Download OHLCV for a single ticker, with retries on network failure."""
    for attempt in range(max_retries):
        try:
            data = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
            if data.empty:
                return pd.DataFrame()
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            required = ["Open", "High", "Low", "Close", "Volume"]
            available = [c for c in required if c in data.columns]
            if len(available) < 5:
                return pd.DataFrame()
            data = data[required]
            data.index = pd.to_datetime(data.index).tz_localize(None)
            return data
        except Exception as e:
            if attempt < max_retries - 1:
                wait = (2 ** attempt) * 3
                print(f"  Retry {ticker} in {wait}s (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(wait)
            else:
                print(f"  Skipped {ticker} after {max_retries} attempts: {e}")
                return pd.DataFrame()
    return pd.DataFrame()


def _build_panels(raw_data: dict, forward_period: int) -> DataBundle:
    """Build panel DataFrames from per-ticker raw data."""
    close_list = []
    open_list = []
    high_list = []
    low_list = []
    volume_list = []

    for ticker in raw_data:
        df = raw_data[ticker]
        if df.empty:
            continue
        close_list.append(df["Close"].rename(ticker))
        open_list.append(df["Open"].rename(ticker))
        high_list.append(df["High"].rename(ticker))
        low_list.append(df["Low"].rename(ticker))
        volume_list.append(df["Volume"].rename(ticker))

    close_df = pd.concat(close_list, axis=1)
    open_df = pd.concat(open_list, axis=1)
    high_df = pd.concat(high_list, axis=1)
    low_df = pd.concat(low_list, axis=1)
    volume_df = pd.concat(volume_list, axis=1)

    idx = close_df.index
    open_df = open_df.reindex(idx).ffill().bfill()
    high_df = high_df.reindex(idx).ffill().bfill()
    low_df = low_df.reindex(idx).ffill().bfill()
    volume_df = volume_df.reindex(idx).fillna(0)

    returns_df = close_df.pct_change()
    forward_returns_df = close_df.shift(-forward_period) / close_df - 1

    return DataBundle(
        close_df=close_df,
        open_df=open_df,
        high_df=high_df,
        low_df=low_df,
        volume_df=volume_df,
        returns_df=returns_df,
        forward_returns_df=forward_returns_df,
        forward_period=forward_period,
    )


def append_to_bundle(
    old_bundle: DataBundle,
    new_raw_data: dict,
    forward_period: Optional[int] = None,
) -> DataBundle:
    """Merge new per-ticker raw data into existing bundle. Drops duplicates, concatenates, rebuilds returns."""
    fp = forward_period or old_bundle.forward_period
    new_panels = _build_panels(new_raw_data, fp)
    if new_panels.close_df.empty:
        return old_bundle
    close_df = pd.concat([old_bundle.close_df, new_panels.close_df])
    close_df = close_df[~close_df.index.duplicated(keep="last")].sort_index()
    open_df = pd.concat([old_bundle.open_df, new_panels.open_df])
    open_df = open_df[~open_df.index.duplicated(keep="last")].sort_index().reindex(close_df.index).ffill().bfill()
    high_df = pd.concat([old_bundle.high_df, new_panels.high_df])
    high_df = high_df[~high_df.index.duplicated(keep="last")].sort_index().reindex(close_df.index).ffill().bfill()
    low_df = pd.concat([old_bundle.low_df, new_panels.low_df])
    low_df = low_df[~low_df.index.duplicated(keep="last")].sort_index().reindex(close_df.index).ffill().bfill()
    volume_df = pd.concat([old_bundle.volume_df, new_panels.volume_df])
    volume_df = volume_df[~volume_df.index.duplicated(keep="last")].sort_index().reindex(close_df.index).fillna(0)
    returns_df = close_df.pct_change()
    forward_returns_df = close_df.shift(-fp) / close_df - 1
    return DataBundle(
        close_df=close_df,
        open_df=open_df,
        high_df=high_df,
        low_df=low_df,
        volume_df=volume_df,
        returns_df=returns_df,
        forward_returns_df=forward_returns_df,
        forward_period=fp,
    )


def load_or_download_data(
    tickers: Optional[list] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    forward_period: int = 5,
    cache_dir: Optional[Path] = None,
    cache_file: Optional[Path] = None,
    force_download: bool = False,
) -> DataBundle:
    """Load data from cache or download via yfinance."""
    tickers = tickers or TICKERS
    start_date = start_date or START_DATE
    end_date = end_date or END_DATE
    cache_dir = cache_dir or CACHE_DIR
    cache_file = cache_file or CACHE_FILE

    if not force_download and cache_file.exists():
        try:
            bundle = pd.read_pickle(cache_file)
            if bundle.forward_period != forward_period:
                bundle.forward_returns_df = bundle.close_df.shift(-forward_period) / bundle.close_df - 1
                bundle.forward_period = forward_period
            return bundle
        except Exception:
            pass

    cache_dir.mkdir(parents=True, exist_ok=True)
    raw_data = {}

    for i, ticker in enumerate(tickers):
        if i > 0:
            time.sleep(3)
        df = _download_ticker(ticker, start_date, end_date)
        if not df.empty:
            raw_data[ticker] = df

    if not raw_data:
        raise RuntimeError(
            "No data downloaded. Check network/VPN. Try again or use cached data (remove --force-download)."
        )

    bundle = _build_panels(raw_data, forward_period)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    pd.to_pickle(bundle, cache_file)
    return bundle
