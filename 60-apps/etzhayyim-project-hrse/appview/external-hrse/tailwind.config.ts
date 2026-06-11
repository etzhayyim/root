import type { Config } from "tailwindcss";

const config: Config = {
	darkMode: "class", // classベースのダークモード
	content: [
		"./pages/**/*.{js,ts,jsx,tsx,mdx}",
		"./components/**/*.{js,ts,jsx,tsx,mdx}",
		"./app/**/*.{js,ts,jsx,tsx,mdx}",
		"./src/**/*.{js,ts,jsx,tsx,mdx}",
	],
	theme: {
		extend: {
			screens: {
				// iPad向けブレークポイント
				ipad: "768px",
				"ipad-pro": "1024px",
			},
			spacing: {
				// タッチターゲット最小サイズ（44px = 11 * 4）
				"touch-target": "44px",
			},
			colors: {
				// デジタル庁デザインシステム v2.9.0 カラーパレット
				brand: {
					50: "#E6EBFF",
					100: "#CCD7FF",
					200: "#99AFFF",
					300: "#6687FF",
					400: "#335FFF",
					500: "#0017C1", // プライマリブルー
					600: "#1A4CFF", // プライマリブルーライト
					700: "#000D7A", // プライマリブルーダーク
					800: "#00095C",
					900: "#00063D",
					950: "#00031F",
				},
			content: {
				primary: "#1A1A1C",
				secondary: "#626264",
				tertiary: "#9A9A9C",
				disabled: "#D4D4D8",
			},
				border: {
					DEFAULT: "#D4D4D8",
					light: "#E8E8EA",
					dark: "#9A9A9C",
				},
				background: {
					DEFAULT: "#FFFFFF",
					surface: "#F5F5F8",
					elevated: "#FFFFFF",
				},
				error: {
					50: "#FEE2E2",
					100: "#FECACA",
					200: "#FCA5A5",
					300: "#F87171",
					400: "#EF4444",
					500: "#C42727", // DADS Error
					600: "#DC2626",
					700: "#B91C1C",
					800: "#991B1B",
					900: "#7F1D1D",
				},
				success: {
					50: "#ECFDF5",
					100: "#D1FAE5",
					200: "#A7F3D0",
					300: "#6EE7B7",
					400: "#34D399",
					500: "#0D8B3E", // DADS Success
					600: "#059669",
					700: "#047857",
					800: "#065F46",
					900: "#064E3B",
				},
				warning: {
					50: "#FFFBEB",
					100: "#FEF3C7",
					200: "#FDE68A",
					300: "#FCD34D",
					400: "#FBBF24",
					500: "#B58300", // DADS Warning
					600: "#D97706",
					700: "#B45309",
					800: "#92400E",
					900: "#78350F",
				},
				neutral: {
					50: "#FAFAFA",
					100: "#F5F5F8", // DADS Surface
					200: "#E8E8EA",
					300: "#D4D4D8", // DADS Border
					400: "#9A9A9C",
					500: "#626264", // DADS Text Secondary
					600: "#4A4A4C",
					700: "#3A3A3C",
					800: "#2A2A2C",
					900: "#1A1A1C", // DADS Text Primary
					950: "#0A0A0A",
				},
			},
			fontFamily: {
				sans: [
					'"Noto Sans JP"',
					"-apple-system",
					"BlinkMacSystemFont",
					'"Segoe UI"',
					"Roboto",
					'"Helvetica Neue"',
					"Arial",
					"sans-serif",
				],
			},
			fontSize: {
				// デジタル庁デザインシステム v2.9.0 タイポグラフィスケール
				"display-2xl": ["4.5rem", { lineHeight: "1.2", letterSpacing: "-0.02em" }],
				"display-xl": ["3.75rem", { lineHeight: "1.2", letterSpacing: "-0.02em" }],
				"display-lg": ["3rem", { lineHeight: "1.3", letterSpacing: "-0.01em" }],
				"display-md": ["2.25rem", { lineHeight: "1.4", letterSpacing: "-0.01em" }],
				"display-sm": ["1.875rem", { lineHeight: "1.5" }],
			},
			fontWeight: {
				light: "300",
				normal: "400",
				medium: "500",
				semibold: "600",
				bold: "700",
				extrabold: "800",
			},
		},
	},
	plugins: [],
};
export default config;
