"""
Base agent for AlphaPilot V3.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAgent(ABC):
    """Base class for all agents with shared LLM and memory access."""

    def __init__(self, name: str, llm, memory, skills):
        self.name = name
        self.llm = llm
        self.memory = memory
        self.skills = skills

    @abstractmethod
    def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent task. Returns result dict."""
        pass
