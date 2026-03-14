"""
Report Agent: generates Markdown research reports.
"""

from typing import Any, Dict

from agents.base_agent import BaseAgent
from skills.report_generator import save_report
from skills.historical_factor_analysis import generate_similar_factors_analysis


class ReportAgent(BaseAgent):
    """Generates research report from memory context."""

    def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        research_goal = task.get("goal", "Alpha factor research")
        candidates = self.memory.recall("candidates") or []
        eval_results = self.memory.recall("eval_results") or []
        bt_results = self.memory.recall("bt_results") or []

        # Build factor_results text for report
        lines = []
        lines.append("## Factor Candidates")
        for e in candidates:
            lines.append(f"- {e}")

        lines.append("\n## Evaluation Results")
        for r in eval_results:
            lines.append(f"- {r.get('expression', '')}: {r.get('summary', '')}")

        lines.append("\n## Backtest Results")
        for r in bt_results:
            lines.append(f"- {r.get('expression', '')}: {r.get('summary', '')}")

        factor_results = "\n".join(lines)

        # Build RAG similar factors analysis for each candidate
        similar_parts = []
        factor_db = self.memory.factor_db
        for expr in candidates:
            f = factor_db.get_factor_by_expression(expr)
            metrics = {"mean_ic": f.get("mean_ic") if f else None}
            analysis = generate_similar_factors_analysis(expr, metrics, factor_db, top_k=5)
            similar_parts.append(f"### {expr}\n{analysis}")
        similar_factors_analysis = "\n\n".join(similar_parts) if similar_parts else None

        generate_report_fn = self.skills.get("generate_report")
        report_content = generate_report_fn(
            factor_results=factor_results,
            research_goal=research_goal,
            similar_factors_analysis=similar_factors_analysis,
        )

        path = save_report(report_content)
        self.memory.store("report", report_content)
        self.memory.store("report_path", str(path))
        self.memory.log_action("report", "generate", {"path": str(path)})
        return {"report": report_content, "path": str(path)}
