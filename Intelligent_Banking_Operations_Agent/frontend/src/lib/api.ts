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

export async function runFraudTriage(payload: FraudPayload): Promise<{ decision: 'approve'|'review'|'decline', score: number, reasons: string[], risk_band?: 'low'|'medium'|'high', summary?: string, explanations?: string[], sla_ms?: number, event_id?: string, rationale?: string }> {
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
		return { decision, score: Math.round((result.alert_score ?? 0)*100), reasons: (result.explanations ?? result.rule_hits ?? []), risk_band: result.risk_band, summary: result.summary, explanations: result.explanations, sla_ms: result.sla_ms, event_id: result.event_id, rationale: result.rationale }
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

export async function runCreditTriage(payload: CreditPayload): Promise<{ decision: 'approve'|'conditional'|'decline', limit_suggested: number, dti: number, reasons: string[], rationale?: string }> {
	if (!USE_MOCKS) {
		const resp = await fetch(`${API_BASE}/triage`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({
			payload: {
				applicant_id: 'app-ui',
				income: payload.income,
				liabilities: payload.liabilities,
				delinquency_flags: payload.delinquency_flags,
				requested_limit: payload.requested_limit,
			}
		}) })
		const json = await resp.json()
		const decision: 'approve'|'conditional'|'decline' = json.decision === 'approve' ? 'approve' : json.decision === 'review' ? 'conditional' : 'decline'
		return { decision, limit_suggested: Math.round((payload.income * 0.4)/50)*50, dti: +(payload.liabilities/(payload.income||1)).toFixed(2), reasons: json.key_factors ?? [], rationale: json.rationale }
	}
	await sleep(700)
	const seed = JSON.stringify(payload)
	const random = rng(seed)
	const dti = payload.income > 0 ? +(payload.liabilities / payload.income).toFixed(2) : 1
	let decision: 'approve'|'conditional'|'decline' = dti < 0.35 ? 'approve' : dti < 0.6 ? 'conditional' : 'decline'
	const reasons: string[] = []
	if (dti >= 0.6) reasons.push('High DTI')
	if (payload.delinquency_flags.length) reasons.push('Delinquency history')
	const limit_suggested = Math.round((payload.income * (0.4 - dti/2)) / 50) * 50
	return { decision, limit_suggested: Math.max(0, limit_suggested), dti, reasons }
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


