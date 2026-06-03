"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useUser } from "@clerk/nextjs";
import { useEffect, useState } from "react";

/**
 * ユーザータイプ選択ページ
 * サインアップ前にユーザータイプ（求職者、企業担当リクルーター、エージェンシー）を選択
 * ※ agency_recruiter はエージェンシーからのメール招待経由でのみ登録可能
 * ※ サインイン済みユーザーでuserType設定済みの場合は各ダッシュボードにリダイレクト
 * ※ サインイン済みユーザーでuserType未設定の場合は選択画面を表示
 */
export default function SelectUserTypePage() {
	const router = useRouter();
	const { user, isLoaded } = useUser();
	const [needsTypeSelection, setNeedsTypeSelection] = useState(false);

	// サインイン済みユーザーはダッシュボードにリダイレクト（userType設定済みの場合）
	useEffect(() => {
		if (!isLoaded) return;

		if (user) {
			const publicMetadata = user.publicMetadata as Record<string, unknown> | undefined;
			const userType = publicMetadata?.userType as string | undefined;

			switch (userType) {
				case "job_seeker":
					router.push("/job-seeker/profile");
					break;
				case "corporate_recruiter":
					router.push("/corporate-recruiter/profile");
					break;
				case "agency":
					router.push("/agency/profile");
					break;
				case "agency_recruiter": {
					// agency_recruiterの場合は組織IDを取得してリダイレクト
					const memberships = user.organizationMemberships;
					const firstMembership = memberships?.[0];
					if (firstMembership) {
						router.push(`/${firstMembership.organization.id}/agency-recruiter/profile`);
					} else {
						router.push("/agency-recruiter/profile");
					}
					break;
				}
				default:
					// userTypeが未設定の場合は選択画面を表示
					setNeedsTypeSelection(true);
			}
		}
	}, [user, isLoaded, router]);

	// サインイン済みユーザーの場合、選択後はcompleteページにリダイレクト
	const handleSelect = (userType: "job_seeker" | "corporate_recruiter" | "agency") => {
		if (user) {
			// サインイン済みの場合はcompleteページでメタデータを設定
			router.push(`/auth/signup/complete?userType=${userType}`);
		} else {
			// 未サインインの場合はサインアップページへ
			router.push(`/auth/signup?userType=${userType}`);
		}
	};

	// ローディング中
	if (!isLoaded) {
		return (
			<div className="flex min-h-screen items-center justify-center bg-neutral-50 dark:bg-neutral-950">
				<div className="text-center">
					<div className="mb-4 inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-brand-600 border-r-transparent dark:border-brand-400"></div>
					<p className="text-neutral-900 dark:text-neutral-100">読み込み中...</p>
				</div>
			</div>
		);
	}

	// サインイン済みでuserType設定済みの場合はリダイレクト中
	if (user && !needsTypeSelection) {
		return (
			<div className="flex min-h-screen items-center justify-center bg-neutral-50 dark:bg-neutral-950">
				<div className="text-center">
					<div className="mb-4 inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-brand-600 border-r-transparent dark:border-brand-400"></div>
					<p className="text-neutral-900 dark:text-neutral-100">ダッシュボードにリダイレクト中...</p>
				</div>
			</div>
		);
	}

	return (
		<div className="flex min-h-screen items-center justify-center bg-neutral-50 p-4 dark:bg-neutral-950">
			<div className="w-full max-w-2xl space-y-8">
				{/* ヘッダー */}
				<div className="text-center">
					<h1 className="text-3xl font-bold text-neutral-900 dark:text-neutral-100">
						アカウントタイプを選択
					</h1>
					<p className="mt-2 text-neutral-600 dark:text-neutral-400">
						あなたの役割を選択してください
					</p>
				</div>

				{/* 選択肢 */}
				<div className="grid gap-4 md:grid-cols-2">
					{/* 求職者 */}
					<button
						type="button"
						onClick={() => handleSelect("job_seeker")}
						className="touch-target flex flex-col items-center justify-center rounded-lg border-2 border-neutral-300 bg-white p-8 text-center transition-all hover:border-brand-500 hover:bg-brand-50 dark:border-neutral-700 dark:bg-neutral-900 dark:hover:border-brand-400 dark:hover:bg-brand-900/20"
					>
						<div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-brand-100 dark:bg-brand-900/30">
							<svg
								className="h-8 w-8 text-brand-600 dark:text-brand-400"
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
						<h3 className="mb-2 text-lg font-semibold text-neutral-900 dark:text-neutral-100">
							求職者
						</h3>
						<p className="text-sm text-neutral-600 dark:text-neutral-400">
							案件を探して応募する
						</p>
					</button>

					{/* 企業担当リクルーター */}
					<button
						type="button"
						onClick={() => handleSelect("corporate_recruiter")}
						className="touch-target flex flex-col items-center justify-center rounded-lg border-2 border-neutral-300 bg-white p-8 text-center transition-all hover:border-brand-500 hover:bg-brand-50 dark:border-neutral-700 dark:bg-neutral-900 dark:hover:border-brand-400 dark:hover:bg-brand-900/20"
					>
						<div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-brand-100 dark:bg-brand-900/30">
							<svg
								className="h-8 w-8 text-brand-600 dark:text-brand-400"
								fill="none"
								stroke="currentColor"
								viewBox="0 0 24 24"
							>
								<path
									strokeLinecap="round"
									strokeLinejoin="round"
									strokeWidth={2}
									d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
								/>
							</svg>
						</div>
						<h3 className="mb-2 text-lg font-semibold text-neutral-900 dark:text-neutral-100">
							リクルーター
						</h3>
						<p className="text-sm text-neutral-600 dark:text-neutral-400">
							自社の採用を担当する
						</p>
					</button>

					{/* エージェンシー */}
					{/* <button
						type="button"
						onClick={() => handleSelect("agency")}
						className="touch-target flex flex-col items-center justify-center rounded-lg border-2 border-neutral-300 bg-white p-8 text-center transition-all hover:border-brand-500 hover:bg-brand-50 dark:border-neutral-700 dark:bg-neutral-900 dark:hover:border-brand-400 dark:hover:bg-brand-900/20"
					>
						<div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-brand-100 dark:bg-brand-900/30">
							<svg
								className="h-8 w-8 text-brand-600 dark:text-brand-400"
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
						<h3 className="mb-2 text-lg font-semibold text-neutral-900 dark:text-neutral-100">
							エージェンシー
						</h3>
						<p className="text-sm text-neutral-600 dark:text-neutral-400">
							人材紹介・仲介サービス
						</p>
					</button> */}
				</div>

				{/* 注意書き */}
				{/* <div className="rounded-lg bg-neutral-100 p-4 dark:bg-neutral-800">
					<p className="text-sm text-neutral-600 dark:text-neutral-400">
						<span className="font-medium">エージェンシー所属リクルーター</span>の方は、
						エージェンシーからのメール招待をお待ちください。
					</p>
				</div> */}

				{/* フッター */}
				<div className="text-center">
					<p className="text-sm text-neutral-600 dark:text-neutral-400">
						既にアカウントをお持ちですか？{" "}
						<Link
							href="/auth/signin"
							className="font-medium text-brand-600 hover:text-brand-700 dark:text-brand-400 dark:hover:text-brand-300"
						>
							サインイン
						</Link>
					</p>
				</div>
			</div>
		</div>
	);
}
