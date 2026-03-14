"""
Factor Lifecycle Management: re-evaluate factors when new data arrives.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

from data.market_data_loader import DataBundle
from engine.backtest import run_backtest
from engine.evaluator import evaluate_factor
from engine.factor_engine import FactorExpressionError, compute_factor
from rag.factor_vector_db import FactorDB

from core.config import OUTPUT_DIR


def re_evaluate_all_factors(
    data_bundle: DataBundle,
    factor_db: FactorDB,
    data_end_date: Optional[str] = None,
) -> List[dict]:
    """
    Re-evaluate all active factors. Compare with last stored metrics, compute decay ratio.
    Returns list of {expression, factor_id, ic_old, ic_new, decay_ratio, is_stable, ...}.
    """
    factors = factor_db.get_all(active_only=True)
    if not factors:
        return []

    data_end = data_end_date or str(data_bundle.close_df.index.max())[:10]
    results = []

    for f in factors:
        factor_id = f["id"]
        expression = f["expression"]
        ic_old = f.get("mean_ic")
        try:
            factor_df = compute_factor(expression, data_bundle)
            metrics = evaluate_factor(factor_df, data_bundle)
            bt = run_backtest(factor_df, data_bundle)
            metrics["sharpe"] = bt["sharpe"]
            metrics["max_drawdown"] = bt["max_drawdown"]
            metrics["turnover"] = bt["turnover"]

            factor_db.save_evaluation_history(factor_id, metrics, data_end)
            factor_db.update_factor(factor_id, metrics)

            ic_new = metrics.get("mean_ic")
            if ic_old is not None and ic_old != 0:
                decay_ratio = ic_new / abs(ic_old) if ic_new is not None else 0
            else:
                decay_ratio = 1.0
            is_stable = decay_ratio >= 0.5

            results.append({
                "expression": expression,
                "factor_id": factor_id,
                "ic_old": ic_old,
                "ic_new": ic_new,
                "decay_ratio": decay_ratio,
                "is_stable": is_stable,
                "sharpe_new": metrics.get("sharpe"),
            })
        except (FactorExpressionError, Exception) as e:
            results.append({
                "expression": expression,
                "factor_id": factor_id,
                "ic_old": ic_old,
                "ic_new": None,
                "decay_ratio": 0,
                "is_stable": False,
                "error": str(e),
            })

    return results


def flag_unstable_factors(
    factor_db: FactorDB,
    results: List[dict],
    decay_threshold: float = 0.5,
) -> int:
    """Mark factors with decay_ratio < threshold as inactive. Returns count deactivated."""
    count = 0
    for r in results:
        if r.get("decay_ratio", 1) < decay_threshold and "factor_id" in r:
            if factor_db.deactivate_factor(r["factor_id"]):
                count += 1
    return count


def save_reeval_results(results: List[dict], output_dir: Path = None) -> Path:
    """Save re-evaluation results to CSV. Returns path."""
    import pandas as pd

    output_dir = output_dir or OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d")
    path = output_dir / f"factor_reeval_{timestamp}.csv"
    df = pd.DataFrame(results)
    df.to_csv(path, index=False)
    return path
