import { NavLink } from 'react-router-dom'
import ThemeToggle from './ThemeToggle'
import { Shield, CreditCard, BarChart3 } from 'lucide-react'

export default function Layout({ children }: { children: React.ReactNode }){
	return (
		<div className="min-h-screen bg-gradient-to-br from-neutral-950 via-neutral-950 to-[#0b0f14]">
			<header className="sticky top-0 z-40 border-b border-border/60 bg-neutral-950/60 backdrop-blur">
				<div className="container-max h-14 flex items-center justify-between">
					<div className="flex items-center gap-3">
						<img src="/dnb-logo.svg" alt="DNB" className="w-7 h-7 rounded" />
						<h1 className="text-sm sm:text-base font-semibold tracking-wide">Intelligent Banking Operations Agent</h1>
					</div>
					<div className="hidden md:flex items-center gap-6 text-sm">
						{/* <NavLink to="/" className={({isActive}) => isActive ? 'font-semibold text-white' : 'text-gray-300 hover:text-white'}>Fraud</NavLink> */}
						<NavLink to="/credit" className={({isActive}) => isActive ? 'font-semibold text-white' : 'text-gray-300 hover:text-white'}>Credit</NavLink>
						{/* <NavLink to="/analytics" className={({isActive}) => isActive ? 'font-semibold text-white' : 'text-gray-300 hover:text-white'}>Analytics</NavLink> */}
					</div>
					<div className="flex items-center gap-2">
						<ThemeToggle />
					</div>
				</div>
			</header>
			<div className="container-max grid grid-cols-12 gap-6 py-8">
				<aside className="col-span-12 md:col-span-3 lg:col-span-2">
					<nav className="rounded-xl border border-border/60 bg-neutral-950/80 backdrop-blur-sm p-2">
						<NavLink to="/fraud" className={({isActive}) => `flex items-center gap-3 px-3 py-2 rounded-md text-sm ${isActive ? 'bg-neutral-900 text-white' : 'text-gray-300 hover:text-white'}`}>
							<Shield size={16} /> Fraud Triage
						</NavLink>
						<NavLink to="/" className={({isActive}) => `flex items-center gap-3 px-3 py-2 rounded-md text-sm ${isActive ? 'bg-neutral-900 text-white' : 'text-gray-300 hover:text-white'}`}>
							<CreditCard size={16} /> Credit Triage
						</NavLink>
						{/* <NavLink to="/analytics" className={({isActive}) => `flex items-center gap-3 px-3 py-2 rounded-md text-sm ${isActive ? 'bg-neutral-900 text-white' : 'text-gray-300 hover:text-white'}`}>
							<BarChart3 size={16} /> Analytics
						</NavLink>
						<NavLink to="/queue" className={({isActive}) => `flex items-center gap-3 px-3 py-2 rounded-md text-sm ${isActive ? 'bg-neutral-900 text-white' : 'text-gray-300 hover:text-white'}`}>
							<Shield size={16} /> Analyst Queue
						</NavLink> */}
					</nav>
				</aside>
				<main className="col-span-12 md:col-span-9 lg:col-span-10">
					{children}
				</main>
			</div>
		</div>
	)
}


