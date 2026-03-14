"""System logs API."""

from fastapi import APIRouter, Query

from api.deps import get_state
from api.schemas import LogEntry

router = APIRouter()


@router.get("", response_model=list[LogEntry])
def get_logs(limit: int = Query(200, le=1000)):
    """Get system logs."""
    state = get_state()
    logs = state.system_logs[-limit:]
    return [
        LogEntry(
            timestamp=l.get("timestamp", ""),
            agent=l.get("agent"),
            action=l.get("action", ""),
            result=l.get("result"),
        )
        for l in logs
    ]
