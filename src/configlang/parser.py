from __future__ import annotations

import ast as _py_ast
from dataclasses import dataclass
from typing import Dict, List, Tuple

from lark import Lark, Transformer, v_args
from lark.exceptions import UnexpectedInput

from .ast import Array, Expr, Number, String, Var, Value, ExprArg
from .errors import ConfigLangSyntaxError


# NOTE:
# Spec says numbers are: \d+\.\d*
# Example in the spec uses integer literal "1" inside expression.
# To be robust, we accept BOTH:
#   - 12.34  12.  0.5
#   - 42
# If you want strict mode, it's easy to tighten the NUMBER regex.
_GRAMMAR = r"""
?start: statement*

statement: NAME "=" value ";"    -> assign

?value: const_expr
      | array
      | NUMBER                   -> number
      | STRING                   -> string

array: "[" [value (";" value)* (";")?] "]"   -> array

const_expr: "^" "(" op operands ")"          -> const_expr

op: "+"             -> op_add
  | "-"             -> op_sub
  | "*"             -> op_mul
  | "sort()"        -> op_sort

operands: operand+                           -> operands

?operand: value
        | NAME                               -> var

NAME: /[_a-z]+/

# Strings in single quotes; supports standard backslash escapes (\n, \\ , \', etc.)
STRING: /'([^'\\]|\\.)*'/

# Numbers: 123.45  123.  123
NUMBER: /\d+(?:\.\d*)?/

LINE_COMMENT: /\|\|[^\n]*/
BLOCK_COMMENT: /<#[\s\S]*?#>/

%import common.WS
%ignore WS
%ignore LINE_COMMENT
%ignore BLOCK_COMMENT
"""


def _build_parser() -> Lark:
    # LALR is fast and good enough for the grammar
    return Lark(_GRAMMAR, parser="lalr", maybe_placeholders=False)


_PARSER = _build_parser()


@v_args(inline=True)
class _ToAst(Transformer):
    def assign(self, name, value):
        return (str(name), value)

    def start(self, *statements):
        # start: statement*  -> list of assignments
        return list(statements)

    def number(self, token):
        # token is str like "12.34" or "12"
        return Number(float(token))

    def string(self, token):
        # token includes quotes; we want actual Python string with escapes interpreted
        # Example: '\n' => newline, '\'' => single quote
        raw = str(token)
        try:
            # Use Python string literal parsing safely by reusing ast.literal_eval
            return String(_py_ast.literal_eval(raw))
        except Exception:
            # Fallback: strip quotes without unescaping
            return String(raw[1:-1])

    def array(self, *values):
        return Array(list(values))

    def op_add(self):
        return "+"

    def op_sub(self):
        return "-"

    def op_mul(self):
        return "*"

    def op_sort(self):
        return "sort()"

    def operands(self, *ops):
        return list(ops)

    def var(self, name):
        return Var(str(name))

    def const_expr(self, op, args):
        assert isinstance(args, list)
        return Expr(op=op, args=args)


def parse(text: str) -> List[Tuple[str, Value]]:
    """Parse source text into a list of (name, value_ast) assignments."""
    try:
        tree = _PARSER.parse(text)
        assignments = _ToAst().transform(tree)
        # `start` may return list, or a single item if only one statement (but our start is statement*)
        if assignments is None:
            return []
        if isinstance(assignments, tuple):
            return [assignments]
        return list(assignments)
    except UnexpectedInput as e:
        # Provide a readable message with line/column
        # Lark already stores line/column on UnexpectedInput
        line = getattr(e, "line", None)
        column = getattr(e, "column", None)
        context = e.get_context(text, span=40)
        msg = f"Syntax error at line {line}, column {column}.\n{context}"
        raise ConfigLangSyntaxError(msg, line=line, column=column) from e