from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import mean, pstdev
from typing import Iterable


@dataclass
class HistoricalTxn:
	amount: float
	timestamp: datetime
	geo: str | None = None
	device_id: str | None = None
	mcc: str | None = None


def compute_time_window_stats(history: Iterable[HistoricalTxn], now: datetime, window: timedelta) -> dict[str, float]:
	window_txns = [h for h in history if now - h.timestamp <= window]
	amounts = [t.amount for t in window_txns]
	if not amounts:
		return {
			"count": 0.0,
			"total_amount": 0.0,
			"avg_amount": 0.0,
		}
	return {
		"count": float(len(amounts)),
		"total_amount": float(sum(amounts)),
		"avg_amount": float(mean(amounts)),
	}


def compute_amount_zscore(current_amount: float, history_amounts: list[float]) -> float:
	if len(history_amounts) < 5:
		return 0.0
	mu = mean(history_amounts)
	sigma = pstdev(history_amounts) or 1e-6
	return (current_amount - mu) / sigma


def device_novelty(device_id: str | None, history: Iterable[HistoricalTxn]) -> float:
	if device_id is None:
		return 0.0
	devices = {h.device_id for h in history if h.device_id}
	return 1.0 if device_id not in devices else 0.0


def geo_distance_flag(current_geo: str | None, history: Iterable[HistoricalTxn]) -> float:
	# Placeholder: Geo distance modeling is complex. We flag novelty only.
	if current_geo is None:
		return 0.0
	geos = {h.geo for h in history if h.geo}
	return 1.0 if current_geo not in geos else 0.0


def build_features(current_amount: float, now: datetime, mcc: str | None, geo: str | None, device_id: str | None, history: Iterable[HistoricalTxn]) -> dict:
	amounts = [h.amount for h in history]
	features_1h = compute_time_window_stats(history, now, timedelta(hours=1))
	features_24h = compute_time_window_stats(history, now, timedelta(hours=24))
	z = compute_amount_zscore(current_amount, amounts)
	feat = {
		"velocity_1h_count": features_1h["count"],
		"velocity_1h_total": features_1h["total_amount"],
		"velocity_24h_count": features_24h["count"],
		"velocity_24h_total": features_24h["total_amount"],
		"amount_zscore": z,
		"device_novelty": device_novelty(device_id, history),
		"geo_novelty": geo_distance_flag(geo, history),
		"high_risk_mcc": 1.0 if mcc in {"4829", "6011", "7995", "5944"} else 0.0,
		# Additional simple features
		"hour_of_day": float(now.hour),
		"is_night": 1.0 if (now.hour < 6 or now.hour >= 22) else 0.0,
		"first_time_mcc": 0.0 if any((h.mcc == mcc) for h in history) else (0.0 if mcc is None else 1.0),
	}
	return feat


