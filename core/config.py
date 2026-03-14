"""
Configuration for AlphaPilot V3.
Extends V2 config with V3-specific settings.
"""

import os
from dataclasses import dataclass
from pathlib import Path

# Base directory: AlphaPilot/
BASE_DIR = Path(__file__).resolve().parent.parent

# Stock pool: US tech + large cap
TICKERS = [
    "AAPL", "MSFT", "AMZN", "GOOGL", "META",
    "NVDA", "TSLA", "NFLX", "INTC", "AMD",
    "JPM", "BAC", "GS", "WMT", "COST",
    "DIS", "PEP", "KO", "MCD", "NKE",
]

# Time range
START_DATE = "2015-01-01"
END_DATE = "2024-01-01"

# Data cache (reuse V1 cache if exists)
_v1_cache = BASE_DIR.parent / "alpha_research_v1" / "data_cache" / "market_data.pkl"
_cache_dir = BASE_DIR / "data_cache"
CACHE_DIR = _v1_cache.parent if _v1_cache.exists() else _cache_dir
CACHE_FILE = CACHE_DIR / "market_data.pkl"

# Factor evaluation
FORWARD_RETURN_PERIOD = 5
IC_DECAY_HORIZONS = [1, 3, 5, 10, 20]
QUANTILE_GROUPS = 5

# Backtest
BACKTEST_TOP_PCT = 0.1
BACKTEST_BOTTOM_PCT = 0.1
ANNUALIZE_FACTOR = 252

# Factor DB
FACTOR_DB_DIR = BASE_DIR / "factor_db"
FACTOR_DB_PATH = FACTOR_DB_DIR / "factors.db"
CHROMA_PATH = FACTOR_DB_DIR / "chroma"

# Agent
MAX_ITERATIONS = 20
GOOD_IC_THRESHOLD = 0.03
GOOD_ICIR_THRESHOLD = 0.5

# LLM settings
LLM_MODEL = "deepseek-chat"
LLM_TEMPERATURE = 0.3
LLM_PROVIDER = "deepseek"
OPENAI_API_KEY = None
if OPENAI_API_KEY is None:
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip().strip('"\'') or None
OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE", "").strip().strip('"\'') or "https://api.deepseek.com/v1"

# Output
OUTPUT_DIR = BASE_DIR / "output"
REPORT_OUTPUT_DIR = OUTPUT_DIR / "reports"

# V3-specific
MEMORY_TYPE = "local"
ORCHESTRATOR_MAX_ROUNDS = 3
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Data update (Optimization 1)
DATA_UPDATE_END_DATE = None  # None = use today


@dataclass
class Config:
    """Mutable config container for runtime overrides."""

    tickers: list = None
    start_date: str = None
    end_date: str = None
    forward_return_period: int = None
    max_iterations: int = None
    max_rounds: int = None
    llm_model: str = None
    llm_temperature: float = None
    llm_provider: str = None
    openai_api_key: str = None
    openai_api_base: str = None

    def __post_init__(self):
        if self.tickers is None:
            self.tickers = TICKERS.copy()
        if self.start_date is None:
            self.start_date = START_DATE
        if self.end_date is None:
            self.end_date = END_DATE
        if self.forward_return_period is None:
            self.forward_return_period = FORWARD_RETURN_PERIOD
        if self.max_iterations is None:
            self.max_iterations = MAX_ITERATIONS
        if self.max_rounds is None:
            self.max_rounds = ORCHESTRATOR_MAX_ROUNDS
        if self.llm_model is None:
            self.llm_model = LLM_MODEL
        if self.llm_temperature is None:
            self.llm_temperature = LLM_TEMPERATURE
        if self.llm_provider is None:
            self.llm_provider = LLM_PROVIDER
        if self.openai_api_key is None:
            self.openai_api_key = OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY", "").strip().strip('"\'') or None
        if self.openai_api_base is None:
            self.openai_api_base = OPENAI_API_BASE
