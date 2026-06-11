"use client";

/**
 * @etzhayyim/etzhayyim-hrse#OrgAgencyDashboard
 * エージェンシー用ダッシュボード（Connect-Web版）
 * Apple Human Interface Guidelinesに基づくiPad最適化デザイン
 */

import { RequireAuth } from "@/lib/auth-helpers-client";
import { useUser, useOrganization } from "@clerk/nextjs";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState, useMemo } from "react";
import { useAgencyServiceClient, useMatchingServiceClient, useMailboxServiceClient } from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import { GetAgencyByClerkOrgIdRequestSchema, ListRecruitersByAgencyRequestSchema } from "@/gen/proto/hrse/v1/agency_pb";
import { ListMatchingResultsForAgencyRequestSchema } from "@/gen/proto/hrse/v1/matching_pb";
import { ListThreadsRequestSchema, CreateMailboxRequestSchema } from "@/gen/proto/hrse/v1/mailbox_pb";
import { DashboardCard, QuickAction, ActivityItem } from "@/components/dashboard/DashboardCard";
import { TouchOptimizedButton } from "@/components/TouchOptimizedButton";
import type { Agency, Recruiter, MatchingResult } from "@/lib/connect/hooks";

export default function AgencyPage() {
	return (
		<RequireAuth>
			<AgencyDashboardContent />
		</RequireAuth>
	);
}

interface DashboardStats {
	matchingCount: number;
	unnotifiedMatchingCount: number;
	threadCount: number;
	unreadThreadCount: number;
	recruiterCount: number;
}

