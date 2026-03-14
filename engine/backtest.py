"""
Simple long-short backtest: rank by factor, long top 10%, short bottom 10%.
"""

from typing import Any, Optional

import numpy as np
import pandas as pd

from core.config import ANNUALIZE_FACTOR, BACKTEST_BOTTOM_PCT, BACKTEST_TOP_PCT
from data.market_data_loader import DataBundle


def run_backtest(
    factor_df: pd.DataFrame,
    data_bundle: DataBundle,
    top_pct: Optional[float] = None,
    bottom_pct: Optional[float] = None,
    annualize_factor: int = ANNUALIZE_FACTOR,
) -> dict[str, Any]:
    """
    Long top_pct, short bottom_pct by factor rank. Equal weight within each leg.
    Returns sharpe, max_drawdown, turnover, daily_returns.
    """
    top_pct = top_pct or BACKTEST_TOP_PCT
    bottom_pct = bottom_pct or BACKTEST_BOTTOM_PCT

    close = data_bundle.close_df
    returns = data_bundle.returns_df

    common_idx = factor_df.index.intersection(returns.index)
    factor_aligned = factor_df.loc[common_idx]
    returns_aligned = returns.loc[common_idx]

    n_dates = len(common_idx)
    n_stocks = factor_aligned.shape[1]

    daily_returns_list = []
    prev_long_mask = None
    prev_short_mask = None
    turnover_list = []

    for i in range(1, n_dates):
        factor_today = factor_aligned.iloc[i - 1]
        ret_today = returns_aligned.iloc[i]

        valid = factor_today.notna() & ret_today.notna()
        if valid.sum() < 3:
            daily_returns_list.append(0.0)
            turnover_list.append(0.0)
            continue

        factor_valid = factor_today[valid]
        ret_valid = ret_today[valid]

        n = len(factor_valid)
        n_long = max(1, int(n * top_pct))
        n_short = max(1, int(n * bottom_pct))

        ranked = factor_valid.rank(ascending=False)
        long_mask = ranked <= n_long
        short_mask = ranked > n - n_short

        long_ret = ret_valid[long_mask].mean()
        short_ret = ret_valid[short_mask].mean()
        port_ret = long_ret - short_ret
        daily_returns_list.append(port_ret)

        turnover = 0.0
        if prev_long_mask is not None and prev_short_mask is not None:
            common_tickers = set(long_mask.index) & set(prev_long_mask.index)
            if common_tickers:
                prev_l = prev_long_mask.reindex(common_tickers).fillna(False)
                curr_l = long_mask.reindex(common_tickers).fillna(False)
                turnover += (prev_l != curr_l).sum() / len(common_tickers)
                prev_s = prev_short_mask.reindex(common_tickers).fillna(False)
                curr_s = short_mask.reindex(common_tickers).fillna(False)
                turnover += (prev_s != curr_s).sum() / len(common_tickers)
        turnover_list.append(turnover)

        prev_long_mask = long_mask
        prev_short_mask = short_mask

    daily_returns = pd.Series(daily_returns_list, index=common_idx[1:])
    turnover_series = pd.Series(turnover_list, index=common_idx[1:])

    mean_ret = daily_returns.mean()
    std_ret = daily_returns.std()
    sharpe = (mean_ret / std_ret * np.sqrt(annualize_factor)) if std_ret > 0 else 0.0

    cumret = (1 + daily_returns).cumprod()
    running_max = cumret.cummax()
    drawdown = (cumret - running_max) / running_max
    max_drawdown = float(drawdown.min()) if len(drawdown) > 0 else 0.0

    turnover_mean = float(turnover_series.mean()) if len(turnover_series) > 0 else 0.0

    return {
        "sharpe": sharpe,
        "max_drawdown": max_drawdown,
        "turnover": turnover_mean,
        "daily_returns": daily_returns,
    }
