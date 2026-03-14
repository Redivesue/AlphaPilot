"""
Factor database: SQLite for metadata, Chroma for vector search (similar factors).
Reused from V2, will be enhanced in Phase 6.
"""

import sqlite3
import uuid
from pathlib import Path
from typing import Any, List, Optional

from core.config import CHROMA_PATH, FACTOR_DB_DIR, FACTOR_DB_PATH
from rag.embeddings import get_embedding_function


class FactorDB:
    """SQLite + Chroma for factor storage and retrieval."""

    def __init__(
        self,
        db_path: Optional[Path] = None,
        chroma_path: Optional[Path] = None,
    ):
        self.db_path = db_path or FACTOR_DB_PATH
        self.chroma_path = chroma_path or CHROMA_PATH
        FACTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
        self._init_sqlite()
        self._chroma_collection = None
        self._embed_fn = None

    def _init_sqlite(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS factors (
                id TEXT PRIMARY KEY,
                expression TEXT NOT NULL,
                mean_ic REAL,
                mean_rank_ic REAL,
                icir REAL,
                sharpe REAL,
                max_drawdown REAL,
                turnover REAL,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS factor_evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                factor_id TEXT NOT NULL,
                eval_date TEXT NOT NULL,
                mean_ic REAL,
                mean_rank_ic REAL,
                icir REAL,
                sharpe REAL,
                data_end_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (factor_id) REFERENCES factors(id)
            )
        """)
        try:
            conn.execute("ALTER TABLE factors ADD COLUMN is_active INTEGER DEFAULT 1")
        except sqlite3.OperationalError:
            pass
        conn.commit()
        conn.close()

    def _get_chroma(self):
        if self._chroma_collection is None:
            try:
                import chromadb
            except ImportError:
                raise RuntimeError("chromadb not installed. pip install chromadb")
            self._embed_fn = get_embedding_function()
            client = chromadb.PersistentClient(path=str(self.chroma_path))
            self._chroma_collection = client.get_or_create_collection(
                name="factors",
                metadata={"hnsw:space": "cosine"},
            )
        return self._chroma_collection

    def save_factor(self, expression: str, metrics: dict) -> str:
        """Persist factor to SQLite + Chroma. Returns factor id."""
        factor_id = str(uuid.uuid4())

        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            INSERT INTO factors (id, expression, mean_ic, mean_rank_ic, icir, sharpe, max_drawdown, turnover)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                factor_id,
                expression,
                metrics.get("mean_ic"),
                metrics.get("mean_rank_ic"),
                metrics.get("icir"),
                metrics.get("sharpe"),
                metrics.get("max_drawdown"),
                metrics.get("turnover"),
            ),
        )
        conn.commit()
        conn.close()

        try:
            coll = self._get_chroma()
            emb = self._embed_fn([expression])
            coll.add(ids=[factor_id], embeddings=emb, documents=[expression])
        except Exception:
            pass

        return factor_id

    def search_similar(self, expression: str, top_k: int = 5) -> List[dict]:
        """Vector search for similar factors. Returns list of dicts with expression, mean_ic, icir, sharpe."""
        try:
            coll = self._get_chroma()
            n = coll.count()
            if n == 0:
                return []
            emb = self._embed_fn([expression])
            results = coll.query(query_embeddings=emb, n_results=min(top_k, n))
        except Exception:
            return []

        if not results or not results.get("ids") or not results["ids"][0]:
            return []

        ids = results["ids"][0]
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = []
        for fid in ids:
            cur = conn.execute(
                "SELECT id, expression, mean_ic, mean_rank_ic, icir, sharpe, max_drawdown, turnover FROM factors WHERE id = ?",
                (fid,),
            )
            row = cur.fetchone()
            if row:
                rows.append(dict(row))
        conn.close()
        return rows

    def get_all(self, active_only: bool = False) -> List[dict]:
        """List all factors from SQLite. If active_only, filter by is_active=1."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        if active_only:
            cur = conn.execute(
                "SELECT id, expression, mean_ic, mean_rank_ic, icir, sharpe, max_drawdown, turnover, created_at "
                "FROM factors WHERE (is_active IS NULL OR is_active = 1) ORDER BY created_at DESC"
            )
        else:
            cur = conn.execute(
                "SELECT id, expression, mean_ic, mean_rank_ic, icir, sharpe, max_drawdown, turnover, created_at "
                "FROM factors ORDER BY created_at DESC"
            )
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def save_evaluation_history(
        self, factor_id: str, metrics: dict, data_end_date: Optional[str] = None
    ) -> None:
        """Save evaluation snapshot for decay analysis."""
        from datetime import datetime

        eval_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            INSERT INTO factor_evaluations (factor_id, eval_date, mean_ic, mean_rank_ic, icir, sharpe, data_end_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                factor_id,
                eval_date,
                metrics.get("mean_ic"),
                metrics.get("mean_rank_ic"),
                metrics.get("icir"),
                metrics.get("sharpe"),
                data_end_date,
            ),
        )
        conn.commit()
        conn.close()

    def get_factor_evaluation_history(self, factor_id: str) -> List[dict]:
        """Get evaluation history for a factor. Returns list of dicts with eval_date, mean_ic, etc."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            "SELECT eval_date, mean_ic, mean_rank_ic, icir, sharpe, data_end_date FROM factor_evaluations "
            "WHERE factor_id = ? ORDER BY eval_date DESC",
            (factor_id,),
        )
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def deactivate_factor(self, factor_id: str) -> bool:
        """Set is_active=0 for factor. Returns True if updated."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute("UPDATE factors SET is_active = 0 WHERE id = ?", (factor_id,))
        updated = cur.rowcount > 0
        conn.commit()
        conn.close()
        return updated

    def get_top_factors(self, metric: str = "sharpe", n: int = 10) -> List[dict]:
        """Retrieve top N factors by metric (sharpe, icir, mean_ic). Uses absolute value for IC metrics."""
        valid_metrics = {"sharpe", "icir", "mean_ic", "mean_rank_ic"}
        if metric not in valid_metrics:
            metric = "sharpe"
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        if metric in ("mean_ic", "mean_rank_ic"):
            order = f"ABS({metric}) DESC"
        else:
            order = f"{metric} DESC"
        cur = conn.execute(
            f"SELECT id, expression, mean_ic, mean_rank_ic, icir, sharpe, max_drawdown, turnover, created_at "
            f"FROM factors WHERE {metric} IS NOT NULL ORDER BY {order} LIMIT ?",
            (n,),
        )
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def get_factor_by_expression(self, expression: str) -> Optional[dict]:
        """Exact lookup by expression. Returns factor dict or None."""
        expr_clean = expression.strip()
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            "SELECT id, expression, mean_ic, mean_rank_ic, icir, sharpe, max_drawdown, turnover, created_at "
            "FROM factors WHERE expression = ? ORDER BY created_at DESC LIMIT 1",
            (expr_clean,),
        )
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def update_factor(self, factor_id: str, metrics: dict) -> bool:
        """Update existing factor with new metrics (e.g., backtest results). Returns True if updated."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute(
            "UPDATE factors SET mean_ic=?, mean_rank_ic=?, icir=?, sharpe=?, max_drawdown=?, turnover=? WHERE id=?",
            (
                metrics.get("mean_ic"),
                metrics.get("mean_rank_ic"),
                metrics.get("icir"),
                metrics.get("sharpe"),
                metrics.get("max_drawdown"),
                metrics.get("turnover"),
                factor_id,
            ),
        )
        updated = cur.rowcount > 0
        conn.commit()
        conn.close()
        return updated
