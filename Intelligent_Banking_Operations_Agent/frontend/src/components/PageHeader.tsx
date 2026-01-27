import { ReactNode } from 'react'

export default function PageHeader({ title, subtitle, actions }: { title: string, subtitle?: string, actions?: ReactNode }) {
	return (
		<div className="mb-6">
			<div className="flex items-end gap-4 justify-between">
				<div>
					<h2 className="text-xl font-semibold tracking-tight">{title}</h2>
					{subtitle && <p className="text-sm text-gray-300 mt-1">{subtitle}</p>}
				</div>
				{actions}
			</div>
		</div>
	)
}


