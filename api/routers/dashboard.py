"""Dashboard API: stats and chart data."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException

from api.deps import get_state
from api.schemas import DashboardStats

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats():
    """Active factors, avg IC, best Sharpe, last data update."""
    state = get_state()
    if state.factor_db is None:
        raise HTTPException(503, "Factor DB not initialized")

    factors = state.factor_db.get_all(active_only=True)
    active = len(factors)

    ic_vals = [f.get("mean_ic") for f in factors if f.get("mean_ic") is not None]
    avg_ic = sum(ic_vals) / len(ic_vals) if ic_vals else 0.0

    sharpe_vals = [f.get("sharpe") for f in factors if f.get("sharpe") is not None]
    best_sharpe = max(sharpe_vals) if sharpe_vals else 0.0

    last_update = None
    if state.data_bundle is not None and not state.data_bundle.close_df.empty:
        last_update = str(state.data_bundle.close_df.index.max())[:10]

    return DashboardStats(
        active_factors=active,
        average_ic=round(avg_ic, 4),
        best_sharpe=round(best_sharpe, 2),
        last_data_update=last_update,
    )


@router.get("/charts")
def get_dashboard_charts():
    """IC distribution, factor performance, equity curve preview, Sharpe ranking."""
    state = get_state()
    if state.factor_db is None or state.data_bundle is None:
        return {
            "ic_distribution": {"x": [], "y": []},
            "factor_performance": {"factors": [], "sharpe": []},
            "equity_curve": {"dates": [], "values": []},
            "sharpe_ranking": {"factors": [], "sharpe": []},
        }

    from engine.backtest import run_backtest
    from engine.evaluator import compute_ic
    from engine.factor_engine import compute_factor

    factors = state.factor_db.get_top_factors(metric="sharpe", n=20)
    bundle = state.data_bundle

    # IC distribution: sample from top factor's IC series
    ic_distribution = {"x": [], "y": []}
    if factors:
        try:
            import numpy as np

            top_expr = factors[0].get("expression")
            if top_expr:
                factor_df = compute_factor(top_expr, bundle)
                ic_series = compute_ic(factor_df, bundle.forward_returns_df)
                hist, bin_edges = np.histogram(ic_series.dropna(), bins=30)
                ic_distribution = {"x": bin_edges[:-1].tolist(), "y": hist.tolist()}
        except Exception:
            pass

    # Factor performance (Sharpe bar chart)
    factor_performance = {
        "factors": [f.get("expression", "")[:40] + "..." if len(f.get("expression", "")) > 40 else f.get("expression", "") for f in factors],
        "sharpe": [round(f.get("sharpe") or 0, 2) for f in factors],
    }

    # Equity curve: backtest top factor
    equity_curve = {"dates": [], "values": []}
    if factors:
        try:
            top_expr = factors[0].get("expression")
            if top_expr:
                factor_df = compute_factor(top_expr, bundle)
                bt = run_backtest(factor_df, bundle)
                dr = bt.get("daily_returns")
                if dr is not None and len(dr) > 0:
                    cum = (1 + dr).cumprod()
                    equity_curve = {
                        "dates": [str(i)[:10] for i in cum.index.tolist()],
                        "values": cum.tolist(),
                    }
        except Exception:
            pass

    # Sharpe ranking (same as factor_performance, sorted)
    sharpe_ranking = {
        "factors": factor_performance["factors"],
        "sharpe": factor_performance["sharpe"],
    }

    return {
        "ic_distribution": ic_distribution,
        "factor_performance": factor_performance,
        "equity_curve": equity_curve,
        "sharpe_ranking": sharpe_ranking,
    }
