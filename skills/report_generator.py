"""
Report generator skill: LLM-powered Markdown research report.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from core.config import REPORT_OUTPUT_DIR
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI


def create_report_skill(llm: ChatOpenAI):
    """Create generate_report skill bound to LLM."""

    def generate_report(
        factor_results: str,
        research_goal: str = "Alpha factor research",
        similar_factors_analysis: Optional[str] = None,
    ) -> str:
        """Generate a Markdown research report from factor results.
        Input: factor_results - text summary of factors, IC metrics, backtest results.
        similar_factors_analysis - optional RAG comparison with historical factors.
        Returns the generated report content."""
        system_prompt = """You are a quantitative research analyst. Generate a professional
Markdown research report with these sections:
1. Summary - brief overview of the research and key findings
2. Factor Expressions - list the factor expressions tested
3. IC Analysis - interpretation of IC, Rank IC, ICIR, decay
4. Backtest Performance - Sharpe, max drawdown, turnover analysis
5. Similar Factors & Improvement Analysis - compare with similar historical factors, highlight improvements (e.g., IC improved by X%)
6. Risk Notes - any caveats or limitations
7. Conclusion - final recommendations

Write in clear, concise professional language. Use markdown headers (##) for sections."""
        analysis_block = ""
        if similar_factors_analysis:
            analysis_block = f"\n\nSimilar Factors & Improvement Analysis (RAG):\n{similar_factors_analysis}"
        user_prompt = f"""Research goal: {research_goal}

Factor results:
{factor_results}
{analysis_block}

Generate the full research report in Markdown."""
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
            response = llm.invoke(messages)
            return response.content
        except Exception as e:
            return f"Error generating report: {type(e).__name__}: {e}"

    return generate_report


def save_report(report_content: str, output_dir: Path = None) -> Path:
    """Save report to file. Returns path to saved file."""
    output_dir = output_dir or REPORT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = output_dir / f"research_{timestamp}.md"
    path.write_text(report_content, encoding="utf-8")
    return path
