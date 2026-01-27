import React, { forwardRef } from 'react'

export function Label({ children, htmlFor, className='' }: { children: React.ReactNode, htmlFor?: string, className?: string }){
	return <label htmlFor={htmlFor} className={`text-sm text-gray-300 ${className}`}>{children}</label>
}

export const Input = forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement> & { label?: string }>(({ label, id, className='', ...rest }, ref) => {
	return (
		<div className="space-y-1">
			{label && <Label htmlFor={id}>{label}</Label>}
			<input ref={ref} id={id} {...rest} className={`focus-ring rounded-md bg-neutral-900 border border-border/60 px-3 py-2 w-full ${className}`} />
		</div>
	)
})
Input.displayName = 'Input'

export const Select = forwardRef<HTMLSelectElement, React.SelectHTMLAttributes<HTMLSelectElement> & { label?: string }>(({ label, id, className='', children, ...rest }, ref) => {
	return (
		<div className="space-y-1">
			{label && <Label htmlFor={id}>{label}</Label>}
			<select ref={ref} id={id} {...rest} className={`focus-ring rounded-md bg-neutral-900 border border-border/60 px-3 py-2 w-full ${className}`}>
				{children}
			</select>
		</div>
	)
})
Select.displayName = 'Select'

export const TextArea = forwardRef<HTMLTextAreaElement, React.TextareaHTMLAttributes<HTMLTextAreaElement> & { label?: string }>(({ label, id, className='', ...rest }, ref) => {
	return (
		<div className="space-y-1">
			{label && <Label htmlFor={id}>{label}</Label>}
			<textarea ref={ref} id={id} {...rest} className={`focus-ring rounded-md bg-neutral-900 border border-border/60 px-3 py-2 w-full ${className}`} />
		</div>
	)
})
TextArea.displayName = 'TextArea'

export function Badge({ children, color='neutral', className='' }: { children: React.ReactNode, color?: 'green'|'amber'|'red'|'neutral', className?: string }){
	const colorMap: Record<string, string> = {
		green: 'bg-green-600/90 text-white',
		amber: 'bg-amber-600/90 text-white',
		red: 'bg-red-600/90 text-white',
		neutral: 'bg-neutral-700 text-neutral-100',
	}
	return <span className={`px-2 py-1 rounded text-xs ${colorMap[color]} ${className}`}>{children}</span>
}


