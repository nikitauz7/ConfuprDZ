from __future__ import annotations

from typing import Any, Dict, List

from .ast import Array, Expr, Number, String, Var, Value, ExprArg
from .errors import ConfigLangEvalError


JsonValue = Any  # float | str | list[JsonValue] | dict[str, JsonValue]


def _ensure_number(x: Any, *, op: str) -> float:
    if isinstance(x, (int, float)) and not isinstance(x, bool):
        return float(x)
    raise ConfigLangEvalError(f"Operator {op} expects numbers, got {type(x).__name__}")


def _ensure_array(x: Any, *, op: str) -> list:
    if isinstance(x, list):
        return x
    raise ConfigLangEvalError(f"Operator {op} expects an array, got {type(x).__name__}")


def eval_value(node: Value, env: Dict[str, JsonValue]) -> JsonValue:
    if isinstance(node, Number):
        return node.value
    if isinstance(node, String):
        return node.value
    if isinstance(node, Array):
        return [eval_value(item, env) for item in node.items]
    if isinstance(node, Expr):
        return eval_expr(node, env)
    raise TypeError(f"Unknown AST node: {node!r}")


def _eval_arg(arg: ExprArg, env: Dict[str, JsonValue]) -> JsonValue:
    if isinstance(arg, Var):
        if arg.name not in env:
            raise ConfigLangEvalError(f"Undefined name: {arg.name}")
        return env[arg.name]
    return eval_value(arg, env)


def eval_expr(expr: Expr, env: Dict[str, JsonValue]) -> JsonValue:
    op = expr.op
    args = [_eval_arg(a, env) for a in expr.args]

    if op in {"+", "-", "*"}:
        if len(args) < 2:
            raise ConfigLangEvalError(f"Operator {op} expects at least 2 operands, got {len(args)}")
        nums = [_ensure_number(a, op=op) for a in args]
        if op == "+":
            result = 0.0
            for n in nums:
                result += n
            return result
        if op == "*":
            result = 1.0
            for n in nums:
                result *= n
            return result
        # op == "-"
        result = nums[0]
        for n in nums[1:]:
            result -= n
        return result

    if op == "sort()":
        if len(args) != 1:
            raise ConfigLangEvalError(f"Function sort() expects exactly 1 argument, got {len(args)}")
        arr = _ensure_array(args[0], op=op)
        if len(arr) <= 1:
            return arr
        # Ensure all elements are comparable and of the same type group (numbers or strings)
        is_num = all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in arr)
        is_str = all(isinstance(x, str) for x in arr)
        if not (is_num or is_str):
            raise ConfigLangEvalError("sort() supports only arrays of numbers or arrays of strings")
        return sorted(arr)

    raise ConfigLangEvalError(f"Unknown operator/function: {op}")


def translate(assignments: list[tuple[str, Value]]) -> dict[str, JsonValue]:
    """Evaluate all assignments and return the final JSON object."""
    env: Dict[str, JsonValue] = {}
    for name, value_ast in assignments:
        env[name] = eval_value(value_ast, env)
    return env
