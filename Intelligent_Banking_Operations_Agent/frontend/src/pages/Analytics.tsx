import { useEffect, useState } from 'react'
import PageHeader from '@/components/PageHeader'
import Button from '@/components/Button'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { getAnalytics } from '@/lib/api'
import type { AnalyticsData } from '@/lib/schemas'

export default function Analytics(){
	const [data, setData] = useState<AnalyticsData|undefined>()
	const [loading, setLoading] = useState(true)

	const load = async ()=>{
		setLoading(true)
		const resp = await getAnalytics()
		setData(resp)
		setLoading(false)
	}

	useEffect(()=>{ load() }, [])

	return (
		<div>
			<PageHeader title="Analytics" subtitle="Operational KPIs and band distribution" actions={<Button onClick={load} variant='subtle'>Refresh</Button>} />
			<div className="grid grid-cols-12 gap-6">
				<div className="col-span-12">
					<div className="grid grid-cols-2 md:grid-cols-4 gap-4">
						{(['precision','recall','alert_volumes','sla_ms'] as const).map((k)=> (
							<Card key={k}>
								<CardContent>
									<div className="text-xs text-gray-400 uppercase">{k.replace('_',' ')}</div>
									<div className="text-2xl mt-1">{ loading ? '…' : (data as any)?.[k] ?? 'N/A' }</div>
								</CardContent>
							</Card>
						))}
					</div>
					<div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
						<Card>
							<CardContent>
								<div className="text-xs text-gray-400 uppercase">VDR</div>
								<div className="text-2xl mt-1">{ loading ? '…' : (data as any)?.vdr !== undefined ? (data as any).vdr.toFixed(1) : 'N/A' }</div>
							</CardContent>
						</Card>
						<Card>
							<CardContent>
								<div className="text-xs text-gray-400 uppercase">Confusion</div>
								<div className="text-sm mt-1">{ loading ? '…' : `TP ${(data as any)?.confusion?.tp ?? 0} / FP ${(data as any)?.confusion?.fp ?? 0}` }</div>
								<div className="text-sm">{ loading ? '' : `TN ${(data as any)?.confusion?.tn ?? 0} / FN ${(data as any)?.confusion?.fn ?? 0}` }</div>
							</CardContent>
						</Card>
					</div>
				</div>
				<div className="col-span-12">
					<Card>
						<CardHeader title="Band Distribution" />
						<CardContent>
							{loading ? 'Loading…' : (
								<div className="flex items-end gap-3 h-44" role="figure" aria-label="Band distribution">
									{(['low','medium','high'] as const).map((band)=>{
										const v = data?.band_distribution[band] ?? 0
										return <div key={band} className="flex-1 flex flex-col items-center" aria-label={`${band} ${v}`}>
											<div className="w-full rounded-t bg-gradient-to-t from-neutral-800 to-neutral-600" style={{height: `${Math.max(6, v/2)}%`}} />
											<span className="text-xs mt-2 capitalize text-gray-300">{band}</span>
										</div>
									})}
								</div>
							)}
						</CardContent>
					</Card>
				</div>
				<div className="col-span-12">
					<Card>
						<CardHeader title="Raw Data" subtitle="For debugging" />
						<CardContent>
							<pre className="text-xs overflow-auto bg-neutral-900 p-3 rounded">
								{JSON.stringify(data ?? {}, null, 2)}
							</pre>
						</CardContent>
					</Card>
				</div>
			</div>
		</div>
	)
}


