"""
Factor DB skills: search similar factors, list operators.
"""

from typing import Any

from engine.factor_operators import OPERATOR_DOCS
from rag.factor_vector_db import FactorDB


def create_search_factor_db_skill(factor_db: FactorDB):
    """Create search_similar_factors skill bound to factor_db."""

    def search_similar_factors(expression: str) -> str:
        """Search for similar factors already in the database.
        Call before trying new expressions to avoid duplicate research.
        Input: factor expression or idea. Returns top similar factors with IC, ICIR, Sharpe."""
        try:
            rows = factor_db.search_similar(expression, top_k=5)
            if not rows:
                return "No similar factors found in database."
            lines = []
            for i, r in enumerate(rows, 1):
                ic = r.get("mean_ic") or 0
                icir = r.get("icir") or 0
                sharpe = r.get("sharpe") or 0
                expr = r.get("expression", "")
                lines.append(f"{i}. {expr} | IC={ic:.4f}, ICIR={icir:.4f}, Sharpe={sharpe:.4f}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error: {type(e).__name__}: {e}"

    return search_similar_factors


def create_list_operators_skill():
    """Create list_operators skill (no dependencies)."""

    def list_operators(query: str = "") -> str:
        """List all available factor operators and variables.
        Call this to see syntax before writing expressions. Input can be empty."""
        return OPERATOR_DOCS

    return list_operators


def create_evaluate_and_store_skill(data_bundle, factor_db):
    """Create evaluate_factor_full skill: evaluate + backtest + store. Returns summary."""
    from engine.backtest import run_backtest
    from engine.evaluator import evaluate_factor
    from engine.factor_engine import FactorExpressionError, compute_factor

    def evaluate_factor_full(expression: str) -> str:
        """Evaluate a factor: compute IC metrics, run backtest, save to database.
        Input: factor expression. Returns IC, Rank IC, ICIR, Sharpe, Max drawdown, Turnover."""
        try:
            factor_df = compute_factor(expression, data_bundle)
            metrics = evaluate_factor(factor_df, data_bundle)
            bt = run_backtest(factor_df, data_bundle)
            metrics["sharpe"] = bt["sharpe"]
            metrics["max_drawdown"] = bt["max_drawdown"]
            metrics["turnover"] = bt["turnover"]
            metrics["summary"] = (
                metrics["summary"] + f" Sharpe={bt['sharpe']:.4f}, MDD={bt['max_drawdown']:.4f}, "
                f"Turnover={bt['turnover']:.4f}."
            )
            factor_db.save_factor(expression, metrics)
            return metrics["summary"]
        except FactorExpressionError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error: {type(e).__name__}: {e}"

    return evaluate_factor_full
