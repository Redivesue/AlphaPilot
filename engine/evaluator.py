"""
Factor quality evaluation: IC, Rank IC, ICIR, IC decay, monotonicity test.
"""

import warnings
from typing import Any, Optional

import numpy as np
import pandas as pd

from core.config import IC_DECAY_HORIZONS, QUANTILE_GROUPS
from data.market_data_loader import DataBundle


def compute_ic(factor_df: pd.DataFrame, forward_returns_df: pd.DataFrame) -> pd.Series:
    common_idx = factor_df.index.intersection(forward_returns_df.index)
    factor_aligned = factor_df.loc[common_idx]
    returns_aligned = forward_returns_df.loc[common_idx]
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*constant.*")
        ic_series = factor_aligned.corrwith(returns_aligned, axis=1, method="pearson")
    return ic_series.dropna()


def compute_rank_ic(factor_df: pd.DataFrame, forward_returns_df: pd.DataFrame) -> pd.Series:
    common_idx = factor_df.index.intersection(forward_returns_df.index)
    factor_aligned = factor_df.loc[common_idx]
    returns_aligned = forward_returns_df.loc[common_idx]
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*constant.*")
        ic_series = factor_aligned.corrwith(returns_aligned, axis=1, method="spearman")
    return ic_series.dropna()


def compute_ic_decay(
    factor_df: pd.DataFrame,
    data_bundle: DataBundle,
    horizons: Optional[list] = None,
) -> dict:
    horizons = horizons or IC_DECAY_HORIZONS
    close = data_bundle.close_df
    result = {}
    for h in horizons:
        fwd_ret = close.shift(-h) / close - 1
        ic_s = compute_ic(factor_df, fwd_ret)
        result[h] = float(ic_s.mean()) if len(ic_s) > 0 else np.nan
    return result


def compute_monotonicity(
    factor_df: pd.DataFrame,
    forward_returns_df: pd.DataFrame,
    n_quantiles: int = QUANTILE_GROUPS,
) -> tuple:
    common_idx = factor_df.index.intersection(forward_returns_df.index)
    factor_aligned = factor_df.loc[common_idx].stack()
    returns_aligned = forward_returns_df.loc[common_idx].stack()
    valid = factor_aligned.notna() & returns_aligned.notna()
    factor_flat = factor_aligned[valid]
    returns_flat = returns_aligned[valid]
    if len(factor_flat) < n_quantiles * 2:
        return [], False
    quantiles = pd.qcut(factor_flat, n_quantiles, labels=False, duplicates="drop")
    mean_returns = returns_flat.groupby(quantiles).mean().tolist()
    if len(mean_returns) < 2:
        return mean_returns, False
    is_monotonic = all(mean_returns[i] <= mean_returns[i + 1] for i in range(len(mean_returns) - 1)) or all(
        mean_returns[i] >= mean_returns[i + 1] for i in range(len(mean_returns) - 1)
    )
    return mean_returns, is_monotonic


def evaluate_factor(
    factor_df: pd.DataFrame,
    data_bundle: DataBundle,
    horizons: Optional[list] = None,
) -> dict:
    horizons = horizons or IC_DECAY_HORIZONS
    fwd = data_bundle.forward_returns_df

    ic_series = compute_ic(factor_df, fwd)
    rank_ic_series = compute_rank_ic(factor_df, fwd)

    mean_ic = float(ic_series.mean()) if len(ic_series) > 0 else np.nan
    mean_rank_ic = float(rank_ic_series.mean()) if len(rank_ic_series) > 0 else np.nan
    ic_std = float(ic_series.std()) if len(ic_series) > 1 else 0.0
    icir = mean_ic / ic_std if ic_std > 0 else (np.nan if np.isnan(mean_ic) else 0.0)

    ic_decay = compute_ic_decay(factor_df, data_bundle, horizons)
    quantile_returns, is_monotonic = compute_monotonicity(factor_df, fwd)

    summary = (
        f"IC={mean_ic:.4f}, Rank_IC={mean_rank_ic:.4f}, ICIR={icir:.4f}. "
        f"IC_decay(1,5,10,20)={[round(ic_decay.get(h, np.nan), 4) for h in [1, 5, 10, 20]]}. "
        f"Monotonic={is_monotonic}."
    )

    return {
        "mean_ic": mean_ic,
        "mean_rank_ic": mean_rank_ic,
        "ic_std": ic_std,
        "icir": icir,
        "ic_decay": ic_decay,
        "quantile_returns": quantile_returns,
        "is_monotonic": is_monotonic,
        "n_obs": len(ic_series),
        "summary": summary,
    }
