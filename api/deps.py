"""Shared application state and dependencies for AlphaPilot API."""

import os
import sys
from pathlib import Path
from queue import Queue
from threading import Lock
from typing import Any, Optional

# Ensure project root is in path when running from api/
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(_PROJECT_ROOT / ".env")

from core.config import Config
from data.market_data_loader import DataBundle, load_or_download_data
from rag.factor_vector_db import FactorDB


class AppState:
    """Singleton application state: DataBundle, FactorDB, LLM, logs."""

    _instance: Optional["AppState"] = None
    _lock = Lock()

    def __new__(cls) -> "AppState":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = False
        self.data_bundle: Optional[DataBundle] = None
        self.factor_db: Optional[FactorDB] = None
        self.config: Optional[Config] = None
        self.llm = None
        self.skill_registry = None
        self.agents = None
        self.orchestrator = None
        self.system_logs: list[dict] = []
        self.agent_running: bool = False
        self.agent_log_queue: Queue = Queue()
        self._log_lock = Lock()

    def initialize(
        self,
        data_bundle: Optional[DataBundle] = None,
        force_load: bool = False,
    ) -> None:
        """Load data, FactorDB, and optionally LLM/agents. Call from lifespan."""
        if self._initialized and not force_load:
            return

        self.config = Config()
        self.factor_db = FactorDB()

        if data_bundle is not None:
            self.data_bundle = data_bundle
        else:
            try:
                self.data_bundle = load_or_download_data(
                    tickers=self.config.tickers,
                    start_date=self.config.start_date,
                    end_date=self.config.end_date,
                    forward_period=self.config.forward_return_period,
                )
            except Exception as e:
                self._log_system(f"Data load failed: {e}")
                self.data_bundle = None

        # Lazy-load LLM and agents on first agent run to avoid slow startup
        self._initialized = True
        self._log_system("AppState initialized")

    def _log_system(self, message: str) -> None:
        from datetime import datetime

        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "agent": "system",
            "action": "log",
            "result": message,
        }
        with self._log_lock:
            self.system_logs.append(entry)
        self.agent_log_queue.put(entry)

    def log_agent_action(self, agent: str, action: str, result: Any) -> None:
        """Called by Memory when an agent performs an action."""
        from datetime import datetime

        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "agent": agent,
            "action": action,
            "result": str(result) if not isinstance(result, (str, int, float, type(None))) else result,
        }
        with self._log_lock:
            self.system_logs.append(entry)
        self.agent_log_queue.put(entry)

    def ensure_llm_and_agents(self) -> None:
        """Lazy-initialize LLM, skills, and agents when needed."""
        if self.llm is not None:
            return
        from core.llm import get_llm
        from core.memory import Memory
        from core.orchestrator import Orchestrator
        from skills.registry import SkillRegistry
        from skills.factor_generator import create_generate_factor_skill
        from skills.factor_evaluator import create_evaluate_factor_skill
        from skills.backtester import create_backtest_skill
        from skills.report_generator import create_report_skill
        from skills.factor_db_skills import (
            create_search_factor_db_skill,
            create_list_operators_skill,
            create_evaluate_and_store_skill,
        )
        from agents.planner_agent import PlannerAgent
        from agents.generator_agent import GeneratorAgent
        from agents.evaluation_agent import EvaluationAgent
        from agents.backtest_agent import BacktestAgent
        from agents.report_agent import ReportAgent

        api_key = (self.config.openai_api_key or os.environ.get("OPENAI_API_KEY") or "").strip().strip('"\'')
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set. Add it to .env")

        self.llm = get_llm(self.config)
        memory = Memory(self.factor_db)
        memory.set_log_callback(self.log_agent_action)

        registry = SkillRegistry()
        registry.register(
            "generate_factor",
            create_generate_factor_skill(self.data_bundle),
            "Compute a factor from an expression.",
        )
        registry.register(
            "search_similar_factors",
            create_search_factor_db_skill(self.factor_db),
            "Search for similar factors in database.",
        )
        registry.register(
            "list_operators",
            create_list_operators_skill(),
            "List all factor operators and variables.",
        )
        registry.register(
            "evaluate_factor_full",
            create_evaluate_and_store_skill(self.data_bundle, self.factor_db),
            "Evaluate factor: IC, backtest, save to DB.",
        )
        registry.register(
            "backtest_strategy",
            create_backtest_skill(self.data_bundle),
            "Run long-short backtest for a factor.",
        )
        registry.register(
            "generate_report",
            create_report_skill(self.llm),
            "Generate Markdown research report.",
        )

        self.skill_registry = registry
        self.agents = {
            "planner": PlannerAgent("planner", self.llm, memory, registry),
            "generator": GeneratorAgent("generator", self.llm, memory, registry, self.config),
            "evaluator": EvaluationAgent("evaluator", self.llm, memory, registry),
            "backtest": BacktestAgent("backtest", self.llm, memory, registry),
            "report": ReportAgent("report", self.llm, memory, registry),
        }
        self.orchestrator = Orchestrator(self.agents, memory, self.config)
        self._memory = memory


def get_state() -> AppState:
    return AppState()
