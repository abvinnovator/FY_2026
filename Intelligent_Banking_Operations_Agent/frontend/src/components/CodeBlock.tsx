import { useState } from 'react'

export default function CodeBlock({ code, className }: { code: string, className?: string }){
	const [copied, setCopied] = useState(false)
	return (
		<div className={`relative rounded-md border border-border/60 bg-neutral-900 ${className||''}`}>
			<button aria-label="Copy code" className="absolute right-2 top-2 text-xs px-2 py-1 bg-neutral-800 rounded focus-ring" onClick={() => { navigator.clipboard.writeText(code); setCopied(true); setTimeout(()=>setCopied(false), 1200) }}>{copied?'Copied':'Copy'}</button>
			<pre className="m-0 overflow-auto text-xs p-4">
				{code}
			</pre>
		</div>
	)
}


