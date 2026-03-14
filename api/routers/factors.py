"""Factors API: list, detail, deactivate."""

from fastapi import APIRouter, HTTPException, Query

from api.deps import get_state
from api.schemas import FactorDetail, FactorListItem

router = APIRouter()


@router.get("", response_model=list[FactorListItem])
def list_factors(
    active_only: bool = Query(False),
    sort_by: str = Query("created_at"),
    limit: int = Query(100, le=500),
):
    """List all factors with optional filter and sort."""
    state = get_state()
    if state.factor_db is None:
        raise HTTPException(503, "Factor DB not initialized")

    factors = state.factor_db.get_all(active_only=active_only)
    if sort_by == "sharpe":
        factors = sorted(factors, key=lambda f: (f.get("sharpe") or 0), reverse=True)
    elif sort_by == "mean_ic":
        factors = sorted(factors, key=lambda f: abs(f.get("mean_ic") or 0), reverse=True)
    elif sort_by == "icir":
        factors = sorted(factors, key=lambda f: (f.get("icir") or 0), reverse=True)
    else:
        factors = sorted(factors, key=lambda f: f.get("created_at") or "", reverse=True)

    factors = factors[:limit]
    return [
        FactorListItem(
            id=f["id"],
            expression=f.get("expression", ""),
            mean_ic=f.get("mean_ic"),
            mean_rank_ic=f.get("mean_rank_ic"),
            icir=f.get("icir"),
            sharpe=f.get("sharpe"),
            max_drawdown=f.get("max_drawdown"),
            turnover=f.get("turnover"),
            is_active=bool(f.get("is_active", 1)),
            created_at=f.get("created_at"),
        )
        for f in factors
    ]


@router.get("/{factor_id}", response_model=FactorDetail)
def get_factor_detail(factor_id: str):
    """Get factor detail: metrics, IC decay, similar factors, eval history."""
    state = get_state()
    if state.factor_db is None:
        raise HTTPException(503, "Factor DB not initialized")

    import sqlite3

    conn_obj = sqlite3.connect(state.factor_db.db_path)
    conn_obj.row_factory = sqlite3.Row
    cur = conn_obj.execute(
        "SELECT id, expression, mean_ic, mean_rank_ic, icir, sharpe, max_drawdown, turnover, is_active, created_at "
        "FROM factors WHERE id = ?",
        (factor_id,),
    )
    row = cur.fetchone()
    conn_obj.close()

    if row is None:
        raise HTTPException(404, "Factor not found")

    f = dict(row)
    expression = f.get("expression", "")

    # IC decay
    ic_decay = None
    if state.data_bundle and expression:
        try:
            from engine.evaluator import compute_ic_decay
            from engine.factor_engine import compute_factor

            factor_df = compute_factor(expression, state.data_bundle)
            ic_decay = compute_ic_decay(factor_df, state.data_bundle)
        except Exception:
            pass

    # Similar factors (RAG)
    similar = state.factor_db.search_similar(expression, top_k=5)
    similar_factors = [
        {"expression": s.get("expression"), "mean_ic": s.get("mean_ic"), "sharpe": s.get("sharpe")}
        for s in similar
        if s.get("id") != factor_id
    ][:5]

    # Eval history
    eval_history = state.factor_db.get_factor_evaluation_history(factor_id)

    return FactorDetail(
        id=f["id"],
        expression=expression,
        mean_ic=f.get("mean_ic"),
        mean_rank_ic=f.get("mean_rank_ic"),
        icir=f.get("icir"),
        sharpe=f.get("sharpe"),
        max_drawdown=f.get("max_drawdown"),
        turnover=f.get("turnover"),
        is_active=bool(f.get("is_active", 1)),
        created_at=f.get("created_at"),
        ic_decay=ic_decay,
        similar_factors=similar_factors,
        eval_history=eval_history,
    )


@router.post("/{factor_id}/deactivate")
def deactivate_factor(factor_id: str):
    """Deactivate a factor."""
    state = get_state()
    if state.factor_db is None:
        raise HTTPException(503, "Factor DB not initialized")

    ok = state.factor_db.deactivate_factor(factor_id)
    if not ok:
        raise HTTPException(404, "Factor not found")
    return {"status": "deactivated"}
