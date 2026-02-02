import { z } from 'zod'
import type { FraudPayload, CreditPayload, AnalyticsData } from './schemas'

const sleep = (ms: number) => new Promise(res => setTimeout(res, ms))

const rng = (seed: string) => {
	let h = 2166136261 ^ seed.length
	for (let i = 0; i < seed.length; i++) {
		h ^= seed.charCodeAt(i)
		h += (h << 1) + (h << 4) + (h << 7) + (h << 8) + (h << 24)
	}
	return () => {
		h += 0x6D2B79F5
		let t = Math.imul(h ^ (h >>> 15), 1 | h)
		t ^= t + Math.imul(t ^ (t >>> 7), 61 | t)
		return ((t ^ (t >>> 14)) >>> 0) / 4294967296
	}
}

// Default to real backend unless explicitly opted into mocks
const USE_MOCKS = ((import.meta as any).env?.VITE_USE_MOCKS ?? 'false') === 'true'
const API_BASE = (import.meta as any).env?.VITE_API_BASE ?? 'http://127.0.0.1:8000/api/v1'

// Enhanced response types with novel fields
export interface FraudTriageResponse {
	decision: 'approve' | 'review' | 'decline'
	score: number
	reasons: string[]
	risk_band?: 'low' | 'medium' | 'high'
	summary?: string
	explanations?: string[]
	sla_ms?: number
	event_id?: string
	rationale?: string
	alert_score?: number
	rule_hits?: string[]
	// Novel fields
	risk_factors?: Array<{
		factor: string
		value: string
		severity: string
		contribution: number
		description: string
	}>
	anomaly_breakdown?: {
		method: string
		raw_score: number
		rule_score: number
		weighted_final: number
		weights: { rule_based: string; ml_anomaly: string }
		interpretation: string
	}
	recommended_actions?: string[]
}

export interface CreditTriageResponse {
	decision: 'approve' | 'review' | 'decline'
	limit_suggested: number
	requested_limit?: number
	dti: string | number
	reasons: string[]
	rationale?: string
	score?: number
	key_factors?: string[]
	
	// Fuzzy + ML Fusion fields
	scoring_method?: string
	confidence?: number
	fuzzy_score?: number
	ml_probability?: number
	ml_score?: number
	fused_risk_level?: string
	fusion_weights?: { fuzzy: number; ml: number }
	fuzzy_rules?: string[]
	ml_factors?: string[]
	
	// Legacy fields
	factor_breakdown?: Array<{
		name: string
		impact: number
		description: string
		severity: string
	}>
	improvement_tips?: string[]
	what_if_scenarios?: Array<{
		name: string
		action: string
		current: { score: number; dti: number; decision: string; band: string }
		simulated: { score: number; dti: number; decision: string; band: string }
		improvement: { score_change: number; dti_change: number; decision_improved: boolean }
	}>
	risk_summary?: {
		overall_score: number
		fuzzy_score?: number
		ml_score?: number
		risk_level: string
		fuzzy_band?: string
		ml_risk_level?: string
		confidence?: string
		dti_percent?: number
		factors_analyzed?: number
	}
	
	// Policy tracking
	policy_violations?: Array<{ code: string; severity: string }>
	policy_citations?: string[]
	hard_decline?: boolean
	hard_decline_reason?: string | null
}

export async function runFraudTriage(payload: FraudPayload): Promise<FraudTriageResponse> {
	if (!USE_MOCKS) {
		const resp = await fetch(`${API_BASE}/triage`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({
			payload: {
				account_id: payload.account_id,
				amount: payload.amount,
				currency: payload.currency,
				merchant: payload.merchant,
				mcc: payload.mcc,
				geo: payload.geo,
				device_id: payload.device_id,
				channel: payload.channel,
			}
		}) })
		const json = await resp.json()
		const result = json.result ?? json
		const decision: 'approve'|'review'|'decline' = result.risk_band === 'high' ? 'decline' : result.risk_band === 'medium' ? 'review' : 'approve'
		return { 
			decision, 
			score: Math.round((result.alert_score ?? 0)*100), 
			reasons: (result.explanations ?? result.rule_hits ?? []), 
			risk_band: result.risk_band, 
			summary: result.summary, 
			explanations: result.explanations, 
			sla_ms: result.sla_ms, 
			event_id: result.event_id, 
			rationale: result.rationale,
			alert_score: result.alert_score,
			rule_hits: result.rule_hits,
			// Novel fields
			risk_factors: result.risk_factors,
			anomaly_breakdown: result.anomaly_breakdown,
			recommended_actions: result.recommended_actions,
		}
	}
	await sleep(600)
	const seed = JSON.stringify(payload)
	const random = rng(seed)
	const score = Math.round((random()*0.6 + 0.2) * 100)
	const decision = score >= 75 ? 'decline' : score >= 45 ? 'review' : 'approve'
	const reasons: string[] = []
	if (payload.mcc === '7995') reasons.push('High-risk MCC')
	if (payload.channel === 'ecommerce') reasons.push('Card-not-present risk')
	if (payload.geo.toUpperCase().startsWith('US-') === false) reasons.push('New geography')
	return { decision, score, reasons, sla_ms: Math.round(120 + random()*80), rationale: "Mock rationale (AI disabled in mock mode)." }
}

