"""
Backtest skill: run long-short backtest for a factor.
"""

from data.market_data_loader import DataBundle
from engine.backtest import run_backtest
from engine.factor_engine import FactorExpressionError, compute_factor


def create_backtest_skill(data_bundle: DataBundle):
    """Create backtest_strategy skill bound to data_bundle."""

    def backtest_strategy(expression: str) -> str:
        """Run long-short backtest for a factor expression.
        Input: factor expression like rank(ts_mean(returns, 10)).
        Returns Sharpe, Max drawdown, Turnover."""
        try:
            factor_df = compute_factor(expression, data_bundle)
            bt = run_backtest(factor_df, data_bundle)
            return (
                f"Sharpe={bt['sharpe']:.4f}, MaxDrawdown={bt['max_drawdown']:.4f}, "
                f"Turnover={bt['turnover']:.4f}."
            )
        except FactorExpressionError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error: {type(e).__name__}: {e}"

    return backtest_strategy
