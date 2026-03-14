"""
Factor generator skill: compute factor from expression.
"""

from typing import Any

from data.market_data_loader import DataBundle
from engine.factor_engine import FactorExpressionError, compute_factor


def create_generate_factor_skill(data_bundle: DataBundle):
    """Create generate_factor skill bound to data_bundle."""

    def generate_factor(expression: str) -> str:
        """Compute a factor from an expression. Input: factor expression like rank(ts_mean(returns, 10)).
        Returns success message with shape info, or error string."""
        try:
            factor_df = compute_factor(expression, data_bundle)
            shape = factor_df.shape
            return f"Success: factor computed, shape {shape[0]} dates x {shape[1]} tickers."
        except FactorExpressionError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error: {type(e).__name__}: {e}"

    return generate_factor
