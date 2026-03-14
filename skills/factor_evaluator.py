"""
Factor evaluator skill: compute IC metrics for a factor.
"""

from data.market_data_loader import DataBundle
from engine.evaluator import evaluate_factor
from engine.factor_engine import FactorExpressionError, compute_factor


def create_evaluate_factor_skill(data_bundle: DataBundle):
    """Create evaluate_factor skill bound to data_bundle."""

    def evaluate_factor_skill(expression: str) -> str:
        """Evaluate a factor expression: compute IC, Rank IC, ICIR, decay, monotonicity.
        Input: factor expression like rank(ts_mean(returns, 10)).
        Returns metrics summary string."""
        try:
            factor_df = compute_factor(expression, data_bundle)
            metrics = evaluate_factor(factor_df, data_bundle)
            return metrics["summary"]
        except FactorExpressionError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error: {type(e).__name__}: {e}"

    return evaluate_factor_skill
