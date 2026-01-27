from __future__ import annotations

from collections import deque
from dataclasses import dataclass, asdict
from time import time
from typing import Deque, Dict, Iterable, List, Optional, Tuple

from src.fraud_detection.fraud_config import get_config


@dataclass
class TriageEvent:
    event_id: str
    timestamp_s: float
    intent: str
    payload: dict
    decision: str
    risk_band: str
    alert_score: float
    explanations: List[str]
    features: dict
    sla_ms: Optional[int] = None


@dataclass
class Label:
    event_id: str
    label: str  # 'fraud' or 'genuine'
    timestamp_s: float


_events: Deque[TriageEvent] = deque(maxlen=5000)
_labels: Dict[str, Label] = {}


def record_event(ev: TriageEvent) -> None:
    _events.append(ev)


def record_label(event_id: str, label: str) -> dict:
    _labels[event_id] = Label(event_id=event_id, label=label, timestamp_s=time())
    return {"status": "ok", "labeled": event_id, "label": label}


def get_event(event_id: str) -> Optional[TriageEvent]:
    for e in reversed(_events):
        if e.event_id == event_id:
            return e
    return None


def iter_events(limit: Optional[int] = None) -> Iterable[TriageEvent]:
    if limit is None:
        return list(_events)
    return list(_events)[-limit:]


def compute_kpis() -> dict:
    """Compute simple KPIs from telemetry and labels.

    - precision/recall using risk_band medium/high as predicted positive
    - VDR (value detection rate) via cost matrix
    - band distribution counts
    - average SLA
    """
    cfg = get_config()
    events = list(_events)
    band_counts = {"low": 0, "medium": 0, "high": 0}
    for e in events:
        band_counts[e.risk_band] = band_counts.get(e.risk_band, 0) + 1

    # Classification metrics
    tp = fp = tn = fn = 0
    total_latency = 0
    latency_count = 0
    for e in events:
        lbl = _labels.get(e.event_id)
        predicted_positive = e.risk_band in {"medium", "high"}
        if e.sla_ms is not None:
            total_latency += e.sla_ms
            latency_count += 1
        if lbl is None:
            continue
        is_fraud = (lbl.label == "fraud")
        if predicted_positive and is_fraud:
            tp += 1
        elif predicted_positive and not is_fraud:
            fp += 1
        elif (not predicted_positive) and (not is_fraud):
            tn += 1
        elif (not predicted_positive) and is_fraud:
            fn += 1

    precision = (tp / (tp + fp)) if (tp + fp) > 0 else None
    recall = (tp / (tp + fn)) if (tp + fn) > 0 else None
    avg_sla = int(total_latency / latency_count) if latency_count > 0 else None

    # Value-based metric
    cm = cfg.cost_matrix
    value = (
        tp * cm.true_positive_savings
        + fp * cm.false_positive_cost
        + fn * cm.false_negative_cost
        + tn * cm.true_negative_savings
    )
    vdr = value / max(1, (tp + fp + fn + tn))

    return {
        "precision": precision,
        "recall": recall,
        "alert_volumes": len(events),
        "sla_ms": avg_sla,
        "band_distribution": band_counts,
        "vdr": vdr,
        "confusion": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
    }


