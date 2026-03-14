"""
Backtest Agent: runs backtest and interprets performance.
"""

from typing import Any, Dict, List

from agents.base_agent import BaseAgent


class BacktestAgent(BaseAgent):
    """Runs backtest for promising factors. Results already in DB from evaluate_factor_full."""

    def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        promising = self.memory.recall("promising_factors")
        if not promising:
            promising = self.memory.recall("candidates") or []

        backtest_fn = self.skills.get("backtest_strategy")
        bt_results = []
        for expr in promising:
            try:
                summary = backtest_fn(expr)
                bt_results.append({"expression": expr, "summary": summary})
            except Exception as e:
                bt_results.append({"expression": expr, "summary": f"Error: {e}"})

        self.memory.store("bt_results", bt_results)
        self.memory.log_action("backtest", "backtest", {"count": len(bt_results)})
        return {"bt_results": bt_results}
