"""Backtest API: run backtest, return Plotly-ready data."""

from fastapi import APIRouter, HTTPException

from api.deps import get_state
from api.schemas import BacktestRequest, BacktestResult

router = APIRouter()


@router.post("/run", response_model=BacktestResult)
def run_backtest(req: BacktestRequest):
    """Run backtest for a factor expression."""
    state = get_state()
    if state.data_bundle is None:
        raise HTTPException(503, "Data not loaded")

    from engine.backtest import run_backtest as _run_backtest
    from engine.factor_engine import FactorExpressionError, compute_factor

    try:
        factor_df = compute_factor(req.factor_expression, state.data_bundle)
        bt = _run_backtest(
            factor_df,
            state.data_bundle,
            top_pct=req.top_pct,
            bottom_pct=req.bottom_pct,
        )
    except FactorExpressionError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))

    daily_returns = bt.get("daily_returns")
    if daily_returns is None or len(daily_returns) == 0:
        return BacktestResult(
            sharpe=bt.get("sharpe", 0),
            max_drawdown=bt.get("max_drawdown", 0),
            turnover=bt.get("turnover"),
            daily_returns=[],
            drawdown_series=[],
            monthly_heatmap=None,
        )

    import numpy as np
    import pandas as pd

    dr = daily_returns
    cum = (1 + dr).cumprod()
    running_max = cum.cummax()
    drawdown = (cum - running_max) / running_max

    daily_returns_list = [{"date": str(i)[:10], "value": float(v)} for i, v in dr.items()]
    drawdown_list = [{"date": str(i)[:10], "value": float(v)} for i, v in drawdown.items()]

    # Annual return
    n_years = len(dr) / 252.0 if len(dr) > 0 else 1
    total_ret = float(cum.iloc[-1]) - 1 if len(cum) > 0 else 0
    annual_return = (1 + total_ret) ** (1 / n_years) - 1 if n_years > 0 else 0

    # Monthly heatmap: {years: [], months: [], values: [[...]]}
    monthly_heatmap = None
    try:
        dr_series = pd.Series(dr)
        dr_series.index = pd.to_datetime(dr_series.index)
        monthly = dr_series.resample("ME").sum()
        pivot = monthly.groupby([monthly.index.year, monthly.index.month]).sum().unstack(fill_value=0)
        years = pivot.index.tolist()
        months = pivot.columns.tolist()
        values = pivot.values.tolist()
        monthly_heatmap = {"years": years, "months": months, "values": values}
    except Exception:
        pass

    return BacktestResult(
        sharpe=round(bt.get("sharpe", 0), 4),
        max_drawdown=round(bt.get("max_drawdown", 0), 4),
        annual_return=round(annual_return, 4),
        turnover=round(bt.get("turnover", 0), 4) if bt.get("turnover") is not None else None,
        daily_returns=daily_returns_list,
        drawdown_series=drawdown_list,
        monthly_heatmap=monthly_heatmap,
    )
