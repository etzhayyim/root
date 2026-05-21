"use client";

import type { ButtonHTMLAttributes, ReactNode } from "react";

/**
 * iPad最適化ボタンコンポーネント
 * Apple HIGに基づくタッチターゲットサイズ（最小44x44px）を確保
 * ダークモード・ライトモード対応、高コントラスト設計
 */
interface TouchOptimizedButtonProps
	extends ButtonHTMLAttributes<HTMLButtonElement> {
	children: ReactNode;
	variant?: "primary" | "secondary" | "outline" | "danger";
	size?: "sm" | "md" | "lg";
}

// Button エイリアスとしてもエクスポート
export { TouchOptimizedButton as Button };

export function TouchOptimizedButton({
	children,
	variant = "primary",
	size = "md",
	className = "",
	disabled,
	...props
}: TouchOptimizedButtonProps) {
	const baseClasses =
		"btn-touch touch-manipulation rounded-md font-semibold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none";

	const variantClasses = {
		primary:
			"bg-brand-500 text-white hover:bg-brand-700 active:bg-brand-800 focus:ring-brand-500 dark:bg-brand-500 dark:hover:bg-brand-600 dark:active:bg-brand-700 dark:focus:ring-brand-400 shadow-sm hover:shadow-md active:shadow-sm",
		secondary:
			"bg-white text-brand-500 border-2 border-brand-500 hover:bg-brand-50 active:bg-brand-100 focus:ring-brand-500 dark:bg-neutral-900 dark:text-brand-400 dark:border-brand-500 dark:hover:bg-neutral-800 dark:active:bg-neutral-700 dark:focus:ring-brand-400 shadow-sm hover:shadow-md active:shadow-sm dark:shadow-neutral-950/50",
		outline:
			"bg-transparent text-brand-500 border-2 border-brand-500 hover:bg-brand-50 active:bg-brand-100 focus:ring-brand-500 dark:bg-transparent dark:text-brand-400 dark:border-brand-500 dark:hover:bg-neutral-800 dark:active:bg-neutral-700 dark:focus:ring-brand-400",
		danger:
			"bg-error-500 text-white hover:bg-error-600 active:bg-error-700 focus:ring-error-500 dark:bg-error-500 dark:hover:bg-error-600 dark:active:bg-error-700 dark:focus:ring-error-400 shadow-sm hover:shadow-md active:shadow-sm",
	};

	const sizeClasses = {
		sm: "px-4 py-2.5 text-sm min-h-[44px]",
		md: "px-6 py-3 text-base min-h-[44px]",
		lg: "px-8 py-4 text-lg min-h-[52px]",
	};

	return (
		<button
			type="button"
			disabled={disabled}
			className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
			{...props}
		>
			{children}
		</button>
	);
}
