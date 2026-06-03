"use client";

/**
 * @etzhayyim/etzhayyim-hrse#CorporateRecruiterMatching
 * 企業担当リクルーター向けマッチング結果ページ
 */

import { useUser } from "@clerk/nextjs";
import { useState } from "react";
import { TouchOptimizedButton } from "@/components/TouchOptimizedButton";

interface MatchingResult {
	id: string;
	jobSeekerId: string;
	jobSeekerName: string;
	jobTitle: string;
	matchScore: number;
	skills: string[];
	experience: string;
	status: "new" | "contacted" | "interviewing" | "rejected" | "hired";
	matchedAt: string;
}

export default function CorporateRecruiterMatchingPage() {
	const { user, isLoaded } = useUser();
	const [matchingResults] = useState<MatchingResult[]>([]);
	const [filterStatus, setFilterStatus] = useState<string | undefined>(undefined);

	if (!isLoaded) {
		return (
			<div className="flex min-h-screen items-center justify-center">
				<div className="text-lg text-neutral-600 dark:text-neutral-400">
					読み込み中...
				</div>
			</div>
		);
	}

	const getStatusLabel = (status: MatchingResult["status"]) => {
		switch (status) {
			case "new":
				return "新規";
			case "contacted":
				return "連絡済み";
			case "interviewing":
				return "面接中";
			case "rejected":
				return "見送り";
			case "hired":
				return "採用";
			default:
				return status;
		}
	};

	const getStatusColor = (status: MatchingResult["status"]) => {
		switch (status) {
			case "new":
				return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200";
			case "contacted":
				return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200";
			case "interviewing":
				return "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200";
			case "rejected":
				return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";
			case "hired":
				return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
			default:
				return "bg-neutral-100 text-neutral-800 dark:bg-neutral-700 dark:text-neutral-200";
		}
	};

	return (
		<div className="min-h-screen bg-neutral-50 p-4 md:p-8 dark:bg-neutral-950">
			<div className="mx-auto max-w-6xl">
				{/* ヘッダー */}
				<div className="mb-8">
					<h1 className="text-3xl font-bold text-neutral-900 dark:text-neutral-100">
						マッチング結果
					</h1>
					<p className="mt-2 text-neutral-600 dark:text-neutral-400">
						あなたの求人案件にマッチする候補者を確認できます
					</p>
				</div>

				{/* フィルター */}
				<div className="mb-6 flex flex-wrap gap-4">
					<TouchOptimizedButton
						variant={filterStatus === undefined ? "primary" : "outline"}
						onClick={() => setFilterStatus(undefined)}
					>
						すべて
					</TouchOptimizedButton>
					<TouchOptimizedButton
						variant={filterStatus === "new" ? "primary" : "outline"}
						onClick={() => setFilterStatus("new")}
					>
						新規
					</TouchOptimizedButton>
					<TouchOptimizedButton
						variant={filterStatus === "contacted" ? "primary" : "outline"}
						onClick={() => setFilterStatus("contacted")}
					>
						連絡済み
					</TouchOptimizedButton>
					<TouchOptimizedButton
						variant={filterStatus === "interviewing" ? "primary" : "outline"}
						onClick={() => setFilterStatus("interviewing")}
					>
						面接中
					</TouchOptimizedButton>
				</div>

				{/* マッチング結果一覧 */}
				{matchingResults.length === 0 ? (
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
									d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
								/>
							</svg>
						</div>
						<h3 className="mb-2 text-lg font-semibold text-neutral-900 dark:text-neutral-100">
							マッチング結果がありません
						</h3>
						<p className="text-neutral-600 dark:text-neutral-400">
							求人案件を作成すると、マッチする候補者が表示されます
						</p>
					</div>
				) : (
					<div className="space-y-4">
						{matchingResults
							.filter((result) => !filterStatus || result.status === filterStatus)
							.map((result) => (
								<div
									key={result.id}
									className="rounded-lg bg-white p-6 shadow dark:bg-neutral-900"
								>
									<div className="flex items-start justify-between">
										<div className="flex-1">
											<div className="mb-2 flex items-center gap-4">
												<h3 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">
													{result.jobSeekerName}
												</h3>
												<div className="flex items-center gap-2">
													<div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-green-400 to-green-600 text-sm font-bold text-white">
														{Math.round(result.matchScore * 100)}
													</div>
													<span className="text-sm font-medium text-green-700 dark:text-green-500">
														マッチ度
													</span>
												</div>
											</div>
											<p className="mb-2 text-neutral-600 dark:text-neutral-400">
												案件: {result.jobTitle}
											</p>
											<div className="mb-3 flex flex-wrap gap-2">
												{result.skills.map((skill) => (
													<span
														key={skill}
														className="rounded-full bg-brand-100 px-2 py-1 text-xs font-medium text-brand-800 dark:bg-brand-900 dark:text-brand-200"
													>
														{skill}
													</span>
												))}
											</div>
											<p className="text-sm text-neutral-600 dark:text-neutral-400">
												経験: {result.experience}
											</p>
										</div>
										<div className="ml-4 flex flex-col items-end gap-2">
											<span
												className={`rounded-full px-3 py-1 text-xs font-medium ${getStatusColor(result.status)}`}
											>
												{getStatusLabel(result.status)}
											</span>
											<TouchOptimizedButton variant="primary">
												詳細を確認
											</TouchOptimizedButton>
										</div>
									</div>
								</div>
							))}
					</div>
				)}
			</div>
		</div>
	);
}

