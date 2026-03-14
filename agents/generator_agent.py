"""
Generator Agent: generates factor expressions via LLM.
"""

from typing import Any, Dict, List

from langchain.agents import AgentExecutor, create_react_agent
from langchain import hub
from langchain_core.prompts import PromptTemplate

from agents.base_agent import BaseAgent


class GeneratorAgent(BaseAgent):
    """Generates factor expressions using LLM + tools (generate_factor, search_similar_factors, list_operators)."""

    def __init__(self, name: str, llm, memory, skills, config):
        super().__init__(name, llm, memory, skills)
        self.config = config

    def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        constraints = task.get("constraints", "Discover alpha factors with high IC and Sharpe")
        n_factors = task.get("n_factors", 3)

        tools = self.skills.as_langchain_tools(
            ["generate_factor", "search_similar_factors", "list_operators"]
        )

        try:
            prompt = hub.pull("hwchase17/react")
        except Exception:
            prompt = PromptTemplate.from_template(
                """Answer the following questions. You have access to these tools:

{tools}

Use this format:
Question: the input question
Thought: think step by step
Action: one of [{tool_names}]
Action Input: the input
Observation: the result
... (repeat as needed)
Thought: I now know the final answer
Final Answer: the final answer

Question: {input}
Thought: {agent_scratchpad}"""
            )

        agent = create_react_agent(self.llm, tools, prompt)
        executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=self.config.max_iterations,
            handle_parsing_errors=True,
        )

        user_task = (
            f"Generate {n_factors} factor expressions. Constraints: {constraints}. "
            "Call list_operators first to see syntax. Call search_similar_factors to avoid duplicates. "
            "Use generate_factor to validate each expression. "
            "Output the final list of valid expressions in your Final Answer, one per line."
        )

        result = executor.invoke({"input": user_task})
        output = result.get("output", "")

        # Parse expressions from output (lines that look like factor expressions)
        expressions = []
        for line in output.split("\n"):
            line = line.strip()
            if line and ("rank(" in line or "ts_mean(" in line or "ts_std(" in line or "zscore(" in line):
                # Extract expression (remove numbering, bullets)
                expr = line.lstrip("0123456789.-) ")
                if expr and len(expr) > 5:
                    expressions.append(expr)

        if not expressions:
            # Fallback: try common expressions
            expressions = [
                "rank(ts_mean(returns, 10))",
                "rank(ts_std(returns, 10))",
                "rank(ts_mean(volume, 20))",
            ]

        self.memory.store("candidates", expressions)
        self.memory.log_action("generator", "generate", {"expressions": expressions})
        return {"expressions": expressions, "output": output}
