"""
Historical factor analysis: RAG-based comparison with similar factors.
"""

from typing import Any, Dict, Optional

from rag.factor_vector_db import FactorDB


def generate_similar_factors_analysis(
    expression: str,
    new_metrics: Dict[str, Any],
    factor_db: FactorDB,
    top_k: int = 5,
) -> str:
    """
    Search for similar factors, compute improvement vs each.
    Returns formatted text: "Similar to: expr_1 (IC=0.03), improvement: +15%; ..."
    """
    rows = factor_db.search_similar(expression, top_k=top_k)
    if not rows:
        return "No similar factors found in database."

    new_ic = new_metrics.get("mean_ic")
    if new_ic is None:
        new_ic = 0

    lines = []
    for r in rows:
        old_ic = r.get("mean_ic")
        expr = r.get("expression", "")
        if expr == expression:
            continue
        if old_ic is not None and old_ic != 0:
            pct = ((new_ic - old_ic) / abs(old_ic)) * 100
            sign = "+" if pct >= 0 else ""
            lines.append(f"- {expr} (IC={old_ic:.4f}), improvement: {sign}{pct:.1f}%")
        else:
            lines.append(f"- {expr} (IC={old_ic or 0:.4f}), no baseline for comparison")

    if not lines:
        return "No comparable similar factors (excluding self)."
    return "Similar factors:\n" + "\n".join(lines)
