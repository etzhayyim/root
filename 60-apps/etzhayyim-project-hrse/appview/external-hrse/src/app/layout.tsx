import type { Metadata, Viewport } from "next";
import dynamicImport from "next/dynamic";
import { Noto_Sans_JP } from "next/font/google";
import { Footer } from "@/components/Footer";
import { Sidebar } from "@/components/Sidebar";
import { ClerkThemeProvider } from "@/components/ClerkThemeProvider";
import { ThemeProvider } from "@/lib/theme-context";
import "./globals.css";

// デジタル庁デザインシステム v2.9.0 フォント
const notoSansJP = Noto_Sans_JP({
	subsets: ["latin"],
	weight: ["300", "400", "500", "600", "700"],
	variable: "--font-noto-sans-jp",
	display: "swap",
});

// AuthDebugPanelはクライアント側でのみレンダリング（ハイドレーションエラーを防ぐ）
const AuthDebugPanel = dynamicImport(
	() => import("@/components/AuthDebugPanel").then((mod) => ({ default: mod.AuthDebugPanel })),
	{ ssr: false }
);

export const metadata: Metadata = {
	title: "etzhayyim HRSE",
	description:
		"サイバーセキュリティ特化型フリーランスマッチングプラットフォーム",
	appleWebApp: {
		capable: true,
		statusBarStyle: "default",
		title: "etzhayyim HRSE",
	},
	formatDetection: {
		telephone: false,
	},
};

export const dynamic = 'force-dynamic';

export const viewport: Viewport = {
	width: "device-width",
	initialScale: 1,
	maximumScale: 1,
	userScalable: false,
	themeColor: [
		{ media: "(prefers-color-scheme: light)", color: "#ffffff" },
		{ media: "(prefers-color-scheme: dark)", color: "#000000" },
	],
};

export default function RootLayout({
	children,
}: Readonly<{
	children: React.ReactNode;
}>) {
	return (
		<html lang="ja" suppressHydrationWarning className={notoSansJP.variable}>
			<body className="antialiased font-sans">
				<ThemeProvider>
					<ClerkThemeProvider>
						<div className="flex min-h-screen bg-white dark:bg-neutral-950">
							<Sidebar />
							<div className="flex flex-1 flex-col md:ml-64">
								<main className="flex-1">{children}</main>
								<Footer />
							</div>
							{/* <AuthDebugPanel /> */}
						</div>
					</ClerkThemeProvider>
				</ThemeProvider>
			</body>
		</html>
	);
}
