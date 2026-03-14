"""
Skill registry: maps skill names to callables, provides LangChain tools.
"""

from typing import Callable, List

from langchain_core.tools import StructuredTool, tool


class SkillRegistry:
    """Registry mapping skill names to callables with metadata."""

    def __init__(self):
        self._skills: dict = {}  # name -> {"func": callable, "description": str}

    def register(self, name: str, func: Callable, description: str) -> None:
        """Register a skill."""
        self._skills[name] = {"func": func, "description": description}

    def get(self, name: str) -> Callable:
        """Get skill callable by name."""
        if name not in self._skills:
            raise KeyError(f"Unknown skill: {name}")
        return self._skills[name]["func"]

    def list_skills(self) -> List[dict]:
        """List all registered skills with metadata."""
        return [
            {"name": name, "description": info["description"]}
            for name, info in self._skills.items()
        ]

    def as_langchain_tools(self, skill_names: List[str] = None) -> List:
        """Convert registered skills to LangChain tools. If skill_names given, only those."""
        names = skill_names or list(self._skills.keys())
        tools = []
        for name in names:
            if name not in self._skills:
                continue
            info = self._skills[name]
            func = info["func"]
            desc = info["description"]
            # Wrap as LangChain tool
            tools.append(StructuredTool.from_function(
                func=func,
                name=name,
                description=desc,
            ))
        return tools
