"use client";

/**
 * @etzhayyim/etzhayyim-hrse#CorporateRecruiterDashboard
 * リクルーター向けダッシュボード
 */

import { useUser } from "@clerk/nextjs";
import Link from "next/link";
import { TouchOptimizedButton } from "@/components/TouchOptimizedButton";

export default function CorporateRecruiterDashboardPage() {
	const { user, isLoaded } = useUser();

	if (!isLoaded) {
		return (
			<div className="flex min-h-screen items-center justify-center">
				<div className="text-lg text-neutral-600 dark:text-neutral-400">
					読み込み中...
				</div>
			</div>
		);
	}

	return (
		<div className="min-h-screen bg-neutral-50 p-4 md:p-8 dark:bg-neutral-950">
			<div className="mx-auto max-w-6xl">
				{/* ヘッダー */}
				<div className="mb-8">
					<h1 className="text-3xl font-bold text-neutral-900 dark:text-neutral-100">
						リクルーター ダッシュボード
					</h1>
					<p className="mt-2 text-neutral-600 dark:text-neutral-400">
						ようこそ、{user?.firstName || user?.username || "ユーザー"}さん
					</p>
				</div>

				{/* クイックアクション */}
				<div className="mb-8 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
					{/* プロファイル */}
					<div className="rounded-lg bg-white p-6 shadow dark:bg-neutral-900">
						<div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-brand-100 dark:bg-brand-900/30">
							<svg
								className="h-6 w-6 text-brand-600 dark:text-brand-400"
								fill="none"
								stroke="currentColor"
								viewBox="0 0 24 24"
							>
								<path
									strokeLinecap="round"
									strokeLinejoin="round"
									strokeWidth={2}
									d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
								/>
							</svg>
						</div>
						<h2 className="mb-2 text-lg font-semibold text-neutral-900 dark:text-neutral-100">
							プロファイル
						</h2>
						<p className="mb-4 text-sm text-neutral-600 dark:text-neutral-400">
							企業情報と担当者情報を管理します
						</p>
						<Link href="/corporate-recruiter/profile">
							<TouchOptimizedButton variant="outline" className="w-full">
								プロファイルを編集
							</TouchOptimizedButton>
						</Link>
					</div>

					{/* 案件管理 */}
					<div className="rounded-lg bg-white p-6 shadow dark:bg-neutral-900">
						<div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-green-100 dark:bg-green-900/30">
							<svg
								className="h-6 w-6 text-green-600 dark:text-green-400"
								fill="none"
								stroke="currentColor"
								viewBox="0 0 24 24"
							>
								<path
									strokeLinecap="round"
									strokeLinejoin="round"
									strokeWidth={2}
									d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
								/>
							</svg>
						</div>
						<h2 className="mb-2 text-lg font-semibold text-neutral-900 dark:text-neutral-100">
							案件管理
						</h2>
						<p className="mb-4 text-sm text-neutral-600 dark:text-neutral-400">
							求人案件の作成・編集・管理を行います
						</p>
						<Link href="/corporate-recruiter/jobs">
							<TouchOptimizedButton variant="outline" className="w-full">
								案件を管理
							</TouchOptimizedButton>
						</Link>
					</div>

					{/* マッチング結果 */}
					<div className="rounded-lg bg-white p-6 shadow dark:bg-neutral-900">
						<div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-purple-100 dark:bg-purple-900/30">
							<svg
								className="h-6 w-6 text-purple-600 dark:text-purple-400"
								fill="none"
								stroke="currentColor"
								viewBox="0 0 24 24"
							>
								<path
									strokeLinecap="round"
									strokeLinejoin="round"
									strokeWidth={2}
									d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
								/>
							</svg>
						</div>
						<h2 className="mb-2 text-lg font-semibold text-neutral-900 dark:text-neutral-100">
							マッチング結果
						</h2>
						<p className="mb-4 text-sm text-neutral-600 dark:text-neutral-400">
							求職者とのマッチング結果を確認します
						</p>
						<Link href="/corporate-recruiter/matching">
							<TouchOptimizedButton variant="outline" className="w-full">
								マッチングを確認
							</TouchOptimizedButton>
						</Link>
					</div>
				</div>

				{/* ステータス概要 */}
				<div className="rounded-lg bg-white p-6 shadow dark:bg-neutral-900">
					<h2 className="mb-4 text-xl font-semibold text-neutral-900 dark:text-neutral-100">
						概要
					</h2>
					<div className="grid gap-4 md:grid-cols-4">
						<div className="rounded-lg bg-neutral-50 p-4 dark:bg-neutral-800">
							<div className="text-2xl font-bold text-brand-600 dark:text-brand-400">
								0
							</div>
							<div className="text-sm text-neutral-600 dark:text-neutral-400">
								公開中の案件
							</div>
						</div>
						<div className="rounded-lg bg-neutral-50 p-4 dark:bg-neutral-800">
							<div className="text-2xl font-bold text-green-600 dark:text-green-400">
								0
							</div>
							<div className="text-sm text-neutral-600 dark:text-neutral-400">
								マッチング候補
							</div>
						</div>
						<div className="rounded-lg bg-neutral-50 p-4 dark:bg-neutral-800">
							<div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
								0
							</div>
							<div className="text-sm text-neutral-600 dark:text-neutral-400">
								進行中の選考
							</div>
						</div>
						<div className="rounded-lg bg-neutral-50 p-4 dark:bg-neutral-800">
							<div className="text-2xl font-bold text-orange-600 dark:text-orange-400">
								0
							</div>
							<div className="text-sm text-neutral-600 dark:text-neutral-400">
								採用済み
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	);
}

