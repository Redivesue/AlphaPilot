"""
Planner Agent: decomposes research goal into ordered tasks.
"""

import json
import re
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage

from agents.base_agent import BaseAgent


class PlannerAgent(BaseAgent):
    """Decomposes research goal into task list: generate, evaluate, backtest, report."""

    def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        goal = task.get("goal", "Discover alpha factors with high IC and Sharpe")
        context = self.memory.get_context_summary()

        system_prompt = """You are a quantitative research planner. Given a research goal, output a JSON task plan.
Output ONLY valid JSON in this format (no markdown, no extra text):
{"tasks": [{"type": "generate", "constraints": "..."}, {"type": "evaluate", "note": "..."}, {"type": "backtest", "note": "..."}, {"type": "report", "note": "..."}]}

Task types: generate (create factor candidates), evaluate (compute IC metrics), backtest (run strategy backtest), report (generate research report).
Always include all four task types in order. The constraints/note fields can be brief."""

        user_prompt = f"""Research goal: {goal}

Current context: {context}

Output the JSON task plan:"""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
            response = self.llm.invoke(messages)
            content = response.content.strip()
            # Extract JSON if wrapped in markdown
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                content = json_match.group()
            plan = json.loads(content)
            if "tasks" not in plan:
                plan = {"tasks": [
                    {"type": "generate", "constraints": goal},
                    {"type": "evaluate", "note": "Evaluate IC for candidates"},
                    {"type": "backtest", "note": "Backtest promising factors"},
                    {"type": "report", "note": "Generate research report"},
                ]}
            return plan
        except (json.JSONDecodeError, Exception) as e:
            # Fallback default plan
            return {
                "tasks": [
                    {"type": "generate", "constraints": goal},
                    {"type": "evaluate", "note": "Evaluate IC for candidates"},
                    {"type": "backtest", "note": "Backtest promising factors"},
                    {"type": "report", "note": "Generate research report"},
                ]
            }
