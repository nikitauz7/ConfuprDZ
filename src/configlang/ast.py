from __future__ import annotations

from dataclasses import dataclass
from typing import List, Union


# --- AST nodes (very small on purpose, only what's needed for Variant 2) ---

@dataclass(frozen=True)
class Number:
    value: float


@dataclass(frozen=True)
class String:
    value: str


@dataclass(frozen=True)
class Array:
    items: List["Value"]


@dataclass(frozen=True)
class Var:
    name: str


@dataclass(frozen=True)
class Expr:
    """Prefix constant expression: ^(op arg1 arg2 ...)."""
    op: str
    args: List["ExprArg"]


Value = Union[Number, String, Array, Expr]
ExprArg = Union[Value, Var]