function AgencyDashboardContent() {
	const params = useParams();
	const router = useRouter();
	const orgId = params?.orgId as string | undefined;
	const { user, isLoaded } = useUser();
	const { organization } = useOrganization();
	const agencyClient = useAgencyServiceClient();
	const matchingClient = useMatchingServiceClient();
	const mailboxClient = useMailboxServiceClient();

	const [loading, setLoading] = useState(true);
	const [agency, setAgency] = useState<Agency | null>(null);
	const [recruiters, setRecruiters] = useState<Recruiter[]>([]);
	const [recentMatches, setRecentMatches] = useState<MatchingResult[]>([]);
	const [stats, setStats] = useState<DashboardStats>({
		matchingCount: 0,
		unnotifiedMatchingCount: 0,
		threadCount: 0,
		unreadThreadCount: 0,
		recruiterCount: 0,
	});

	// 現在の時刻に基づく挨拶
	const greeting = useMemo(() => {
		const hour = new Date().getHours();
		if (hour < 12) return "おはようございます";
		if (hour < 17) return "こんにちは";
		return "こんばんは";
	}, []);

	// エージェンシープロファイル取得
	const fetchAgency = useCallback(async () => {
		if (!orgId) return null;

		try {
			const response = await agencyClient.getAgencyByClerkOrgId(
				create(GetAgencyByClerkOrgIdRequestSchema, { clerkOrgId: orgId })
			);
			return response.agency ?? null;
		} catch (error) {
			console.error("Failed to fetch agency:", error);
			return null;
		}
	}, [orgId, agencyClient]);

	// リクルーター一覧取得
	const fetchRecruiters = useCallback(async (agencyId: string) => {
		try {
			const response = await agencyClient.listRecruitersByAgency(
				create(ListRecruitersByAgencyRequestSchema, { agencyId })
			);
			return response.recruiters ?? [];
		} catch (error) {
			console.error("Failed to fetch recruiters:", error);
			return [];
		}
	}, [agencyClient]);

	// マッチング結果取得
	const fetchMatchingResults = useCallback(async (agencyId: string) => {
		try {
			const response = await matchingClient.listMatchingResultsForAgency(
				create(ListMatchingResultsForAgencyRequestSchema, {
					agencyId,
					limit: 5,
					offset: 0,
				})
			);
			return {
				results: response.matchingResults ?? [],
				total: response.total ?? 0,
			};
		} catch (error) {
			console.error("Failed to fetch matching results:", error);
			return { results: [], total: 0 };
		}
	}, [matchingClient]);

	// 未通知のマッチング数取得
	const fetchUnnotifiedMatches = useCallback(async (agencyId: string) => {
		try {
			const response = await matchingClient.listMatchingResultsForAgency(
				create(ListMatchingResultsForAgencyRequestSchema, {
					agencyId,
					limit: 1,
					offset: 0,
					notifiedOnly: false,
				})
			);
			return response.total ?? 0;
		} catch (error) {
			return 0;
		}
	}, [matchingClient]);

	// スレッド数取得
	const fetchThreadStats = useCallback(async (agencyId: string) => {
		try {
			// まずメールボックスを取得または作成
			let mailboxId: string | null = null;
			try {
				const createResponse = await mailboxClient.createMailbox(
					create(CreateMailboxRequestSchema, {
						ownerType: "organization",
						ownerId: agencyId,
					})
				);
				mailboxId = createResponse.mailbox?.id ?? null;
			} catch {
				// すでに存在する場合は無視
			}

			if (!mailboxId) {
				return { total: 0, unread: 0 };
			}

			const response = await mailboxClient.listThreads(
				create(ListThreadsRequestSchema, {
					mailboxId,
					limit: 100,
				})
			);

			const threads = response.threads ?? [];
			const unreadCount = threads.filter(t => t.unreadCount > 0).length;

			return { total: threads.length, unread: unreadCount };
		} catch (error) {
			console.error("Failed to fetch thread stats:", error);
			return { total: 0, unread: 0 };
		}
	}, [mailboxClient]);

	// データ取得
	useEffect(() => {
		const loadDashboardData = async () => {
			if (!orgId || !isLoaded) return;

			setLoading(true);
			try {
				// エージェンシー情報取得
				const agencyData = await fetchAgency();
				setAgency(agencyData);

				if (agencyData?.id) {
					// 並行してデータを取得
					const [recruiterData, matchingData, unnotifiedCount, threadStats] = await Promise.all([
						fetchRecruiters(agencyData.id),
						fetchMatchingResults(agencyData.id),
						fetchUnnotifiedMatches(agencyData.id),
						fetchThreadStats(agencyData.id),
					]);

					setRecruiters(recruiterData);
					setRecentMatches(matchingData.results);
					setStats({
						matchingCount: matchingData.total,
						unnotifiedMatchingCount: unnotifiedCount,
						threadCount: threadStats.total,
						unreadThreadCount: threadStats.unread,
						recruiterCount: recruiterData.length,
					});
				}
			} catch (error) {
				console.error("Failed to load dashboard data:", error);
			} finally {
				setLoading(false);
			}
		};

		loadDashboardData();
	}, [orgId, isLoaded, fetchAgency, fetchRecruiters, fetchMatchingResults, fetchUnnotifiedMatches, fetchThreadStats]);

	// ローディング表示
	if (!isLoaded || loading) {
		return (
			<div className="flex min-h-screen items-center justify-center">
				<div className="flex flex-col items-center gap-4">
					<div className="h-12 w-12 animate-spin rounded-full border-4 border-brand-200 border-t-brand-600 dark:border-brand-800 dark:border-t-brand-400" />
					<p className="text-lg text-neutral-600 dark:text-neutral-400">読み込み中...</p>
				</div>
			</div>
		);
	}

	// プロファイル未作成の場合
	if (!agency) {
		return (
			<div className="min-h-screen bg-neutral-50 p-4 md:p-8 dark:bg-neutral-950">
				<div className="mx-auto max-w-2xl">
					<div className="rounded-2xl bg-white p-8 shadow-lg text-center dark:bg-neutral-900 dark:border dark:border-neutral-800">
						<div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-brand-100 dark:bg-brand-900/30">
							<svg className="h-10 w-10 text-brand-600 dark:text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
							</svg>
						</div>
						<h2 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
							エージェンシープロファイルを作成
						</h2>
						<p className="mt-3 text-neutral-600 dark:text-neutral-400">
							ダッシュボードを使用するには、まずエージェンシーのプロファイルを作成してください。
						</p>
						<TouchOptimizedButton
							onClick={() => router.push(`/${orgId}/agency/profile`)}
							className="mt-6"
							size="lg"
						>
							プロファイルを作成
						</TouchOptimizedButton>
					</div>
				</div>
			</div>
		);
	}

	return (
		<div className="min-h-screen bg-neutral-50 dark:bg-neutral-950">
			<div className="mx-auto max-w-7xl px-4 py-8 md:px-6 lg:px-8">
				{/* Header */}
				<header className="mb-8">
					<div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
						<div>
							<h1 className="text-3xl font-bold text-neutral-900 dark:text-neutral-100">
								{greeting}、{user?.firstName || organization?.name || "エージェンシー"}
							</h1>
							<p className="mt-1 text-neutral-600 dark:text-neutral-400">
								{agency.name}のダッシュボード
							</p>
						</div>
						<div className="flex items-center gap-3">
							<span className="rounded-full bg-emerald-100 px-4 py-1.5 text-sm font-medium text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400">
								Connect-Web
							</span>
						</div>
					</div>
				</header>

				{/* KPI Cards */}
				<section className="mb-8">
					<div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
						<DashboardCard
							title="マッチング件数"
							value={stats.matchingCount}
							subtitle="累計マッチング"
							variant="primary"
							href={`/${orgId}/agency/matching`}
							icon={
								<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
								</svg>
							}
							trend={stats.unnotifiedMatchingCount > 0 ? {
								direction: "up",
								value: `${stats.unnotifiedMatchingCount}件 新着`,
							} : undefined}
						/>
						<DashboardCard
							title="メールスレッド"
							value={stats.threadCount}
							subtitle="アクティブな会話"
							variant="info"
							href={`/${orgId}/agency/mailbox`}
							icon={
								<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
								</svg>
							}
							trend={stats.unreadThreadCount > 0 ? {
								direction: "up",
								value: `${stats.unreadThreadCount}件 未読`,
							} : undefined}
						/>
						<DashboardCard
							title="リクルーター"
							value={stats.recruiterCount}
							subtitle="チームメンバー"
							variant="success"
							href={`/${orgId}/agency/members`}
							icon={
								<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
								</svg>
							}
						/>
						<DashboardCard
							title="AIサポート"
							value="利用可能"
							subtitle="Hume AI統合"
							variant="warning"
							href={`/${orgId}/agency/recruiter-supporter`}
							icon={
								<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
								</svg>
							}
						/>
					</div>
				</section>

				{/* Main Content Grid */}
				<div className="grid gap-8 lg:grid-cols-3">
					{/* Quick Actions */}
					<section className="lg:col-span-1">
						<h2 className="mb-4 text-lg font-semibold text-neutral-900 dark:text-neutral-100">
							クイックアクション
						</h2>
						<div className="space-y-3">
							<QuickAction
								title="マッチング結果を確認"
								description="最新のマッチング候補を確認"
								href={`/${orgId}/agency/matching`}
								icon={
									<svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
									</svg>
								}
							/>
							<QuickAction
								title="メールボックス"
								description="受信トレイを確認"
								href={`/${orgId}/agency/mailbox`}
								icon={
									<svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
									</svg>
								}
							/>
							<QuickAction
								title="プロファイル編集"
								description="エージェンシー情報を更新"
								href={`/${orgId}/agency/profile`}
								icon={
									<svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
									</svg>
								}
							/>
							<QuickAction
								title="メンバー招待"
								description="新しいリクルーターを招待"
								href={`/${orgId}/agency/members/invite`}
								icon={
									<svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
									</svg>
								}
							/>
							<QuickAction
								title="AIサポートに相談"
								description="業務のアドバイスを受ける"
								href={`/${orgId}/agency/recruiter-supporter`}
								icon={
									<svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
									</svg>
								}
							/>
						</div>
					</section>

					{/* Recent Matching Results */}
					<section className="lg:col-span-2">
						<div className="flex items-center justify-between mb-4">
							<h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
								最近のマッチング結果
							</h2>
							<TouchOptimizedButton
								variant="outline"
								size="sm"
								onClick={() => router.push(`/${orgId}/agency/matching`)}
							>
								すべて表示
							</TouchOptimizedButton>
						</div>
						<div className="rounded-2xl border border-neutral-200 bg-white shadow-sm dark:border-neutral-800 dark:bg-neutral-900">
							{recentMatches.length === 0 ? (
								<div className="flex flex-col items-center justify-center py-12 px-4 text-center">
									<div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-neutral-100 dark:bg-neutral-800">
										<svg className="h-8 w-8 text-neutral-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
										</svg>
									</div>
									<p className="text-neutral-600 dark:text-neutral-400">
										マッチング結果がありません
									</p>
									<p className="mt-1 text-sm text-neutral-500">
										求職者と案件が登録されると、マッチングが自動的に行われます
									</p>
								</div>
							) : (
								<div className="divide-y divide-neutral-100 dark:divide-neutral-800">
									{recentMatches.map((match) => (
										<div
											key={match.id}
											className="flex items-center gap-4 p-4 transition-colors hover:bg-neutral-50 dark:hover:bg-neutral-800/50"
										>
											<div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-emerald-400 to-emerald-600 text-lg font-bold text-white shadow-md">
												{Math.round(match.totalScore * 100)}
											</div>
											<div className="flex-1 min-w-0">
												<h4 className="font-medium text-neutral-900 dark:text-neutral-100 truncate">
													{match.job?.title ?? "案件名不明"}
												</h4>
												<p className="text-sm text-neutral-600 dark:text-neutral-400 truncate">
													{match.job?.description ?? "詳細なし"}
												</p>
												<div className="mt-1 flex items-center gap-3 text-xs text-neutral-500">
													<span>{match.job?.jobLocation ?? "勤務地不明"}</span>
													<span>•</span>
													<span>
														{match.job?.salary?.min ?? match.job?.jobUnitPriceMin ?? 0}円 〜
													</span>
												</div>
											</div>
											<div className="shrink-0">
												{match.notifiedAt ? (
													<span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-medium text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400">
														送信済み
													</span>
												) : (
													<span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
														未送信
													</span>
												)}
											</div>
										</div>
									))}
								</div>
							)}
						</div>
					</section>
				</div>

				{/* Agency Info Card */}
				<section className="mt-8">
					<div className="rounded-2xl border border-neutral-200 bg-white p-6 shadow-sm dark:border-neutral-800 dark:bg-neutral-900">
						<div className="flex items-start justify-between">
							<div>
								<h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
									{agency.name}
								</h3>
								<div className="mt-3 grid gap-2 text-sm text-neutral-600 dark:text-neutral-400 sm:grid-cols-2 lg:grid-cols-4">
									{agency.licenseNumber && (
										<div className="flex items-center gap-2">
											<svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
												<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
											</svg>
											<span>許可番号: {agency.licenseNumber}</span>
										</div>
									)}
									{agency.contactEmail && (
										<div className="flex items-center gap-2">
											<svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
												<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
											</svg>
											<span>{agency.contactEmail}</span>
										</div>
									)}
									{agency.contactPhone && (
										<div className="flex items-center gap-2">
											<svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
												<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
											</svg>
											<span>{agency.contactPhone}</span>
										</div>
									)}
									{agency.address && (
										<div className="flex items-center gap-2">
											<svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
												<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
												<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
											</svg>
											<span className="truncate">{agency.address}</span>
										</div>
									)}
								</div>
							</div>
							<TouchOptimizedButton
								variant="outline"
								size="sm"
								onClick={() => router.push(`/${orgId}/agency/profile`)}
							>
								編集
							</TouchOptimizedButton>
						</div>
					</div>
				</section>
			</div>
		</div>
	);
}
