import { useEffect, useState } from 'react'
import PageHeader from '@/components/PageHeader'
import Button from '@/components/Button'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { listFraudEvents, labelFraudEvent, suggestRules, getRuntimeRules, acceptRuntimeRule, clearRuntimeRules } from '@/lib/api'
import { toast } from 'sonner'

export default function AnalystQueue(){
	const [items, setItems] = useState<Array<any>>([])
	const [loading, setLoading] = useState(true)
	const [suggestions, setSuggestions] = useState<Array<any>>([])
	const [runtimeRules, setRuntimeRules] = useState<Array<any>>([])

	const load = async ()=>{
		setLoading(true)
		const resp = await listFraudEvents(100)
		// prioritize high/medium bands
		setItems((resp.items||[]).sort((a,b)=>{
			const rank = (x:string)=> x==='high'?2: x==='medium'?1:0
			return rank(b.risk_band) - rank(a.risk_band)
		}))
		const rs = await suggestRules(5)
		setSuggestions(rs.suggestions||[])
		const rr = await getRuntimeRules()
		setRuntimeRules(rr.rules||[])
		setLoading(false)
	}

	useEffect(()=>{ load() }, [])

	return (
		<div>
			<PageHeader title="Analyst Queue" subtitle="Review recent events and apply labels" actions={<Button onClick={load} variant='subtle'>Refresh</Button>} />
			<div className="grid grid-cols-12 gap-6">
				<div className="col-span-12">
					<Card>
						<CardHeader title="Recent Events" subtitle="Newest first; high/medium prioritized" />
						<CardContent>
							{loading ? 'Loading…' : (
								<div className="space-y-3">
									{items.map((e)=> (
										<div key={e.event_id} className="rounded border border-border/60 p-3 bg-neutral-950">
											<div className="flex items-center gap-3">
												<span className={`px-2 py-1 rounded text-xs ${e.risk_band==='low'?'bg-green-600':e.risk_band==='medium'?'bg-amber-600':'bg-red-600'}`}>{String(e.risk_band).toUpperCase()}</span>
												<div className="text-sm text-gray-300">Score {Math.round((e.alert_score||0)*100)}/100</div>
												<div className="ml-auto text-xs text-gray-400">{e.event_id}</div>
											</div>
											<div className="text-xs text-gray-400 mt-1">{(e.explanations||[]).join(' • ')}</div>
											<div className="flex gap-2 mt-2">
												<Button variant='subtle' onClick={async()=>{ await labelFraudEvent(e.event_id, 'fraud'); toast.success('Labeled fraud'); }}>Fraud</Button>
												<Button variant='subtle' onClick={async()=>{ await labelFraudEvent(e.event_id, 'genuine'); toast.success('Labeled genuine'); }}>Genuine</Button>
											</div>
										</div>
									))}
								</div>
							)}
						</CardContent>
					</Card>
				</div>
				<div className="col-span-12 lg:col-span-6">
					<Card>
						<CardHeader title="Rule Suggestions" subtitle="Derived from recent telemetry" />
						<CardContent>
							{loading ? 'Loading…' : (
								<div className="space-y-3">
									{suggestions.map((s:any)=>(
										<div key={s.rule_id} className="rounded border border-border/60 p-3 bg-neutral-950">
											<div className="flex items-center gap-2 text-sm text-gray-200">
												<span className="text-gray-300">{s.description}</span>
												<span className="ml-auto text-xs text-gray-400">Support {s.support}</span>
											</div>
											<div className="text-xs text-gray-400 mt-1">If {s.condition.feature} {s.condition.operator} {s.condition.value} then +{s.proposed_weight.toFixed(2)}</div>
											<div className="mt-2 flex gap-2">
												<Button variant='subtle' onClick={async()=>{ await acceptRuntimeRule({ description: s.description, feature: s.condition.feature, operator: s.condition.operator, value: s.condition.value, weight: s.proposed_weight }); const rr = await getRuntimeRules(); setRuntimeRules(rr.rules||[]); toast.success('Rule accepted'); }}>Accept</Button>
											</div>
										</div>
									))}
								</div>
							)}
						</CardContent>
					</Card>
				</div>
				<div className="col-span-12 lg:col-span-6">
					<Card>
						<CardHeader title="Active Runtime Rules" subtitle="Applied on top of core rules" />
						<CardContent>
							{loading ? 'Loading…' : (
								<div className="space-y-3">
									{runtimeRules.length===0 && <div className="text-sm text-gray-400">No runtime rules</div>}
									{runtimeRules.map((r:any, idx:number)=>(
										<div key={idx} className="rounded border border-border/60 p-3 bg-neutral-950">
											<div className="text-sm text-gray-200">{r.description}</div>
											<div className="text-xs text-gray-400">If {r.feature} {r.operator} {r.value} then +{(+r.weight).toFixed(2)}</div>
										</div>
									))}
									{runtimeRules.length>0 && <div className="mt-2"><Button variant='subtle' onClick={async()=>{ await clearRuntimeRules(); setRuntimeRules([]); toast.success('Cleared') }}>Clear All</Button></div>}
								</div>
							)}
						</CardContent>
					</Card>
				</div>
			</div>
		</div>
	)
}


