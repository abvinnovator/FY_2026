import React from 'react'

type ErrorBoundaryState = { hasError: boolean; error?: Error }

export default class ErrorBoundary extends React.Component<{ children: React.ReactNode }, ErrorBoundaryState> {
	state: ErrorBoundaryState = { hasError: false }

	static getDerivedStateFromError(error: Error): ErrorBoundaryState {
		return { hasError: true, error }
	}

	componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
		console.error('ErrorBoundary caught an error', error, errorInfo)
	}

	render() {
		if (this.state.hasError) {
			return (
				<div className="m-4 rounded border border-destructive/60 bg-red-950 text-red-100 p-4">
					<h2 className="font-semibold">Something went wrong.</h2>
					{this.state.error?.message && (
						<pre className="text-xs whitespace-pre-wrap mt-2">{this.state.error.message}</pre>
					)}
				</div>
			)
		}
		return this.props.children
	}
}


