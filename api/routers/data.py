"""Data API: status, update."""

import sys
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from api.deps import get_state
from api.schemas import DataStatusResponse, DataUpdateRequest

router = APIRouter()


@router.get("/status", response_model=DataStatusResponse)
def get_data_status():
    """Current data range, tickers, last update."""
    state = get_state()
    from core.config import Config

    cfg = state.config if state.config else Config()

    if state.data_bundle is None:
        try:
            state.initialize()
        except Exception:
            pass

    if state.data_bundle is None:
        return DataStatusResponse(
            start_date=cfg.start_date,
            end_date=cfg.end_date,
            tickers=cfg.tickers,
            n_days=0,
            n_tickers=0,
            last_update=None,
        )

    bundle = state.data_bundle
    return DataStatusResponse(
        start_date=str(bundle.close_df.index.min())[:10],
        end_date=str(bundle.close_df.index.max())[:10],
        tickers=list(bundle.close_df.columns),
        n_days=len(bundle.close_df),
        n_tickers=len(bundle.close_df.columns),
        last_update=str(bundle.close_df.index.max())[:10],
    )


@router.post("/update")
def update_data(req: DataUpdateRequest):
    """Trigger data download and optional re-evaluation."""
    state = get_state()
    from core.config import TICKERS
    from data_pipeline.data_updater import update_data as incremental_update
    from core.factor_lifecycle import re_evaluate_all_factors, flag_unstable_factors, save_reeval_results

    cfg = state.config
    tickers = list(cfg.tickers) if cfg else list(TICKERS)
    start_date = cfg.start_date if cfg else "2015-01-01"
    end_date = cfg.end_date if cfg else "2024-01-01"

    if req.tickers_to_add:
        tickers = list(set(tickers) | set(req.tickers_to_add))
    if req.start_date:
        start_date = req.start_date
    if req.end_date:
        end_date = req.end_date

    try:
        bundle = incremental_update(
            tickers=tickers,
            end_date=end_date,
            forward_period=cfg.forward_return_period if cfg else 5,
        )
        state.data_bundle = bundle
        state.config.tickers = tickers
        state.config.start_date = start_date
        state.config.end_date = end_date

        if req.re_evaluate and state.factor_db:
            reeval_results = re_evaluate_all_factors(bundle, state.factor_db)
            if reeval_results:
                flag_unstable_factors(state.factor_db, reeval_results, decay_threshold=0.5)
                save_reeval_results(reeval_results)
                return {
                    "status": "ok",
                    "message": f"Data updated. Re-evaluated {len(reeval_results)} factors.",
                    "n_days": len(bundle.close_df),
                    "n_tickers": len(bundle.close_df.columns),
                }

        return {
            "status": "ok",
            "message": "Data updated.",
            "n_days": len(bundle.close_df),
            "n_tickers": len(bundle.close_df.columns),
        }
    except Exception as e:
        raise HTTPException(500, str(e))
