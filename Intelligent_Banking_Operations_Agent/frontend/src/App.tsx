import { Route, Routes } from 'react-router-dom'
import { Toaster } from 'sonner'
import { motion, AnimatePresence } from 'framer-motion'
import CreditTriage from '@/pages/CreditTriage'
import Layout from './components/Layout'

export default function App() {
	return (
		<Layout>
			<Toaster position="top-right" richColors />
			<AnimatePresence mode="wait">
				<Routes>
					{/* <Route path="/" element={
						<motion.div key="fraud" initial={{opacity: 0, y: 8}} animate={{opacity: 1, y: 0}} exit={{opacity: 0, y: -6}} transition={{duration: 0.15}}>
							<FraudTriage />
						</motion.div>
					} /> */}
					<Route path="/" element={
						<motion.div key="credit" initial={{opacity: 0, y: 8}} animate={{opacity: 1, y: 0}} exit={{opacity: 0, y: -6}} transition={{duration: 0.15}}>
							<CreditTriage />
						</motion.div>
					} />
					{/* <Route path="/analytics" element={
						<motion.div key="analytics" initial={{opacity: 0, y: 8}} animate={{opacity: 1, y: 0}} exit={{opacity: 0, y: -6}} transition={{duration: 0.15}}>
							<Analytics />
						</motion.div>
					} />
					<Route path="/queue" element={
						<motion.div key="queue" initial={{opacity: 0, y: 8}} animate={{opacity: 1, y: 0}} exit={{opacity: 0, y: -6}} transition={{duration: 0.15}}>
							<AnalystQueue />
						</motion.div>
					} /> */}
				</Routes>
			</AnimatePresence>
		</Layout>
	)
}


