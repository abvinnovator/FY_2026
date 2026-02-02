import { z } from 'zod'

export const FraudPayloadSchema = z.object({
	amount: z.number().min(0),
	currency: z.enum(['USD','EUR','INR']).default('USD'),
	merchant: z.string().min(1),
	mcc: z.string().min(2),
	geo: z.string().min(2),
	device_id: z.string().min(1),
	account_id: z.string().min(1),
	channel: z.enum(['ecommerce','pos','atm','p2p'])
})

export type FraudPayload = z.infer<typeof FraudPayloadSchema>

export const CreditPayloadSchema = z.object({
	// Core fields (required)
	income: z.number().min(0),
	liabilities: z.number().min(0),
	delinquency_flags: z.array(z.enum(['30+ days','60+ days','90+ days','bankruptcy','charge-off'])).default([]),
	requested_limit: z.number().min(0),
	// Enhanced fields for ML model (optional with defaults)
	credit_utilization: z.number().min(0).max(100).default(30),
	credit_history_months: z.number().min(0).optional().default(36),
	current_balance: z.number().min(0).optional(),
	credit_limit: z.number().min(0).optional(),
	employment_months: z.number().min(0).optional(),
	age: z.number().min(18).max(100).optional(),
	loan_type: z.enum(['credit_card', 'bnpl', 'personal_loan']).default('bnpl'),
})

export type CreditPayload = z.infer<typeof CreditPayloadSchema>

export const AnalyticsSchema = z.object({
	precision: z.number().nullable(),
	recall: z.number().nullable(),
	alert_volumes: z.number(),
	sla_ms: z.number().nullable(),
	band_distribution: z.object({ low: z.number(), medium: z.number(), high: z.number() }),
	vdr: z.number().optional(),
	confusion: z.object({ tp: z.number(), fp: z.number(), tn: z.number(), fn: z.number() }).optional()
})

export type AnalyticsData = z.infer<typeof AnalyticsSchema>


