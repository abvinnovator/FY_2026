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
	const [result, setResult] = useState<ReturnType<typeof Object> | null>(null)
	const { register, handleSubmit, formState: { errors, isSubmitting }, reset } = useForm<CreditPayload>({
		resolver: zodResolver(CreditPayloadSchema),
		defaultValues: {
			income: 4000,
			liabilities: 1200,
			delinquency_flags: [],
			requested_limit: 1500,
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

	return (
		<div>
			<PageHeader title="Credit Triage" subtitle="Scorecard and affordability with policy gating" actions={<Button variant='subtle' onClick={()=>reset()}>Reset form</Button>} />
			<div className="grid grid-cols-12 gap-6">
				<form className="col-span-12 md:col-span-6 space-y-4" onSubmit={handleSubmit(onSubmit)} aria-label="Credit Triage Form">
					<Card>
						<CardHeader title="Application" subtitle="Applicant financials" />
						<CardContent>
							<div className="grid grid-cols-2 gap-4">
								<Input step="100" type="number" {...register('income', { valueAsNumber: true })} label="Monthly Income" />{errors.income && <span className="text-red-400">{errors.income.message}</span>}
								<Input step="50" type="number" {...register('liabilities', { valueAsNumber: true })} label="Monthly Liabilities" />{errors.liabilities && <span className="text-red-400">{errors.liabilities.message}</span>}
								<label className="flex flex-col gap-1 text-sm col-span-2">Delinquency Flags<select multiple {...register('delinquency_flags')} className="focus-ring rounded bg-neutral-900 border border-border/60 px-3 py-2 h-28">
									<option>30+ days</option>
									<option>60+ days</option>
									<option>90+ days</option>
									<option>bankruptcy</option>
									<option>charge-off</option>
								</select>{errors.delinquency_flags && <span className="text-red-400">{errors.delinquency_flags.message}</span>}</label>
								<Input step="50" type="number" {...register('requested_limit', { valueAsNumber: true })} label="Requested Limit" />{errors.requested_limit && <span className="text-red-400">{errors.requested_limit.message}</span>}
							</div>
							<div className="mt-4">
								<Button type="submit" disabled={isSubmitting}>{isSubmitting ? 'Running…' : 'Run Credit Triage'}</Button>
							</div>
						</CardContent>
					</Card>
				</form>
				<div className="col-span-12 md:col-span-6">
					<AnimatePresence mode="wait">
					{result ? (
						<motion.div key="result" initial={{opacity: 0, y: 8}} animate={{opacity: 1, y: 0}} exit={{opacity: 0, y: -6}} transition={{duration: 0.15}} className="rounded border border-border/60 p-4 bg-neutral-950 space-y-2">
							<div className="flex items-center gap-3 mb-2">
								<span className={`px-2 py-1 rounded text-xs ${result.decision==='approve'?'bg-green-600':result.decision==='conditional'?'bg-amber-600':'bg-red-600'}`}>{(result as any).decision}</span>
								<div className="text-sm text-gray-300">DTI {(result as any).dti}</div>
							</div>
							<div className="text-sm">Suggested Limit: ${(result as any).limit_suggested}</div>
							{(result as any).rationale && (
								<div className="text-sm text-blue-300 italic my-3 border-l-2 border-blue-500 pl-3">
									{(result as any).rationale}
								</div>
							)}
							{((result as any).reasons?.length > 0) && (
								<>
									<div className="text-xs text-gray-400 mb-1">Key Factors</div>
									<ul className="list-disc pl-5 text-sm">
										{(result as any).reasons?.map((r:string, i:number)=>(<li key={i}>{r}</li>))}
									</ul>
								</>
							)}
						</motion.div>
					) : (
						<motion.div key="placeholder" initial={{opacity: 0}} animate={{opacity: 1}} exit={{opacity: 0}} className="rounded border border-dashed border-border/60 p-8 text-center text-gray-400">No results yet</motion.div>
					)}
					</AnimatePresence>
				</div>
			</div>
		</div>
	)
}


