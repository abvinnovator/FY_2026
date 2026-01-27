import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { FraudPayload, CreditPayload } from '@/lib/schemas'

type FraudState = {
	lastFraudInput?: FraudPayload
	fraudResult?: { decision: 'approve'|'review'|'decline', score: number, reasons: string[], sla_ms?: number }
}

type CreditState = {
	lastCreditInput?: CreditPayload
	creditResult?: { decision: 'approve'|'conditional'|'decline', limit_suggested: number, dti: number, reasons: string[] }
}

type AppState = FraudState & CreditState & {
	setFraud: (input: FraudPayload, result: FraudState['fraudResult']) => void
	setCredit: (input: CreditPayload, result: CreditState['creditResult']) => void
}

export const useAppStore = create<AppState>()(persist((set) => ({
	setFraud: (input, result) => set({ lastFraudInput: input, fraudResult: result }),
	setCredit: (input, result) => set({ lastCreditInput: input, creditResult: result }),
}), { name: 'banking-ops-store' }))


