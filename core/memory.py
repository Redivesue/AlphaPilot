"""
Memory system for AlphaPilot V3: short-term session state + long-term Factor DB.
"""

from typing import Any, Callable, List, Optional


class Memory:
    """Two-tier memory: short-term (session) and long-term (Factor DB)."""

    def __init__(self, factor_db):
        self.short_term: dict = {}
        self.research_log: List[dict] = []
        self.factor_db = factor_db
        self._log_callback: Optional[Callable[[str, str, Any], None]] = None

    def set_log_callback(self, callback: Callable[[str, str, Any], None]) -> None:
        """Set callback for real-time log streaming (e.g., to WebSocket)."""
        self._log_callback = callback

    def store(self, key: str, value: Any) -> None:
        """Store value in short-term memory."""
        self.short_term[key] = value

    def recall(self, key: str) -> Optional[Any]:
        """Recall value from short-term memory."""
        return self.short_term.get(key)

    def log_action(self, agent: str, action: str, result: Any) -> None:
        """Log an agent action for auditability."""
        entry = {
            "agent": agent,
            "action": action,
            "result": result,
        }
        self.research_log.append(entry)
        if self._log_callback:
            try:
                self._log_callback(agent, action, result)
            except Exception:
                pass

    def get_context_summary(self) -> str:
        """Get a text summary of current context for agents."""
        parts = []
        if self.short_term.get("candidates"):
            parts.append(f"Candidates: {len(self.short_term['candidates'])} factors")
        if self.short_term.get("eval_results"):
            parts.append(f"Evaluation results: {len(self.short_term['eval_results'])} factors")
        if self.short_term.get("promising_factors"):
            parts.append(f"Promising factors: {len(self.short_term['promising_factors'])}")
        if self.short_term.get("bt_results"):
            parts.append(f"Backtest results: {len(self.short_term['bt_results'])} factors")
        if not parts:
            return "No research context yet."
        return "; ".join(parts)

    def get_summary(self) -> dict:
        """Get full summary of research session."""
        return {
            "short_term": dict(self.short_term),
            "research_log_count": len(self.research_log),
            "report": self.short_term.get("report"),
        }

    def clear_short_term(self) -> None:
        """Clear short-term memory (e.g., between research runs)."""
        self.short_term.clear()
        self.research_log.clear()
