"""Agent API: run research pipeline, WebSocket for real-time logs."""

import asyncio
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException, WebSocket, WebSocketDisconnect

from api.deps import get_state
from api.schemas import AgentRunRequest, AgentStatusResponse

router = APIRouter()


def _run_research_pipeline(req: AgentRunRequest) -> None:
    """Run orchestrator in sync context (blocking)."""
    state = get_state()
    state.agent_running = True
    try:
        state._log_system("Agent pipeline started")
        state.ensure_llm_and_agents()

        if req.tickers:
            state.config.tickers = req.tickers
        if req.start_date:
            state.config.start_date = req.start_date
        if req.end_date:
            state.config.end_date = req.end_date
        if req.max_rounds is not None:
            state.config.max_rounds = req.max_rounds

        goal = req.research_goal or "Discover alpha factors with high IC, ICIR, and Sharpe."
        result = state.orchestrator.run(goal)
        state._log_system(f"Agent pipeline completed: {result.get('research_log_count', 0)} actions logged")
    except Exception as e:
        state._log_system(f"Agent pipeline error: {e}")
        state.log_agent_action("orchestrator", "error", str(e))
    finally:
        state.agent_running = False


@router.post("/run")
async def run_agent(req: AgentRunRequest, background_tasks: BackgroundTasks):
    """Start research pipeline in background."""
    state = get_state()
    if state.agent_running:
        raise HTTPException(409, "Agent already running")

    if state.data_bundle is None:
        raise HTTPException(503, "Data not loaded. Check data cache or run data update.")

    async def run_pipeline_task():
        await asyncio.to_thread(_run_research_pipeline, req)

    background_tasks.add_task(run_pipeline_task)
    return {"status": "started", "message": "Research pipeline started. Connect to WebSocket for logs."}


@router.get("/status", response_model=AgentStatusResponse)
def get_agent_status():
    """Check if agent is running."""
    state = get_state()
    return AgentStatusResponse(
        running=state.agent_running,
        message="Running" if state.agent_running else "Idle",
    )


@router.websocket("/ws")
async def agent_websocket(websocket: WebSocket):
    """Stream real-time agent logs via WebSocket."""
    await websocket.accept()
    state = get_state()
    try:
        while True:
            try:
                while not state.agent_log_queue.empty():
                    log = state.agent_log_queue.get_nowait()
                    await websocket.send_json(log)
                await asyncio.sleep(0.3)
            except WebSocketDisconnect:
                break
    except Exception:
        pass
