# AlphaPilot V3 - Multi-Agent Alpha Factor Research System

Multi-agent system for automated alpha factor discovery with Planner, Generator, Evaluation, Backtest, and Report agents.

## Architecture

```
User / Research Goal
        ↓
Planner Agent (decomposes into tasks)
        ↓
Orchestrator (Task Queue)
        ↓
┌───────────────────────────────────────┐
│ Generator Agent   → factor candidates  │
│ Evaluation Agent  → IC metrics, store  │
│ Backtest Agent    → Sharpe, MDD        │
│ Report Agent      → Markdown report    │
└───────────────────────────────────────┘
        ↓
Skills / Tool Layer (generate_factor, evaluate_factor, backtest_strategy, etc.)
        ↓
Engine + Factor DB + RAG
```

## Setup

```bash
cd AlphaPilot
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set OPENAI_API_KEY (DeepSeek or OpenAI)
```

## Usage

```bash
# Default research goal
python main.py

# Custom research goal
python main.py --goal "Find momentum factors with high ICIR"

# Force re-download market data
python main.py --force-download

# Limit max rounds and iterations
python main.py --max-rounds 1 --max-iterations 10
```

## Output

- `output/factor_results.csv` - Factor expressions and evaluation summaries
- `output/reports/research_YYYYMMDD_HHMMSS.md` - LLM-generated research report
- `factor_db/` - SQLite + Chroma for factor storage and retrieval

## Agents

| Agent | Role | Tools |
|-------|------|-------|
| Planner | Decompose research goal into tasks | - |
| Generator | Generate factor expressions | generate_factor, search_similar_factors, list_operators |
| Evaluation | Compute IC metrics, store to DB | evaluate_factor_full |
| Backtest | Run long-short backtest | backtest_strategy |
| Report | Generate Markdown report | generate_report |

## Skills

- `generate_factor` - Compute factor from expression (AST-safe)
- `search_similar_factors` - RAG search for similar factors
- `list_operators` - List available operators (ts_mean, rank, etc.)
- `evaluate_factor_full` - Evaluate + backtest + store
- `backtest_strategy` - Long top 10%, short bottom 10%
- `generate_report` - LLM-powered Markdown report

## Data

Reuses V1/V2 data: 20 US stocks (AAPL, MSFT, AMZN, ...), 2015-2024, yfinance. Cache shared with alpha_research_v1 if present.

## Web Platform

AlphaPilot includes a React + FastAPI web console for interactive research.

### Backend (FastAPI)

```bash
pip install -r requirements.txt  # includes fastapi, uvicorn
python run_web.py
# API at http://localhost:8000
```

### Frontend (React)

```bash
cd frontend
npm install
npm run dev
# UI at http://localhost:5173 (proxies /api to backend)
```

### Production

```bash
cd frontend && npm run build
python run_web.py
# Serves both API and static frontend at http://localhost:8000
```

### Pages

- **Dashboard** - Active factors, avg IC, best Sharpe, IC distribution, equity curve
- **Factor Library** - List factors, view detail, IC decay, similar factors (RAG)
- **Agent Console** - Run factor discovery, real-time WebSocket logs
- **Data Manager** - View/update data range and tickers
- **Backtesting** - Run backtest, equity curve, drawdown charts
- **Reports** - List and view research reports
- **System Logs** - Agent and system log viewer

## API

- Default: DeepSeek (`deepseek-chat`) via `OPENAI_API_KEY` + `OPENAI_API_BASE=https://api.deepseek.com/v1`
- Supports OpenAI by setting `OPENAI_API_BASE` and `LLM_MODEL` in .env
