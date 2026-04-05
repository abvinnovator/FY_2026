import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import PageHeader from '@/components/PageHeader'
import Button from '@/components/Button'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { Input, Select } from '@/components/ui/Inputs'
import { CreditPayloadSchema, type CreditPayload } from '@/lib/schemas'
import { runCreditTriage } from '@/lib/api'
import { useAppStore } from '@/store/useAppStore'
import { toast } from 'sonner'
import { AnimatePresence, motion } from 'framer-motion';

export default function CreditTriage(){
	const { setCredit } = useAppStore()
	const [result, setResult] = useState<any | null>(null)
	const { register, handleSubmit, formState: { errors, isSubmitting }, reset } = useForm<CreditPayload>({
		resolver: zodResolver(CreditPayloadSchema),
		defaultValues: {
			income: 5000,
			liabilities: 1500,
			delinquency_flags: [],
			requested_limit: 2000,
			credit_utilization: 35,
			credit_history_months: 48,
			employment_months: 24,
			age: 32,
			loan_type: 'bnpl',
		},
	})

	const onSubmit = async (data: CreditPayload) => {
		try {
			const resp = await runCreditTriage(data)
			setResult(resp as any)
			setCredit(data, resp)
			toast.success(`Credit: ${resp.decision} - DTI ${resp.dti}`)
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
			<PageHeader title="Credit Triage" subtitle="Fuzzy Logic + ML Fusion Credit Risk Analysis" actions={<Button variant='subtle' onClick={()=>reset()}>Reset form</Button>} />
			<div className="grid grid-cols-12 gap-6">
				{/* Input Form */}
				<form className="col-span-12 md:col-span-5 space-y-4" onSubmit={handleSubmit(onSubmit)} aria-label="Credit Triage Form">
					<Card>
						<CardHeader title="Application" subtitle="Applicant financials" />
						<CardContent>
							<div className="grid grid-cols-2 gap-4">
								<div className="col-span-2">
									<label className="text-sm font-medium mb-1 block">Loan Type <span className="text-red-500">*</span></label>
									<select 
										{...register('loan_type')} 
										className="w-full focus-ring rounded bg-neutral-900 border border-border/60 px-3 py-2"
									>
										<option value="bnpl">BNPL (Buy Now Pay Later)</option>
										<option value="credit_card">Credit Card</option>
										<option value="personal_loan">Personal Loan</option>
									</select>
								</div>

								<Input step="100" type="number" {...register('income', { valueAsNumber: true })} label={<>Monthly Income ($) <span className="text-red-500">*</span></>} />{errors.income && <span className="text-red-400">{errors.income.message}</span>}
								<Input step="50" type="number" {...register('liabilities', { valueAsNumber: true })} label={<>Monthly Liabilities ($) <span className="text-red-500">*</span></>} />{errors.liabilities && <span className="text-red-400">{errors.liabilities.message}</span>}
								<Input step="50" type="number" {...register('requested_limit', { valueAsNumber: true })} label={<>Requested Limit ($) <span className="text-red-500">*</span></>} />{errors.requested_limit && <span className="text-red-400">{errors.requested_limit.message}</span>}
								<Input step="1" type="number" {...register('credit_utilization', { valueAsNumber: true })} label={<>Credit Utilization (%) <span className="text-red-500">*</span></>} />{errors.credit_utilization && <span className="text-red-400">{errors.credit_utilization.message}</span>}
								
								<Input step="1" type="number" {...register('credit_history_months', { valueAsNumber: true })} label="Credit History (months)" />
								<Input step="1" type="number" {...register('employment_months', { valueAsNumber: true })} label="Employment (months)" />
								<Input step="1" type="number" {...register('age', { valueAsNumber: true })} label="Age (years)" />
								{/* <Input step="100" type="number" {...register('current_balance', { valueAsNumber: true })} label="Current Balance ($)" />
								
								<div className="col-span-2">
									<Input step="500" type="number" {...register('credit_limit', { valueAsNumber: true })} label="Current Credit Limit ($)" />
								</div> */}

								<label className="flex flex-col gap-1 text-sm col-span-2">Delinquency Flags<select multiple {...register('delinquency_flags')} className="focus-ring rounded bg-neutral-900 border border-border/60 px-3 py-2 h-24">
									<option>30+ days</option>
									<option>60+ days</option>
									<option>90+ days</option>
									<option>bankruptcy</option>
									<option>charge-off</option>
								</select>{errors.delinquency_flags && <span className="text-red-400">{errors.delinquency_flags.message}</span>}</label>
							</div>
							
							<div className="mt-6 flex items-center gap-3">
								<Button type="submit" disabled={isSubmitting} className="w-full md:w-auto">{isSubmitting ? 'Analyzing…' : 'Run Risk Analysis'}</Button>
								{/* <span className="text-xs text-gray-500">Hybrid Risk Engine Engaged</span> */}
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
										{/* Decision Badge - show conditional if approved but limit > suggested */}
										{(() => {
											const isConditional = result.decision === 'approve' && 
												result.limit_suggested && 
												result.limit_suggested < (result.requested_limit || 0);
											const displayDecision = isConditional ? 'CONDITIONAL' : result.decision?.toUpperCase();
											const badgeClass = result.decision === 'approve' 
												? (isConditional 
													? 'bg-amber-600/20 text-amber-400 border border-amber-600/40'
													: 'bg-green-600/20 text-green-400 border border-green-600/40')
												: result.decision === 'review' 
													? 'bg-amber-600/20 text-amber-400 border border-amber-600/40'
													: 'bg-red-600/20 text-red-400 border border-red-600/40';
											return (
												<span className={`px-3 py-1 rounded-full text-sm font-medium ${badgeClass}`}>
													{displayDecision}
												</span>
											);
										})()}
										<span className="text-lg font-semibold text-white">Score: {result.risk_summary?.overall_score || Math.round(result.score * 100)}/100</span>
									</div>
									<div className="text-sm text-gray-400">DTI: {result.dti}</div>
								</div>
								
								{/* Suggested Limit Display */}
								{result.limit_suggested && (
									<div className="flex items-center gap-4 mb-3 p-3 rounded bg-neutral-900/50 border border-border/40">
										<div className="flex-1">
											<div className="text-xs text-gray-500 uppercase tracking-wider">Suggested Limit</div>
											<div className="text-xl font-bold text-green-400">${result.limit_suggested.toLocaleString()}</div>
										</div>
										{result.requested_limit && result.limit_suggested < result.requested_limit && (
											<div className="flex-1 border-l border-border/40 pl-4">
												<div className="text-xs text-gray-500 uppercase tracking-wider">Requested</div>
												<div className="text-xl font-bold text-amber-400">${result.requested_limit?.toLocaleString()}</div>
												<div className="text-xs text-amber-500">Exceeds suggested by ${(result.requested_limit - result.limit_suggested).toLocaleString()}</div>
											</div>
										)}
									</div>
								)}
								
								{/* AI Rationale */}
								{result.rationale && (
									<div className="text-sm text-blue-300 italic border-l-2 border-blue-500 pl-3 py-2 bg-blue-950/20 rounded-r">
										{result.rationale}
									</div>
								)}
							</div>

							{/* Factor Breakdown - NOVEL FEATURE */}
							{result.factor_breakdown?.length > 0 && (
								<div className="rounded-lg border border-border/60 p-4 bg-neutral-950">
									<h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
										<span className="w-2 h-2 bg-purple-500 rounded-full"></span>
										Factor Contribution Analysis
									</h3>
									<div className="space-y-2">
										{result.factor_breakdown.map((factor: any, i: number) => (
											<div key={i} className="flex items-center justify-between p-2 rounded bg-neutral-900/50">
												<div className="flex-1">
													<div className="text-sm font-medium text-white">{factor.name}</div>
													<div className="text-xs text-gray-400">{factor.description}</div>
												</div>
												<div className="flex items-center gap-2">
													<span className={`px-2 py-0.5 rounded text-xs ${getSeverityColor(factor.severity)}`}>
														{factor.impact > 0 ? '+' : ''}{factor.impact} pts
													</span>
												</div>
											</div>
										))}
									</div>
								</div>
							)}

							{/* What-If Scenarios - NOVEL FEATURE */}
							{result.what_if_scenarios?.length > 0 && (
								<div className="rounded-lg border border-border/60 p-4 bg-neutral-950">
									<h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
										<span className="w-2 h-2 bg-cyan-500 rounded-full"></span>
										What-If Scenarios
									</h3>
									<div className="space-y-3">
										{result.what_if_scenarios.map((scenario: any, i: number) => (
											<div key={i} className="p-3 rounded bg-gradient-to-r from-cyan-950/30 to-transparent border border-cyan-800/30">
												<div className="text-sm font-medium text-cyan-300 mb-1">{scenario.name}</div>
												<div className="text-xs text-gray-400 mb-2">{scenario.action}</div>
												<div className="flex items-center gap-4 text-xs">
													<span className="text-gray-400">
														Score: {scenario.current?.score} → <span className="text-green-400 font-medium">{scenario.simulated?.score}</span>
													</span>
													<span className="text-gray-400">
														DTI: {scenario.current?.dti}% → <span className="text-green-400 font-medium">{scenario.simulated?.dti}%</span>
													</span>
													{scenario.improvement?.decision_improved && (
														<span className="px-2 py-0.5 bg-green-600/20 text-green-400 rounded text-xs">
															Decision Improves!
														</span>
													)}
												</div>
											</div>
										))}
									</div>
								</div>
							)}

							{/* Improvement Tips - NOVEL FEATURE */}
							{result.improvement_tips?.length > 0 && (
								<div className="rounded-lg border border-border/60 p-4 bg-neutral-950">
									<h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
										<span className="w-2 h-2 bg-emerald-500 rounded-full"></span>
										Improvement Recommendations
									</h3>
									<ul className="space-y-2">
										{result.improvement_tips.map((tip: string, i: number) => (
											<li key={i} className="flex items-start gap-2 text-sm text-gray-300">
												<span className="text-emerald-400 mt-0.5">✓</span>
												{tip}
											</li>
										))}
									</ul>
								</div>
							)}

							{/* Policy Violations - NEW FEATURE */}
							{result.policy_violations?.length > 0 && (
								<div className="rounded-lg border border-red-800/50 p-4 bg-red-950/20">
									<h3 className="text-sm font-semibold text-red-300 mb-3 flex items-center gap-2">
										<span className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
										Policy Violations Detected ({result.policy_violations.length})
									</h3>
									<div className="space-y-3">
										{result.policy_violations.map((pv: any, i: number) => (
											<div key={i} className="p-2 rounded bg-red-900/20 border border-red-800/30">
												<div className="flex items-center gap-2 mb-1">
													<span className="px-2 py-0.5 bg-red-600/30 text-red-300 rounded text-xs font-mono">
														{pv.code}
													</span>
													<span className="text-sm font-medium text-red-200">{pv.policy_name}</span>
												</div>
												<div className="text-xs text-gray-400 ml-0">
													<span className="text-gray-500">{pv.section}:</span> {pv.threshold}
												</div>
												<div className="text-xs text-red-300 mt-1">
													→ {pv.actual_value}
												</div>
											</div>
										))}
									</div>
								</div>
							)}

							{/* Key Factors (Original) */}
							{result.key_factors?.length > 0 && (
								<div className="rounded-lg border border-border/60 p-4 bg-neutral-950">
									<div className="text-xs text-gray-400 mb-2">Key Factors</div>
									<ul className="list-disc pl-5 text-sm text-gray-300">
										{result.key_factors.map((r:string, i:number)=>(<li key={i}>{r}</li>))}
									</ul>
								</div>
							)}

						</motion.div>
					) : (
						<motion.div key="placeholder" initial={{opacity: 0}} animate={{opacity: 1}} exit={{opacity: 0}} className="rounded border border-dashed border-border/60 p-8 text-center text-gray-400">
							<div className="text-4xl mb-2">📊</div>
							<div>Submit an application to see results</div>
							<div className="text-xs mt-2 text-gray-500">Includes Factor Analysis, What-If Scenarios & AI Recommendations</div>
						</motion.div>
					)}
					</AnimatePresence>
				</div>
			</div>
		</div>
	)
}
