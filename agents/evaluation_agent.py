"""
Evaluation Agent: evaluates factors and interprets IC metrics.
"""

from typing import Any, Dict, List

from agents.base_agent import BaseAgent


class EvaluationAgent(BaseAgent):
    """Evaluates factor expressions: compute IC, run backtest, save to DB. Filters promising factors."""

    def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        candidates = self.memory.recall("candidates")
        if not candidates:
            return {"eval_results": [], "promising_factors": []}

        tools = self.skills.as_langchain_tools(["evaluate_factor_full"])
        evaluate_fn = self.skills.get("evaluate_factor_full")

        eval_results = []
        promising = []
        for expr in candidates:
            try:
                summary = evaluate_fn(expr)
                eval_results.append({"expression": expr, "summary": summary})
                # Simple heuristic: if summary contains reasonable numbers, consider promising
                if "Error" not in summary and "IC=" in summary:
                    promising.append(expr)
            except Exception as e:
                eval_results.append({"expression": expr, "summary": f"Error: {e}"})

        self.memory.store("eval_results", eval_results)
        self.memory.store("promising_factors", promising if promising else candidates[:3])
        self.memory.log_action("evaluator", "evaluate", {"count": len(eval_results), "promising": len(promising)})
        return {"eval_results": eval_results, "promising_factors": promising or candidates[:3]}
