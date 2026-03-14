"""
Multi-agent task orchestrator for AlphaPilot V3.
"""

from typing import Any, Dict


class Orchestrator:
    """Coordinates multi-agent workflow: Planner -> Generator -> Evaluator -> Backtest -> Report."""

    def __init__(self, agents: Dict[str, Any], memory, config):
        self.planner = agents["planner"]
        self.generator = agents["generator"]
        self.evaluator = agents["evaluator"]
        self.backtester = agents["backtest"]
        self.reporter = agents["report"]
        self.memory = memory
        self.config = config

    def run(self, research_goal: str) -> Dict[str, Any]:
        """Execute full research pipeline."""
        self.memory.clear_short_term()
        self.memory.store("goal", research_goal)

        max_rounds = getattr(self.config, "max_rounds", 1)
        for round_num in range(max_rounds):
            # Step 1: Planner decomposes goal into tasks
            plan = self.planner.run({"goal": research_goal})
            tasks = plan.get("tasks", [])

            # Step 2: Execute tasks sequentially
            for task in tasks:
                task_type = task.get("type", "")
                try:
                    if task_type == "generate":
                        result = self.generator.run(task)
                        self.memory.store("candidates", result.get("expressions", []))

                    elif task_type == "evaluate":
                        result = self.evaluator.run(task)
                        self.memory.store("eval_results", result.get("eval_results", []))
                        self.memory.store("promising_factors", result.get("promising_factors", []))

                    elif task_type == "backtest":
                        result = self.backtester.run(task)
                        self.memory.store("bt_results", result.get("bt_results", []))

                    elif task_type == "report":
                        result = self.reporter.run({"goal": research_goal, **task})
                        self.memory.store("report", result.get("report", ""))
                        self.memory.store("report_path", result.get("path", ""))

                except Exception as e:
                    self.memory.log_action(task_type, "error", str(e))
                    # Continue with next task

        return self.memory.get_summary()
