"""
Data Update Service: incremental data refresh.
Checks last date in cache, downloads new data, appends to dataset.
"""

import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd

from core.config import CACHE_DIR, CACHE_FILE, DATA_UPDATE_END_DATE, TICKERS
from data.market_data_loader import (
    DataBundle,
    _download_ticker,
    append_to_bundle,
    load_or_download_data,
)


def get_last_date(bundle: DataBundle) -> Optional[date]:
    """Return max index date from close_df."""
    if bundle.close_df.empty:
        return None
    return pd.Timestamp(bundle.close_df.index.max()).date()


def update_data(
    tickers: Optional[list] = None,
    cache_file: Optional[Path] = None,
    end_date: Optional[str] = None,
    forward_period: int = 5,
) -> DataBundle:
    """
    Load cache, get last_date, download from last_date+1 to end_date,
    merge with existing, rebuild returns, save pickle.
    If no cache exists, fall back to full load_or_download_data.
    """
    tickers = tickers or TICKERS
    cache_file = cache_file or CACHE_FILE
    end_d = end_date or (DATA_UPDATE_END_DATE if DATA_UPDATE_END_DATE else str(date.today()))

    if not cache_file.exists():
        return load_or_download_data(
            tickers=tickers,
            end_date=end_d,
            forward_period=forward_period,
            cache_file=cache_file,
            force_download=False,
        )

    try:
        bundle = pd.read_pickle(cache_file)
    except Exception:
        return load_or_download_data(
            tickers=tickers,
            end_date=end_d,
            forward_period=forward_period,
            cache_file=cache_file,
            force_download=False,
        )

    last_d = get_last_date(bundle)
    if last_d is None:
        return load_or_download_data(
            tickers=tickers,
            end_date=end_d,
            forward_period=forward_period,
            cache_file=cache_file,
            force_download=False,
        )

    start_d = last_d + timedelta(days=1)
    start_str = start_d.strftime("%Y-%m-%d")
    if start_d >= datetime.strptime(end_d, "%Y-%m-%d").date():
        return bundle

    raw_data = {}
    for i, ticker in enumerate(tickers):
        if i > 0:
            time.sleep(3)
        df = _download_ticker(ticker, start_str, end_d)
        if not df.empty:
            raw_data[ticker] = df

    if not raw_data:
        return bundle

    new_bundle = append_to_bundle(bundle, raw_data, forward_period=forward_period)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    pd.to_pickle(new_bundle, cache_file)
    return new_bundle
