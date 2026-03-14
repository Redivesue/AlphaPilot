"""
Entry point for AlphaPilot V3 - Multi-agent alpha factor research system.
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env from AlphaPilot directory
load_dotenv(Path(__file__).resolve().parent / ".env")

from core.config import Config, OUTPUT_DIR, REPORT_OUTPUT_DIR
from core.llm import get_llm
from core.memory import Memory
from core.orchestrator import Orchestrator
from data.market_data_loader import load_or_download_data
from data_pipeline.data_updater import update_data
from core.factor_lifecycle import (
    re_evaluate_all_factors,
    flag_unstable_factors,
    save_reeval_results,
)
from rag.factor_vector_db import FactorDB
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


def parse_args():
    parser = argparse.ArgumentParser(description="AlphaPilot V3 - Multi-agent alpha factor research")
    parser.add_argument("--goal", type=str, default=None, help="Research goal for the agent")
    parser.add_argument("--force-download", action="store_true", help="Force re-download data")
    parser.add_argument("--update-data", action="store_true", help="Incremental data update before research")
    parser.add_argument("--re-evaluate", action="store_true", help="Re-evaluate all factors after data update")
    parser.add_argument("--max-rounds", type=int, default=None, help="Max orchestrator rounds")
    parser.add_argument("--max-iterations", type=int, default=None, help="Max per-agent LLM iterations")
    return parser.parse_args()


def main():
    args = parse_args()
    config = Config()
    if args.max_iterations is not None:
        config.max_iterations = args.max_iterations
    if args.max_rounds is not None:
        config.max_rounds = args.max_rounds

    api_key = (config.openai_api_key or os.environ.get("OPENAI_API_KEY") or "").strip().strip('"\'')
    if not api_key:
        print("Error: OPENAI_API_KEY not set.")
        print("Create AlphaPilot/.env with: OPENAI_API_KEY=your-DeepSeek-or-OpenAI-key")
        sys.exit(1)

    print("Loading data...")
    if args.update_data:
        data_bundle = update_data(
            tickers=config.tickers,
            forward_period=config.forward_return_period,
        )
        print(f"Data updated: {data_bundle.close_df.shape[0]} days, {data_bundle.close_df.shape[1]} tickers")
    else:
        data_bundle = load_or_download_data(
            tickers=config.tickers,
            start_date=config.start_date,
            end_date=config.end_date,
            forward_period=config.forward_return_period,
            force_download=args.force_download,
        )
        print(f"Data: {data_bundle.close_df.shape[0]} days, {data_bundle.close_df.shape[1]} tickers")

    print("Initializing Factor DB...")
    factor_db = FactorDB()

    if args.re_evaluate:
        print("Re-evaluating all factors...")
        reeval_results = re_evaluate_all_factors(data_bundle, factor_db)
        if reeval_results:
            deactivated = flag_unstable_factors(factor_db, reeval_results, decay_threshold=0.5)
            path = save_reeval_results(reeval_results)
            print(f"Re-evaluation complete: {len(reeval_results)} factors, {deactivated} deactivated. Saved to {path}")
        else:
            print("No factors to re-evaluate.")

    print("Creating LLM and Memory...")
    llm = get_llm(config)
    memory = Memory(factor_db)

    print("Registering skills...")
    registry = SkillRegistry()
    registry.register(
        "generate_factor",
        create_generate_factor_skill(data_bundle),
        "Compute a factor from an expression. Input: factor expression like rank(ts_mean(returns, 10)).",
    )
    registry.register(
        "search_similar_factors",
        create_search_factor_db_skill(factor_db),
        "Search for similar factors in database. Input: expression or idea. Call before new expressions.",
    )
    registry.register(
        "list_operators",
        create_list_operators_skill(),
        "List all factor operators and variables. Call to see syntax before writing expressions.",
    )
    registry.register(
        "evaluate_factor_full",
        create_evaluate_and_store_skill(data_bundle, factor_db),
        "Evaluate factor: IC, backtest, save to DB. Input: factor expression.",
    )
    registry.register(
        "backtest_strategy",
        create_backtest_skill(data_bundle),
        "Run long-short backtest for a factor. Input: factor expression.",
    )
    registry.register(
        "generate_report",
        create_report_skill(llm),
        "Generate Markdown research report. Input: factor_results text, research_goal.",
    )

    print("Creating agents...")
    agents = {
        "planner": PlannerAgent("planner", llm, memory, registry),
        "generator": GeneratorAgent("generator", llm, memory, registry, config),
        "evaluator": EvaluationAgent("evaluator", llm, memory, registry),
        "backtest": BacktestAgent("backtest", llm, memory, registry),
        "report": ReportAgent("report", llm, memory, registry),
    }

    print("Creating orchestrator...")
    orchestrator = Orchestrator(agents, memory, config)

    research_goal = args.goal or (
        "Discover alpha factors with high IC, ICIR, and Sharpe. "
        "Try momentum and mean-reversion style factors."
    )

    print("Running research pipeline...")
    try:
        result = orchestrator.run(research_goal)
    except Exception as e:
        err_msg = str(e).lower()
        if "401" in err_msg or "authentication" in err_msg or "invalid_api_key" in err_msg:
            print("\n[API 认证失败] 请检查 OPENAI_API_KEY 或 OPENAI_API_BASE")
        raise

    # Save factor results CSV
    eval_results = memory.recall("eval_results") or []
    if eval_results:
        import pandas as pd

        rows = []
        for r in eval_results:
            expr = r.get("expression", "")
            summary = r.get("summary", "")
            # Parse metrics from summary if possible
            rows.append({"expression": expr, "summary": summary})
        df = pd.DataFrame(rows)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = OUTPUT_DIR / "factor_results.csv"
        df.to_csv(out_path, index=False)
        print(f"\nSaved {len(rows)} factors to {out_path}")

    report_path = memory.recall("report_path")
    if report_path:
        print(f"Research report saved to {report_path}")

    print("\nDone.")


if __name__ == "__main__":
    main()
