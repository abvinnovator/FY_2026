import { ReactNode } from 'react'

export function Card({ className='', children }: { className?: string, children: ReactNode }){
	return (
		<div className={`rounded-xl border border-border/60 bg-neutral-950/80 backdrop-blur-sm shadow-soft ${className}`}>
			{children}
		</div>
	)
}

export function CardHeader({ className='', title, subtitle, right }: { className?: string, title: string, subtitle?: string, right?: ReactNode }){
	return (
		<div className={`px-5 py-4 border-b border-border/60 flex items-start justify-between ${className}`}>
			<div>
				<div className="text-sm text-gray-400">{subtitle}</div>
				<h3 className="text-base font-semibold tracking-tight mt-0.5">{title}</h3>
			</div>
			{right}
		</div>
	)
}

export function CardContent({ className='', children }: { className?: string, children: ReactNode }){
	return <div className={`px-5 py-5 ${className}`}>{children}</div>
}


