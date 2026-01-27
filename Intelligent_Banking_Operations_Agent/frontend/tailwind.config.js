/** @type {import('tailwindcss').Config} */
export default {
	darkMode: ["class"],
	content: [
		"./index.html",
		"./src/**/*.{ts,tsx}",
	],
	theme: {
		extend: {
			colors: {
				background: "hsl(220 20% 6%)",
				foreground: "hsl(220 13% 96%)",
				primary: {
					DEFAULT: "hsl(245 100% 65%)",
					foreground: "#fff",
				},
				secondary: {
					DEFAULT: "hsl(220 9% 20%)",
					foreground: "hsl(220 13% 96%)",
				},
				destructive: {
					DEFAULT: "hsl(0 62% 50%)",
					foreground: "#fff",
				},
				muted: {
					DEFAULT: "hsl(220 9% 20%)",
					foreground: "hsl(220 13% 85%)",
				},
				accent: {
					DEFAULT: "hsl(220 9% 22%)",
					foreground: "hsl(220 13% 96%)",
				},
				border: "hsl(220 9% 22%)",
				input: "hsl(220 9% 22%)",
				ring: "hsl(245 100% 65%)",
			},
			boxShadow: {
				soft: "0 10px 30px -12px rgba(0,0,0,0.35)",
			},
		},
	},
	plugins: [],
}