export async function runCreditTriage(payload: CreditPayload): Promise<CreditTriageResponse> {
	if (!USE_MOCKS) {
		const resp = await fetch(`${API_BASE}/triage`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({
			payload: {
				applicant_id: 'app-ui',
				income: payload.income,
				liabilities: payload.liabilities,
				delinquency_flags: payload.delinquency_flags,
				requested_limit: payload.requested_limit,
				credit_utilization: payload.credit_utilization,
				credit_history_months: payload.credit_history_months,
				employment_months: payload.employment_months,
				age: payload.age,
				current_balance: payload.current_balance,
				credit_limit: payload.credit_limit,
				loan_type: payload.loan_type,
			}
		}) })
		const json = await resp.json()
		const decision: 'approve'|'review'|'decline' = json.decision === 'approve' ? 'approve' : json.decision === 'review' ? 'review' : 'decline'
		return { 
			decision, 
			limit_suggested: json.limit_suggested ?? Math.round((payload.income * 0.4)/50)*50,
			requested_limit: payload.requested_limit,
			dti: json.dti ?? (+(payload.liabilities/(payload.income||1)).toFixed(2)), 
			reasons: json.key_factors ?? [], 
			rationale: json.rationale,
			score: json.score,
			key_factors: json.key_factors,
			// Fusion fields
			scoring_method: json.scoring_method,
			confidence: json.confidence,
			fuzzy_score: json.fuzzy_score,
			ml_probability: json.ml_probability,
			ml_score: json.ml_score,
			fused_risk_level: json.fused_risk_level,
			fusion_weights: json.fusion_weights,
			fuzzy_rules: json.fuzzy_rules,
			ml_factors: json.ml_factors,
			// Legacy fields
			factor_breakdown: json.factor_breakdown,
			improvement_tips: json.improvement_tips,
			what_if_scenarios: json.what_if_scenarios,
			risk_summary: json.risk_summary,
			// Policy tracking
			policy_violations: json.policy_violations,
			policy_citations: json.policy_citations,
			hard_decline: json.hard_decline,
			hard_decline_reason: json.hard_decline_reason,
		}
	}
	await sleep(700)
	const seed = JSON.stringify(payload)
	const random = rng(seed)
	const dti = payload.income > 0 ? +(payload.liabilities / payload.income).toFixed(2) : 1
	let decision: 'approve'|'review'|'decline' = dti < 0.35 ? 'approve' : dti < 0.6 ? 'review' : 'decline'
	const reasons: string[] = []
	if (dti >= 0.6) reasons.push('High DTI')
	if (payload.delinquency_flags.length) reasons.push('Delinquency history')
	const limit_suggested = Math.round((payload.income * (0.4 - dti/2)) / 50) * 50
	return { decision, limit_suggested: Math.max(0, limit_suggested), dti: `${(dti * 100).toFixed(1)}%`, reasons }
}

export async function getAnalytics(): Promise<AnalyticsData> {
	if (!USE_MOCKS) {
		const resp = await fetch(`${API_BASE}/analytics/kpis`)
		return await resp.json()
	}
	await sleep(500)
	return {
		precision: Math.random() > 0.2 ? +(0.7 + Math.random()*0.2).toFixed(2) : null,
		recall: Math.random() > 0.2 ? +(0.6 + Math.random()*0.25).toFixed(2) : null,
		alert_volumes: 100 + Math.floor(Math.random()*200),
		sla_ms: Math.random() > 0.3 ? 180 + Math.floor(Math.random()*100) : null,
		band_distribution: {
			low: 60 + Math.floor(Math.random()*40),
			medium: 30 + Math.floor(Math.random()*30),
			high: 10 + Math.floor(Math.random()*20),
		},
	}
}

export async function listFraudEvents(limit = 50): Promise<{ items: Array<{ event_id: string, timestamp_s: number, decision: string, risk_band: 'low'|'medium'|'high', alert_score: number, explanations: string[], sla_ms?: number }>}> {
	if (!USE_MOCKS) {
		const resp = await fetch(`${API_BASE}/fraud/events?limit=${encodeURIComponent(String(limit))}`)
		return await resp.json()
	}
	await sleep(300)
	return { items: [] }
}

export async function labelFraudEvent(event_id: string, label: 'fraud'|'genuine'): Promise<{ status: string }> {
	if (!USE_MOCKS) {
		const resp = await fetch(`${API_BASE}/fraud/label`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ event_id, label }) })
		return await resp.json()
	}
	await sleep(200)
	return { status: 'ok' }
}

export async function suggestRules(limit = 3): Promise<{ suggestions: Array<{ rule_id: string, description: string, proposed_weight: number, condition: { feature: string, operator: string, value: number }, support: number }>}> {
	if (!USE_MOCKS) {
		const resp = await fetch(`${API_BASE}/fraud/rules/suggest`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ limit }) })
		return await resp.json()
	}
	await sleep(200)
	return { suggestions: [] }
}

export async function getRuntimeRules(): Promise<{ rules: Array<{ description: string, feature: string, operator: string, value: number, weight: number }>}> {
	if (!USE_MOCKS) {
		const resp = await fetch(`${API_BASE}/fraud/rules/runtime`)
		return await resp.json()
	}
	await sleep(200)
	return { rules: [] }
}

export async function acceptRuntimeRule(rule: { description: string, feature: string, operator?: string, value?: number, weight?: number }): Promise<{ accepted: any }>{
	if (!USE_MOCKS) {
		const resp = await fetch(`${API_BASE}/fraud/rules/runtime`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(rule) })
		return await resp.json()
	}
	await sleep(200)
	return { accepted: rule }
}

export async function clearRuntimeRules(): Promise<{ status: string }>{
	if (!USE_MOCKS) {
		const resp = await fetch(`${API_BASE}/fraud/rules/runtime`, { method: 'DELETE' })
		return await resp.json()
	}
	await sleep(200)
	return { status: 'cleared' }
}
