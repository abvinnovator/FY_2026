import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import PageHeader from '@/components/PageHeader'
import Button from '@/components/Button'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { Input, Select } from '@/components/ui/Inputs'
import { FraudPayloadSchema, type FraudPayload } from '@/lib/schemas'
import { runFraudTriage, labelFraudEvent } from '@/lib/api'
import { useAppStore } from '@/store/useAppStore'
import { toast } from 'sonner'
import { AnimatePresence, motion } from 'framer-motion'

export default function FraudTriage(){
	const { setFraud } = useAppStore()
	const [result, setResult] = useState<any | null>(null)
	const { register, handleSubmit, formState: { errors, isSubmitting }, reset } = useForm<FraudPayload>({
		resolver: zodResolver(FraudPayloadSchema),
		defaultValues: {
			amount: 120,
			currency: 'USD',
			merchant: 'Test Merchant',
			mcc: '7995',
			geo: 'US-NY',
			device_id: 'dev-123',
			account_id: 'acct-001',
			channel: 'ecommerce',
		},
	})

	const onSubmit = async (data: FraudPayload) => {
		try {
			const resp = await runFraudTriage(data)
			setResult(resp as any)
			setFraud(data, resp)
			const band = (resp as any).risk_band ? ((resp as any).risk_band as string).toUpperCase() : 'N/A'
			const score = typeof resp.score === 'number' ? resp.score : Math.round(((resp as any).alert_score ?? 0)*100)
			toast.success(`Fraud: ${band} • ${resp.decision} • ${score}/100${(resp as any).event_id?` • ${(resp as any).event_id}`:''}`)
		} catch (error) {
			console.error(error)
			toast.error('An unexpected error occurred.', {
				description: error instanceof Error ? error.message : 'Please check the console for more details.'
			})
		}
	}

	// Helper to get severity color
	const getSeverityColor = (severity: string) => {
		switch(severity) {
			case 'critical': return 'text-red-400 bg-red-900/30';
			case 'high': return 'text-orange-400 bg-orange-900/30';
			case 'medium': return 'text-yellow-400 bg-yellow-900/30';
			default: return 'text-green-400 bg-green-900/30';
		}
	}

	return (
		<div>
			<PageHeader title="Fraud Triage" subtitle="Real-time fraud detection with explainable AI" actions={<Button variant='subtle' onClick={()=>reset()}>Reset form</Button>} />
			<div className="grid grid-cols-12 gap-6">
				{/* Input Form */}
				<form className="col-span-12 md:col-span-5 space-y-4" onSubmit={handleSubmit(onSubmit)} aria-label="Fraud Triage Form">
					<Card>
						<CardHeader title="Transaction" subtitle="Enter transaction details" />
						<CardContent>
							<div className="grid grid-cols-2 gap-4">
								<Input type="number" step="1" {...register('amount', { valueAsNumber: true })} label="Amount" />{errors.amount && <span className="text-red-400">{errors.amount.message}</span>}
								<Select {...register('currency')} label="Currency"><option>USD</option><option>EUR</option><option>INR</option></Select>{errors.currency && <span className="text-red-400">{errors.currency.message}</span>}
								<Input {...register('merchant')} label="Merchant" />{errors.merchant && <span className="text-red-400">{errors.merchant.message}</span>}
								<Input {...register('mcc')} label="MCC" />{errors.mcc && <span className="text-red-400">{errors.mcc.message}</span>}
								<Input {...register('geo')} label="Geo" />{errors.geo && <span className="text-red-400">{errors.geo.message}</span>}
								<Input {...register('device_id')} label="Device ID" />{errors.device_id && <span className="text-red-400">{errors.device_id.message}</span>}
								<Input {...register('account_id')} label="Account ID" />{errors.account_id && <span className="text-red-400">{errors.account_id.message}</span>}
								<Select {...register('channel')} label="Channel"><option>ecommerce</option><option>pos</option><option>atm</option><option>p2p</option></Select>{errors.channel && <span className="text-red-400">{errors.channel.message}</span>}
							</div>
							<div className="mt-4 flex gap-3 items-center">
								<Button type="submit" disabled={isSubmitting}>{isSubmitting ? 'Running…' : 'Run Fraud Triage'}</Button>
								{result?.event_id && (
									<div className="text-xs text-gray-400">Event: {result.event_id}</div>
								)}
							</div>
						</CardContent>
					</Card>
				</form>

				{/* Results Panel */}
				<div className="col-span-12 md:col-span-7 space-y-4">
					<AnimatePresence mode="wait">
						{result ? (
							<motion.div key="result" initial={{opacity: 0, y: 8}} animate={{opacity: 1, y: 0}} exit={{opacity: 0, y: -6}} transition={{duration: 0.15}} className="space-y-4">
								
								{/* Main Result Card */}
								<div className="rounded-lg border border-border/60 p-4 bg-neutral-950">
									<div className="flex items-center justify-between mb-3">
										<div className="flex items-center gap-3">
											<span className={`px-3 py-1 rounded-full text-sm font-medium ${(result.risk_band||'low')==='low'?'bg-green-600/20 text-green-400 border border-green-600/40':(result.risk_band||'')==='medium'?'bg-amber-600/20 text-amber-400 border border-amber-600/40':'bg-red-600/20 text-red-400 border border-red-600/40'}`}>
												{(result.risk_band||'LOW').toString().toUpperCase()} RISK
											</span>
											<span className="text-lg font-semibold text-white">Score: {Math.round((result.alert_score ?? 0)*100)}/100</span>
										</div>
										<span className={`px-2 py-1 rounded text-xs ${result.decision==='allow'?'bg-green-600':'bg-red-600'}`}>
											{result.decision?.toUpperCase()}
										</span>
									</div>
									
									{/* AI Rationale */}
									{result.rationale && (
										<div className="text-sm text-blue-300 italic border-l-2 border-blue-500 pl-3 py-2 bg-blue-950/20 rounded-r">
											{result.rationale}
										</div>
									)}
								</div>

								{/* Risk Factors - NOVEL FEATURE */}
								{result.risk_factors?.length > 0 && (
									<div className="rounded-lg border border-border/60 p-4 bg-neutral-950">
										<h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
											<span className="w-2 h-2 bg-red-500 rounded-full"></span>
											Risk Factor Analysis
										</h3>
										<div className="space-y-2">
											{result.risk_factors.map((factor: any, i: number) => (
												<div key={i} className="flex items-center justify-between p-2 rounded bg-neutral-900/50">
													<div className="flex-1">
														<div className="text-sm font-medium text-white">{factor.factor}</div>
														<div className="text-xs text-gray-400">{factor.description}</div>
													</div>
													<div className="flex items-center gap-2">
														<span className="text-xs text-gray-400">{factor.value}</span>
														<span className={`px-2 py-0.5 rounded text-xs ${getSeverityColor(factor.severity)}`}>
															+{factor.contribution} pts
														</span>
													</div>
												</div>
											))}
										</div>
									</div>
								)}

								{/* Anomaly Breakdown - NOVEL FEATURE */}
								{result.anomaly_breakdown && (
									<div className="rounded-lg border border-border/60 p-4 bg-neutral-950">
										<h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
											<span className="w-2 h-2 bg-purple-500 rounded-full"></span>
											ML Anomaly Analysis
										</h3>
										<div className="grid grid-cols-3 gap-4 mb-3">
											<div className="text-center p-2 rounded bg-neutral-900/50">
												<div className="text-xs text-gray-400">Rule Score</div>
												<div className="text-lg font-semibold text-white">{result.anomaly_breakdown.rule_score}/100</div>
												<div className="text-xs text-gray-500">{result.anomaly_breakdown.weights?.rule_based}</div>
											</div>
											<div className="text-center p-2 rounded bg-neutral-900/50">
												<div className="text-xs text-gray-400">ML Score</div>
												<div className="text-lg font-semibold text-white">{result.anomaly_breakdown.raw_score}/100</div>
												<div className="text-xs text-gray-500">{result.anomaly_breakdown.weights?.ml_anomaly}</div>
											</div>
											<div className="text-center p-2 rounded bg-purple-900/30 border border-purple-600/30">
												<div className="text-xs text-purple-400">Final Score</div>
												<div className="text-lg font-semibold text-purple-300">{result.anomaly_breakdown.weighted_final}/100</div>
												<div className="text-xs text-purple-400">Combined</div>
											</div>
										</div>
										<div className="text-sm text-gray-300 text-center italic">{result.anomaly_breakdown.interpretation}</div>
									</div>
								)}

								{/* Recommended Actions - NOVEL FEATURE */}
								{result.recommended_actions?.length > 0 && (
									<div className="rounded-lg border border-border/60 p-4 bg-neutral-950">
										<h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
											<span className="w-2 h-2 bg-amber-500 rounded-full"></span>
											Recommended Actions
										</h3>
										<ul className="space-y-2">
											{result.recommended_actions.map((action: string, i: number) => (
												<li key={i} className="flex items-start gap-2 text-sm text-gray-300">
													<span className="text-amber-400 mt-0.5">{i === 0 ? '●' : '○'}</span>
													{action}
												</li>
											))}
										</ul>
									</div>
								)}

								{/* Rule Hits */}
								{(result.rule_hits?.length > 0) && (
									<div className="rounded-lg border border-border/60 p-4 bg-neutral-950">
										<div className="text-xs text-gray-400 mb-2">Rule Triggers</div>
										<ul className="list-disc pl-5 text-sm text-gray-300">
											{result.rule_hits.map((r:string, i:number)=>(<li key={i}>{r}</li>))}
										</ul>
									</div>
								)}

								{/* Labeling Actions */}
								{result.event_id && (
									<div className="flex items-center gap-3 p-3 rounded-lg bg-neutral-900/50 border border-border/40">
										<div className="text-xs text-gray-500 flex-1">Event ID: {result.event_id}</div>
										<Button variant='subtle' onClick={async()=>{ await labelFraudEvent(result.event_id, 'fraud'); toast.success('Labeled as fraud') }}>Mark Fraud</Button>
										<Button variant='subtle' onClick={async()=>{ await labelFraudEvent(result.event_id, 'genuine'); toast.success('Labeled as genuine') }}>Mark Genuine</Button>
									</div>
								)}

							</motion.div>
						) : (
							<motion.div key="placeholder" initial={{opacity: 0}} animate={{opacity: 1}} exit={{opacity: 0}} className="rounded border border-dashed border-border/60 p-8 text-center text-gray-400">
								<div className="text-4xl mb-2">🔍</div>
								<div>Submit a transaction to analyze</div>
								<div className="text-xs mt-2 text-gray-500">Includes Risk Factor Analysis, ML Anomaly Detection & Recommended Actions</div>
							</motion.div>
						)}
					</AnimatePresence>
				</div>
			</div>
		</div>
	)
}
