"""Reports API: list, get content."""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse

from api.schemas import ReportListItem

router = APIRouter()

# Import from project
import sys

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from core.config import REPORT_OUTPUT_DIR


@router.get("", response_model=list[ReportListItem])
def list_reports():
    """List all report files."""
    if not REPORT_OUTPUT_DIR.exists():
        return []

    reports = []
    for f in sorted(REPORT_OUTPUT_DIR.glob("*.md"), reverse=True):
        stat = f.stat()
        from datetime import datetime

        created = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        reports.append(
            ReportListItem(
                filename=f.name,
                created_at=created,
                title=f.stem.replace("_", " ").title(),
            )
        )
    return reports


@router.get("/{filename}")
def get_report_content(filename: str):
    """Get report Markdown content."""
    if ".." in filename or "/" in filename:
        raise HTTPException(400, "Invalid filename")

    path = REPORT_OUTPUT_DIR / filename
    if not path.exists():
        raise HTTPException(404, "Report not found")

    return PlainTextResponse(content=path.read_text(encoding="utf-8"))


@router.get("/{filename}/download")
def download_report(filename: str):
    """Download report as file."""
    if ".." in filename or "/" in filename:
        raise HTTPException(400, "Invalid filename")

    path = REPORT_OUTPUT_DIR / filename
    if not path.exists():
        raise HTTPException(404, "Report not found")

    return FileResponse(path, filename=filename, media_type="text/markdown")
