import Button from './Button'
import { useEffect, useState } from 'react'

export default function ThemeToggle(){
	const [isDark, setIsDark] = useState(true)
	useEffect(()=>{
		document.documentElement.classList.toggle('dark', isDark)
	}, [isDark])
	return (
		<Button variant="ghost" size="icon" aria-label="Toggle theme" onClick={()=>setIsDark(v=>!v)}>
			{isDark ? '☀️' : '🌙'}
		</Button>
	)
}


