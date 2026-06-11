"use client";

/**
 * @etzhayyim/etzhayyim-hrse#AgencyMatchingConnect
 * Agency向けマッチング結果ページ（Connect-Web版）
 */

import { useUser } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { TouchOptimizedButton } from "@/components/TouchOptimizedButton";
import {
	useAgencyServiceClient,
	useMatchingServiceClient,
	type Agency,
	type MatchingResult,
} from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import { GetAgencyProfileRequestSchema } from "@/gen/proto/hrse/v1/agency_pb";
import { ListMatchingResultsForAgencyRequestSchema } from "@/gen/proto/hrse/v1/matching_pb";

export default function AgencyMatchingPage() {
	const { user, isLoaded } = useUser();
	const router = useRouter();
	const agencyClient = useAgencyServiceClient();
	const matchingClient = useMatchingServiceClient();

	const [loading, setLoading] = useState(true);
	const [profile, setProfile] = useState<Agency | null>(null);
	const [matchingResults, setMatchingResults] = useState<MatchingResult[]>([]);
	const [filterNotified, setFilterNotified] = useState<boolean | undefined>(undefined);
	const [page, setPage] = useState(1);
	const limit = 20;

	// プロファイル取得
	const fetchProfile = useCallback(async () => {
		try {
			const res = await agencyClient.getAgencyProfile(
				create(GetAgencyProfileRequestSchema, {})
			);
			if (res.agency) {
				setProfile(res.agency);
			}
		} catch (error) {
			console.error("Failed to fetch profile:", error);
		}
	}, [agencyClient]);

	// マッチング結果取得
	const fetchMatchingResults = useCallback(async () => {
		if (!profile?.id) return;

		setLoading(true);
		try {
			const res = await matchingClient.listMatchingResultsForAgency(
				create(ListMatchingResultsForAgencyRequestSchema, {
					agencyId: profile.id,
					limit,
					offset: (page - 1) * limit,
				})
			);

			let results = res.matchingResults || [];

			// 通知済みフィルター
			if (filterNotified !== undefined) {
				results = results.filter((r) =>
					filterNotified ? r.notifiedAt : !r.notifiedAt
				);
			}

			setMatchingResults(results);
		} catch (error) {
			console.error("Failed to fetch matching results:", error);
		} finally {
			setLoading(false);
		}
	}, [profile?.id, matchingClient, filterNotified, page]);

	useEffect(() => {
		if (user?.id) {
			fetchProfile();
		}
	}, [user?.id, fetchProfile]);

	useEffect(() => {
		if (profile?.id) {
			fetchMatchingResults();
		}
	}, [profile?.id, fetchMatchingResults]);

	// 認証チェック
	if (!isLoaded) {
		return (
			<div className="flex min-h-screen items-center justify-center">
				<div className="text-lg">読み込み中...</div>
			</div>
		);
	}

	if (!user) {
		router.push("/auth/signin");
		return null;
	}

	// プロファイルが存在しない場合
	if (!loading && !profile?.id) {
		return (
			<div className="min-h-screen bg-neutral-50 p-4 md:p-8 dark:bg-neutral-950">
				<div className="mx-auto max-w-6xl">
					<div className="rounded-lg bg-white p-8 shadow dark:bg-neutral-900">
						<p className="text-neutral-600 dark:text-neutral-400">
							エージェンシープロファイルが作成されていません。プロファイルを作成してください。
						</p>
						<TouchOptimizedButton
							onClick={() => router.push("/agency/profile")}
							className="mt-4"
						>
							プロファイル作成
						</TouchOptimizedButton>
					</div>
				</div>
			</div>
		);
	}

	return (
		<div className="min-h-screen bg-neutral-50 p-4 md:p-8 dark:bg-neutral-950">
			<div className="mx-auto max-w-6xl">
				<div className="mb-8 flex items-center gap-3">
					<h1 className="text-3xl font-bold text-neutral-900 dark:text-neutral-100">
						マッチング結果
					</h1>
					<span className="rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-800 dark:bg-green-900 dark:text-green-200">
						Connect-Web
					</span>
				</div>

				{/* フィルター */}
				<div className="mb-6 flex flex-wrap gap-4">
					<TouchOptimizedButton
						variant={filterNotified === undefined ? "primary" : "outline"}
						onClick={() => setFilterNotified(undefined)}
					>
						すべて
					</TouchOptimizedButton>
					<TouchOptimizedButton
						variant={filterNotified === false ? "primary" : "outline"}
						onClick={() => setFilterNotified(false)}
					>
						未送信のみ
					</TouchOptimizedButton>
					<TouchOptimizedButton
						variant={filterNotified === true ? "primary" : "outline"}
						onClick={() => setFilterNotified(true)}
					>
						送信済みのみ
					</TouchOptimizedButton>
				</div>

				{/* マッチング結果一覧 */}
				{loading ? (
					<div className="flex items-center justify-center py-12">
						<div className="text-lg text-neutral-600 dark:text-neutral-400">読み込み中...</div>
					</div>
				) : matchingResults.length === 0 ? (
					<div className="rounded-lg bg-white p-12 text-center shadow dark:bg-neutral-900">
						<p className="text-neutral-600 dark:text-neutral-400">マッチング結果がありません</p>
					</div>
				) : (
					<div className="space-y-4">
						{matchingResults.map((result) => (
							<div key={result.id} className="rounded-lg bg-white p-6 shadow dark:bg-neutral-900">
								<div className="mb-4 flex items-start justify-between">
									<div className="flex-1">
										<div className="mb-2 flex items-center gap-4">
											<h3 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">
												{result.job?.title ?? "案件名不明"}
											</h3>
											<div className="flex items-center gap-2">
												<div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-green-400 to-green-600 text-sm font-bold text-white">
													{Math.round(result.totalScore * 100)}
												</div>
												<span className="text-sm font-medium text-green-700 dark:text-green-500">
													マッチ度
												</span>
											</div>
										</div>
										<p className="mb-2 text-neutral-600 dark:text-neutral-400">
											{result.job?.description ?? ""}
										</p>
										<div className="grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
											<div>
												<span className="text-neutral-600 dark:text-neutral-400">勤務地:</span>
												<span className="ml-2 font-medium text-neutral-900 dark:text-neutral-100">
													{result.job?.jobLocation ?? "-"}
												</span>
											</div>
											<div>
												<span className="text-neutral-600 dark:text-neutral-400">単価:</span>
												<span className="ml-2 font-medium text-neutral-900 dark:text-neutral-100">
													{result.job?.salary?.min ?? result.job?.jobUnitPriceMin ?? 0}円 〜 {result.job?.salary?.max ?? result.job?.jobUnitPriceMax ?? 0}円
												</span>
											</div>
											<div>
												<span className="text-neutral-600 dark:text-neutral-400">リモート:</span>
												<span className="ml-2 font-medium text-neutral-900 dark:text-neutral-100">
													{result.job?.remoteAllowed ? "可" : "不可"}
												</span>
											</div>
											<div>
												<span className="text-neutral-600 dark:text-neutral-400">人材ID:</span>
												<span className="ml-2 font-medium text-neutral-900 dark:text-neutral-100">
													{result.jobSeekerId ?? "-"}
												</span>
											</div>
										</div>
										{result.semanticExplanation && (
											<div className="mt-4 rounded-lg bg-green-50 p-4 dark:bg-green-900/20">
												<p className="text-sm text-green-800 dark:text-green-400">
													{result.semanticExplanation}
												</p>
											</div>
										)}
									</div>
									<div className="ml-4 flex flex-col gap-2">
										{result.notifiedAt ? (
											<span className="rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-800 dark:bg-green-900 dark:text-green-100">
												送信済み
											</span>
										) : (
											<TouchOptimizedButton
												variant="primary"
												onClick={() => alert("提案メール送信機能は現在利用できません")}
											>
												提案メール送信
											</TouchOptimizedButton>
										)}
									</div>
								</div>
							</div>
						))}
					</div>
				)}

				{/* ページネーション */}
				{matchingResults.length > 0 && (
					<div className="mt-8 flex justify-center gap-4">
						<TouchOptimizedButton
							variant="outline"
							onClick={() => setPage((p) => Math.max(1, p - 1))}
							disabled={page === 1}
						>
							前へ
						</TouchOptimizedButton>
						<span className="flex items-center text-neutral-600 dark:text-neutral-400">
							ページ {page}
						</span>
						<TouchOptimizedButton
							variant="outline"
							onClick={() => setPage((p) => p + 1)}
							disabled={matchingResults.length < limit}
						>
							次へ
						</TouchOptimizedButton>
					</div>
				)}
			</div>
		</div>
	);
}
