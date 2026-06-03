"use client";

/**
 * @etzhayyim/etzhayyim-hrse#AgencyRecruiterMailbox
 * エージェンシー所属リクルーター向けメールボックスページ
 */

import { useUser, useOrganization } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function AgencyRecruiterMailboxPage() {
	const { user, isLoaded } = useUser();
	const { organization } = useOrganization();
	const router = useRouter();

	// 組織に所属している場合は組織付きURLにリダイレクト
	useEffect(() => {
		if (organization?.id) {
			router.push(`/${organization.id}/agency-recruiter/mailbox`);
		}
	}, [organization?.id, router]);

	if (!isLoaded) {
		return (
			<div className="flex min-h-screen items-center justify-center">
				<div className="text-lg text-neutral-600 dark:text-neutral-400">
					読み込み中...
				</div>
			</div>
		);
	}

	if (!user) {
		router.push("/auth/signin");
		return null;
	}

	return (
		<div className="min-h-screen bg-neutral-50 p-4 md:p-8 dark:bg-neutral-950">
			<div className="mx-auto max-w-6xl">
				{/* ヘッダー */}
				<div className="mb-8">
					<h1 className="text-3xl font-bold text-neutral-900 dark:text-neutral-100">
						メールボックス
					</h1>
					<p className="mt-2 text-neutral-600 dark:text-neutral-400">
						求職者とのメッセージを管理します
					</p>
				</div>

				{/* メールボックス */}
				<div className="rounded-lg bg-white p-12 text-center shadow dark:bg-neutral-900">
					<div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-neutral-100 dark:bg-neutral-800">
						<svg
							className="h-8 w-8 text-neutral-400 dark:text-neutral-500"
							fill="none"
							stroke="currentColor"
							viewBox="0 0 24 24"
						>
							<path
								strokeLinecap="round"
								strokeLinejoin="round"
								strokeWidth={2}
								d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
							/>
						</svg>
					</div>
					<h3 className="mb-2 text-lg font-semibold text-neutral-900 dark:text-neutral-100">
						メッセージがありません
					</h3>
					<p className="text-neutral-600 dark:text-neutral-400">
						求職者とのやり取りがここに表示されます
					</p>
				</div>
			</div>
		</div>
	);
}
