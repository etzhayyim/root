"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

type Theme = "light" | "dark";

interface ThemeContextType {
	theme: Theme;
	toggleTheme: () => void;
	isTransitioning: boolean;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

/**
 * テーマプロバイダー
 * プロジェクト全体でテーマ状態を管理し、スムーズな切り替えを提供
 */
export function ThemeProvider({ children }: { children: ReactNode }) {
	const [theme, setTheme] = useState<Theme>("light");
	const [mounted, setMounted] = useState(false);
	const [isTransitioning, setIsTransitioning] = useState(false);

	useEffect(() => {
		setMounted(true);
		// ローカルストレージからテーマを読み込む
		const savedTheme = localStorage.getItem("theme") as Theme | null;
		const systemTheme: Theme = window.matchMedia("(prefers-color-scheme: dark)")
			.matches
			? "dark"
			: "light";
		const initialTheme = savedTheme || systemTheme;
		setTheme(initialTheme);
		applyTheme(initialTheme, false);
	}, []);

	const applyTheme = (newTheme: Theme, withTransition = true) => {
		if (withTransition) {
			setIsTransitioning(true);
		}

		// トランジション効果のためにクラスを追加
		document.documentElement.classList.add("theme-transitioning");

		// テーマを適用
		if (newTheme === "dark") {
			document.documentElement.classList.add("dark");
		} else {
			document.documentElement.classList.remove("dark");
		}

		localStorage.setItem("theme", newTheme);

		// トランジション完了後にクラスを削除
		if (withTransition) {
			setTimeout(() => {
				document.documentElement.classList.remove("theme-transitioning");
				setIsTransitioning(false);
			}, 300);
		}
	};

	const toggleTheme = () => {
		const newTheme = theme === "light" ? "dark" : "light";
		setTheme(newTheme);
		applyTheme(newTheme, true);
	};

	// システムテーマの変更を監視
	useEffect(() => {
		if (!mounted) return;

		const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
		const handleChange = (e: MediaQueryListEvent) => {
			// ユーザーが手動でテーマを設定していない場合のみシステムテーマに従う
			if (!localStorage.getItem("theme")) {
				const newTheme: Theme = e.matches ? "dark" : "light";
				setTheme(newTheme);
				applyTheme(newTheme, false);
			}
		};

		// 古いブラウザ対応のため、addEventListenerとaddListenerの両方をサポート
		if (mediaQuery.addEventListener) {
			mediaQuery.addEventListener("change", handleChange);
		} else {
			// @ts-ignore - 古いブラウザ対応
			mediaQuery.addListener(handleChange);
		}

		return () => {
			if (mediaQuery.removeEventListener) {
				mediaQuery.removeEventListener("change", handleChange);
			} else {
				// @ts-ignore - 古いブラウザ対応
				mediaQuery.removeListener(handleChange);
			}
		};
	}, [mounted]);

	return (
		<ThemeContext.Provider value={{ theme, toggleTheme, isTransitioning }}>
			{children}
		</ThemeContext.Provider>
	);
}

/**
 * テーマコンテキストを使用するフック
 */
export function useTheme() {
	const context = useContext(ThemeContext);
	if (context === undefined) {
		throw new Error("useTheme must be used within a ThemeProvider");
	}
	return context;
}
