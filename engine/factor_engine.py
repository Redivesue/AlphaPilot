"""
Safe expression parser and executor for factor expressions.
"""

import ast
from typing import Any

import pandas as pd

from engine.factor_operators import OPERATORS
from data.market_data_loader import DataBundle

ALLOWED_VARS = {"close", "open", "high", "low", "volume", "returns"}
ALLOWED_FUNCS = set(OPERATORS.keys())


class FactorExpressionError(Exception):
    pass


class _SafeEvaluator(ast.NodeVisitor):
    def __init__(self, data_bundle: DataBundle):
        self.bundle = data_bundle
        self._vars = {
            "close": data_bundle.close_df,
            "open": data_bundle.open_df,
            "high": data_bundle.high_df,
            "low": data_bundle.low_df,
            "volume": data_bundle.volume_df,
            "returns": data_bundle.returns_df,
        }

    def _ensure_df(self, val: Any) -> pd.DataFrame:
        if isinstance(val, pd.DataFrame):
            return val
        if isinstance(val, (int, float)):
            return pd.DataFrame(
                val,
                index=self.bundle.close_df.index,
                columns=self.bundle.close_df.columns,
            )
        raise FactorExpressionError(f"Expected DataFrame or scalar, got {type(val)}")

    def visit_Expression(self, node: ast.Expression) -> pd.DataFrame:
        return self.visit(node.body)

    def visit_Call(self, node: ast.Call) -> pd.DataFrame:
        if not isinstance(node.func, ast.Name):
            raise FactorExpressionError("Only simple function calls allowed")
        name = node.func.id
        if name not in ALLOWED_FUNCS:
            raise FactorExpressionError(f"Unknown function: {name}")
        func = OPERATORS[name]
        args = [self.visit(a) for a in node.args]
        for i, a in enumerate(args):
            if isinstance(a, pd.DataFrame):
                continue
            if isinstance(a, (int, float)):
                args[i] = a
            else:
                raise FactorExpressionError(f"Invalid argument type for {name}")
        if name in ("ts_mean", "ts_std", "ts_max", "ts_min", "delta", "delay"):
            if len(args) != 2:
                raise FactorExpressionError(f"{name} requires 2 arguments")
            df = self._ensure_df(args[0])
            period = args[1]
            if not isinstance(period, (int, float)):
                period = int(period)
            return func(df, int(period))
        elif name in ("rank", "zscore", "log", "abs_val", "sign"):
            if len(args) != 1:
                raise FactorExpressionError(f"{name} requires 1 argument")
            return func(self._ensure_df(args[0]))
        elif name in ("max_val", "min_val"):
            if len(args) != 2:
                raise FactorExpressionError(f"{name} requires 2 arguments (df, bound)")
            df = self._ensure_df(args[0])
            bound = args[1]
            if not isinstance(bound, (int, float)):
                bound = float(bound)
            return func(df, bound)
        else:
            raise FactorExpressionError(f"Unhandled function: {name}")

    def visit_Name(self, node: ast.Name) -> pd.DataFrame:
        if node.id not in ALLOWED_VARS:
            raise FactorExpressionError(f"Unknown variable: {node.id}")
        return self._vars[node.id].copy()

    def visit_Constant(self, node: ast.Constant) -> float:
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise FactorExpressionError("Only numeric constants allowed")

    def visit_BinOp(self, node: ast.BinOp) -> pd.DataFrame:
        left = self.visit(node.left)
        right = self.visit(node.right)
        left_df = self._ensure_df(left) if isinstance(left, pd.DataFrame) else left
        right_df = self._ensure_df(right) if isinstance(right, pd.DataFrame) else right
        if isinstance(node.op, ast.Add):
            return left_df + right_df
        if isinstance(node.op, ast.Sub):
            return left_df - right_df
        if isinstance(node.op, ast.Mult):
            return left_df * right_df
        if isinstance(node.op, ast.Div):
            return left_df / right_df
        if isinstance(node.op, ast.FloorDiv):
            return left_df // right_df
        if isinstance(node.op, ast.Pow):
            return left_df ** right_df
        raise FactorExpressionError(f"Unsupported operator: {type(node.op)}")

    def visit_UnaryOp(self, node: ast.UnaryOp) -> pd.DataFrame:
        if isinstance(node.op, ast.USub):
            return -self._ensure_df(self.visit(node.operand))
        if isinstance(node.op, ast.UAdd):
            return self._ensure_df(self.visit(node.operand))
        raise FactorExpressionError(f"Unsupported unary op: {type(node.op)}")

    def generic_visit(self, node: ast.AST) -> Any:
        raise FactorExpressionError(f"Disallowed construct: {type(node).__name__}")


def compute_factor(expression: str, data_bundle: DataBundle) -> pd.DataFrame:
    expr = expression.strip()
    if not expr:
        raise FactorExpressionError("Empty expression")
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise FactorExpressionError(f"Syntax error: {e}")
    evaluator = _SafeEvaluator(data_bundle)
    return evaluator.visit(tree)
