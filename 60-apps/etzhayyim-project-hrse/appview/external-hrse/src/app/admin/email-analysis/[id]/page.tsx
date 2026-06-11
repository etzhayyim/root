"use client";

import { useUser } from "@clerk/nextjs";
import { useParams } from "next/navigation";

/**
 * メール分析詳細ページ
 * TODO: Connect-RPC サービスにemailAnalysis関連のRPCを追加後に実装
 */
export default function EmailAnalysisDetailPage() {
	const { user, isLoaded } = useUser();
	const params = useParams();
	const id = params?.id as string;

	if (!isLoaded) {
		return (
			<div className="flex min-h-screen items-center justify-center">
				<div className="text-lg">読み込み中...</div>
			</div>
		);
	}

	return (
		<div className="min-h-screen bg-neutral-50 p-4 md:p-8 dark:bg-neutral-950">
			<div className="mx-auto max-w-6xl">
				<h1 className="mb-8 text-3xl font-bold text-neutral-900 dark:text-neutral-100">
					メール分析詳細 (ID: {id})
				</h1>
				<div className="rounded-lg bg-white p-6 shadow-md dark:bg-neutral-900 dark:border dark:border-neutral-800">
					<p className="text-neutral-600 dark:text-neutral-400">
						この機能は現在開発中です。Connect-RPC サービスにemailAnalysis関連のRPCを追加後に実装予定です。
					</p>
				</div>
			</div>
		</div>
	);
}
