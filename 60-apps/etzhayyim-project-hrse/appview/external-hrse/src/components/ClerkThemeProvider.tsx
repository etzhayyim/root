"use client";

import { ClerkProvider } from "@clerk/nextjs";
import { dark } from "@clerk/themes";
import { useEffect, useState, type ReactNode } from "react";

/**
 * Clerkプロバイダーにダークモード対応を追加するラッパー
 * HTMLのdarkクラスを監視して動的にテーマを切り替え
 */
export function ClerkThemeProvider({ children }: { children: ReactNode }) {
	const [isDark, setIsDark] = useState(false);
	const [mounted, setMounted] = useState(false);

	useEffect(() => {
		setMounted(true);
		// 初期状態をチェック
		setIsDark(document.documentElement.classList.contains("dark"));

		// MutationObserverでdarkクラスの変更を監視
		const observer = new MutationObserver((mutations) => {
			for (const mutation of mutations) {
				if (mutation.attributeName === "class") {
					setIsDark(document.documentElement.classList.contains("dark"));
				}
			}
		});

		observer.observe(document.documentElement, {
			attributes: true,
			attributeFilter: ["class"],
		});

		return () => observer.disconnect();
	}, []);

	// マウント前はデフォルトのテーマを使用
	if (!mounted) {
		return <ClerkProvider>{children}</ClerkProvider>;
	}

	// Clerkコンポーネント用のカスタムスタイル
	const clerkAppearance = {
		baseTheme: isDark ? dark : undefined,
		variables: isDark
			? {
					colorPrimary: "#0ea5e9", // brand-500
					colorBackground: "#171717", // neutral-900
					colorInputBackground: "#262626", // neutral-800
					colorText: "#fafafa", // neutral-50
					colorTextSecondary: "#a3a3a3", // neutral-400
					colorDanger: "#ef4444", // red-500
					colorSuccess: "#22c55e", // green-500
					colorWarning: "#f59e0b", // amber-500
					borderRadius: "0.5rem",
				}
			: {
					colorPrimary: "#0284c7", // brand-600
					colorBackground: "#ffffff",
					colorInputBackground: "#f5f5f5", // neutral-100
					colorText: "#171717", // neutral-900
					colorTextSecondary: "#525252", // neutral-600
					colorDanger: "#dc2626", // red-600
					colorSuccess: "#16a34a", // green-600
					colorWarning: "#d97706", // amber-600
					borderRadius: "0.5rem",
				},
		elements: {
			// ポップオーバーカードのスタイル
			card: isDark
				? "bg-neutral-900 border border-neutral-800 shadow-lg"
				: "bg-white border border-neutral-200 shadow-lg",
			// フッターのスタイル
			footer: isDark ? "bg-neutral-900" : "bg-white",
			footerAction: isDark
				? "text-neutral-400 hover:text-neutral-200"
				: "text-neutral-600 hover:text-neutral-900",
			// ボタンのスタイル
			formButtonPrimary: isDark
				? "bg-brand-500 hover:bg-brand-400 text-white"
				: "bg-brand-600 hover:bg-brand-700 text-white",
			// リストアイテムのスタイル
			organizationSwitcherPopoverActionButton: isDark
				? "text-neutral-300 hover:bg-neutral-800"
				: "text-neutral-700 hover:bg-neutral-100",
			userButtonPopoverActionButton: isDark
				? "text-neutral-300 hover:bg-neutral-800"
				: "text-neutral-700 hover:bg-neutral-100",
			// プレビューテキスト
			organizationPreviewMainIdentifier: isDark
				? "text-neutral-100"
				: "text-neutral-900",
			organizationPreviewSecondaryIdentifier: isDark
				? "text-neutral-400"
				: "text-neutral-600",
			userPreviewMainIdentifier: isDark
				? "text-neutral-100"
				: "text-neutral-900",
			userPreviewSecondaryIdentifier: isDark
				? "text-neutral-400"
				: "text-neutral-600",
		},
	};

	return (
		<ClerkProvider
        appearance={clerkAppearance as any}
        >
            {children}
        </ClerkProvider>
	);
}
