"""Pydantic request/response models for AlphaPilot API."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# Dashboard
class DashboardStats(BaseModel):
    active_factors: int
    average_ic: float
    best_sharpe: float
    last_data_update: Optional[str] = None


class ChartDataPoint(BaseModel):
    x: list
    y: list
    type: str = "bar"
    name: Optional[str] = None


# Factors
class FactorListItem(BaseModel):
    id: str
    expression: str
    mean_ic: Optional[float] = None
    mean_rank_ic: Optional[float] = None
    icir: Optional[float] = None
    sharpe: Optional[float] = None
    max_drawdown: Optional[float] = None
    turnover: Optional[float] = None
    is_active: bool = True
    created_at: Optional[str] = None


class FactorDetail(BaseModel):
    id: str
    expression: str
    mean_ic: Optional[float] = None
    mean_rank_ic: Optional[float] = None
    icir: Optional[float] = None
    sharpe: Optional[float] = None
    max_drawdown: Optional[float] = None
    turnover: Optional[float] = None
    is_active: bool = True
    created_at: Optional[str] = None
    ic_decay: Optional[dict] = None
    similar_factors: list = Field(default_factory=list)
    eval_history: list = Field(default_factory=list)


# Agent
class AgentRunRequest(BaseModel):
    research_goal: str = Field(default="Discover alpha factors with high IC, ICIR, and Sharpe.")
    tickers: Optional[list[str]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    max_rounds: Optional[int] = None


class AgentStatusResponse(BaseModel):
    running: bool
    message: Optional[str] = None


# Data
class DataStatusResponse(BaseModel):
    start_date: str
    end_date: str
    tickers: list[str]
    n_days: int
    n_tickers: int
    last_update: Optional[str] = None


class DataUpdateRequest(BaseModel):
    tickers_to_add: Optional[list[str]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    re_evaluate: bool = False


# Backtest
class BacktestRequest(BaseModel):
    factor_expression: str
    top_pct: float = 0.1
    bottom_pct: float = 0.1
    transaction_cost: float = 0.0005


class BacktestResult(BaseModel):
    sharpe: float
    max_drawdown: float
    annual_return: Optional[float] = None
    turnover: Optional[float] = None
    daily_returns: Optional[list[dict]] = None  # [{date, value}, ...]
    drawdown_series: Optional[list[dict]] = None
    monthly_heatmap: Optional[dict] = None  # {years, months, values}


# Reports
class ReportListItem(BaseModel):
    filename: str
    created_at: str
    title: Optional[str] = None


# Logs
class LogEntry(BaseModel):
    timestamp: str
    agent: Optional[str] = None
    action: str
    result: Any = None


class AgentLogMessage(BaseModel):
    agent: str
    action: str
    result: Any = None
    timestamp: Optional[str] = None
