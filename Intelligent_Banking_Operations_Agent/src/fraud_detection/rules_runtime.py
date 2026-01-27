from __future__ import annotations

from dataclasses import dataclass, asdict
from threading import RLock
from typing import Literal


Operator = Literal[">=", "<=", "==", ">", "<"]


@dataclass
class RuntimeRule:
    description: str
    feature: str
    operator: Operator
    value: float
    weight: float


_lock = RLock()
_rules: list[RuntimeRule] = []


def get_runtime_rules() -> list[dict]:
    with _lock:
        return [asdict(r) for r in _rules]


def clear_runtime_rules() -> None:
    global _rules
    with _lock:
        _rules = []


def add_runtime_rule(rule: dict) -> dict:
    rr = RuntimeRule(
        description=str(rule.get("description") or "runtime rule"),
        feature=str(rule["feature"]),
        operator=str(rule.get("operator", ">=")).strip() or ">=",
        value=float(rule.get("value", 1.0)),
        weight=float(rule.get("weight", 0.05)),
    )
    with _lock:
        _rules.append(rr)
    return asdict(rr)


def _compare(op: Operator, lhs: float, rhs: float) -> bool:
    if op == ">=":
        return lhs >= rhs
    if op == "<=":
        return lhs <= rhs
    if op == "==":
        return lhs == rhs
    if op == ">":
        return lhs > rhs
    if op == "<":
        return lhs < rhs
    return False


def apply_runtime_rules(features: dict) -> tuple[float, list[str]]:
    """Apply accepted runtime rules to features, returning (score_add, hits)."""
    score_add = 0.0
    hits: list[str] = []
    with _lock:
        rules_snapshot = list(_rules)
    for r in rules_snapshot:
        try:
            fv = float(features.get(r.feature, 0.0))
            if _compare(r.operator, fv, r.value):
                score_add += float(r.weight)
                hits.append(r.description)
        except Exception:
            # ignore any malformed feature comparisons
            continue
    return score_add, hits


