"use client";

import { useTheme } from "@/lib/theme-context";

/**
 * テーマ切り替えコンポーネント
 * ダークモード・ライトモードの切り替えを提供
 * 動的なアニメーション効果付き
 */
export function ThemeToggle() {
	const { theme, toggleTheme, isTransitioning } = useTheme();

	return (
		<button
			type="button"
			onClick={toggleTheme}
			disabled={isTransitioning}
			className="group relative min-h-[44px] min-w-[44px] rounded-lg p-2 text-neutral-600 transition-all duration-300 hover:bg-neutral-100 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2 dark:text-neutral-300 dark:hover:bg-neutral-800 dark:focus:ring-brand-400 disabled:cursor-wait disabled:opacity-50"
			aria-label={theme === "light" ? "Switch to dark mode" : "Switch to light mode"}
		>
			{/* アイコンコンテナ - 回転アニメーション */}
			<div className="relative h-6 w-6">
				{/* 月アイコン */}
				<span
					className={`absolute inset-0 flex items-center justify-center text-xl transition-all duration-500 ${
						theme === "light"
							? "rotate-0 scale-100 opacity-100"
							: "rotate-90 scale-0 opacity-0"
					}`}
					role="img"
					aria-label="Dark mode"
				>
					🌙
				</span>
				{/* 太陽アイコン */}
				<span
					className={`absolute inset-0 flex items-center justify-center text-xl transition-all duration-500 ${
						theme === "dark"
							? "rotate-0 scale-100 opacity-100"
							: "-rotate-90 scale-0 opacity-0"
					}`}
					role="img"
					aria-label="Light mode"
				>
					☀️
				</span>
			</div>
			{/* ホバー時の光る効果 */}
			<span className="absolute inset-0 rounded-lg bg-gradient-to-r from-brand-400/0 via-brand-400/20 to-brand-400/0 opacity-0 transition-opacity duration-300 group-hover:opacity-100 dark:from-brand-500/0 dark:via-brand-500/20 dark:to-brand-500/0" />
		</button>
	);
}
