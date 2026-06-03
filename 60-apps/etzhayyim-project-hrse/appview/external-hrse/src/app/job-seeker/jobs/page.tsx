"use client";

/**
 * @etzhayyim/etzhayyim-hrse#JobSeekerJobsConnect
 * 求職者向け案件検索・一覧ページ（Connect-Web版）
 */

import { useUser } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { TouchOptimizedButton } from "@/components/TouchOptimizedButton";
import {
	useJobServiceClient,
	useJobSeekerServiceClient,
	useHiringServiceClient,
	type Job,
} from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import {
	ListJobsRequestSchema,
} from "@/gen/proto/hrse/v1/job_pb";
import {
	SearchJobSeekersRequestSchema,
} from "@/gen/proto/hrse/v1/job_seeker_pb";
import {
	CreateProposalRequestSchema,
	ListProposalsRequestSchema,
} from "@/gen/proto/hrse/v1/hiring_pb";

export default function JobSeekerJobsPage() {
	const { user, isLoaded } = useUser();
	const router = useRouter();
	const jobClient = useJobServiceClient();
	const jobSeekerClient = useJobSeekerServiceClient();
	const hiringClient = useHiringServiceClient();

	const [loading, setLoading] = useState(true);
	const [jobs, setJobs] = useState<Job[]>([]);
	const [jobSeekerId, setJobSeekerId] = useState<string | null>(null);
	const [appliedJobIds, setAppliedJobIds] = useState<Set<string>>(new Set());
	const [filters, setFilters] = useState({
		remoteAllowed: undefined as boolean | undefined,
		status: "open" as string | undefined,
	});
	const [page, setPage] = useState(1);
	const limit = 20;

	// 求職者IDを取得
	const fetchJobSeekerId = useCallback(async () => {
		if (!user?.id) return;

		try {
			const res = await jobSeekerClient.searchJobSeekers(
				create(SearchJobSeekersRequestSchema, { limit: 1000 })
			);
			const found = res.jobSeekers?.find((js) => js.userId === user.id);
			if (found) {
				setJobSeekerId(found.id);
			}
		} catch (error) {
			console.error("Failed to fetch job seeker:", error);
		}
	}, [user?.id, jobSeekerClient]);

	// 応募済み案件IDを取得
	const fetchAppliedJobs = useCallback(async () => {
		if (!jobSeekerId) return;

		try {
			const res = await hiringClient.listProposals(
				create(ListProposalsRequestSchema, {
					jobSeekerId,
					limit: 1000,
					offset: 0,
				})
			);
			const appliedIds = new Set((res.proposals || []).map((p) => p.jobId));
			setAppliedJobIds(appliedIds);
		} catch (error) {
			console.error("Failed to fetch applied jobs:", error);
		}
	}, [jobSeekerId, hiringClient]);

	// 案件一覧を取得
	const fetchJobs = useCallback(async () => {
		setLoading(true);
		try {
			const res = await jobClient.listJobs(
				create(ListJobsRequestSchema, {
					status: filters.status,
					limit,
					offset: (page - 1) * limit,
				})
			);

			let filteredJobs = res.jobs || [];

			// リモートフィルター
			if (filters.remoteAllowed !== undefined) {
				filteredJobs = filteredJobs.filter((j) => j.remoteAllowed === filters.remoteAllowed);
			}

			setJobs(filteredJobs);
		} catch (error) {
			console.error("Failed to fetch jobs:", error);
		} finally {
			setLoading(false);
		}
	}, [jobClient, filters, page]);

	useEffect(() => {
		if (user?.id) {
			fetchJobSeekerId();
		}
	}, [user?.id, fetchJobSeekerId]);

	useEffect(() => {
		if (jobSeekerId) {
			fetchAppliedJobs();
		}
	}, [jobSeekerId, fetchAppliedJobs]);

	useEffect(() => {
		if (isLoaded) {
			fetchJobs();
		}
	}, [isLoaded, fetchJobs]);

	const handleApply = async (jobId: string) => {
		if (!jobSeekerId) {
			alert("プロファイルを作成してください");
			router.push("/job-seeker/profile");
			return;
		}

		try {
			await hiringClient.createProposal(
				create(CreateProposalRequestSchema, {
					jobId,
					jobSeekerId,
					message: "",
				})
			);
			alert("応募が完了しました");
			fetchJobs();
			fetchAppliedJobs();
		} catch (error) {
			console.error("Failed to apply:", error);
			const message = error instanceof Error ? error.message : "応募に失敗しました";
			alert(message);
		}
	};

	if (!isLoaded) {
		return (
			<div className="flex min-h-screen items-center justify-center dark:bg-neutral-950 dark:text-neutral-100">
				<div className="text-lg">読み込み中...</div>
			</div>
		);
	}

	if (!user) {
		router.push("/auth/signin");
		return null;
	}

	return (
		<div className="min-h-screen bg-neutral-50 px-4 py-8 md:px-6 lg:px-8 dark:bg-neutral-950">
			<div className="mx-auto max-w-7xl">
				<div className="mb-8 flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
					<div>
						<div className="flex items-center gap-3">
							<h1 className="text-3xl font-bold text-neutral-900 dark:text-neutral-100">
								案件検索
							</h1>
							<span className="rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-800 dark:bg-green-900 dark:text-green-200">
								Connect-Web
							</span>
						</div>
						<p className="mt-2 text-neutral-600 dark:text-neutral-400">
							あなたに最適な案件を見つけましょう
						</p>
					</div>
					<TouchOptimizedButton
						variant="secondary"
						onClick={() => router.push("/freelancer/profile")}
					>
						プロファイル編集
					</TouchOptimizedButton>
				</div>

				{/* 検索フィルタ */}
				<div className="card-elevated mb-6">
					<h2 className="mb-4 text-xl font-semibold text-neutral-900 dark:text-neutral-100">
						検索条件
					</h2>
					<div className="grid grid-cols-1 gap-4 md:grid-cols-3">
						<div>
							<label htmlFor="remoteFilter" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">
								リモート
							</label>
							<select
								id="remoteFilter"
								value={filters.remoteAllowed === undefined ? "all" : filters.remoteAllowed.toString()}
								onChange={(e) =>
									setFilters({
										...filters,
										remoteAllowed: e.target.value === "all" ? undefined : e.target.value === "true",
									})
								}
								className="input-touch mt-1 block w-full rounded-md border border-neutral-300 bg-white focus:border-brand-500 focus:ring-brand-500 dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100"
							>
								<option value="all">すべて</option>
								<option value="true">リモート可</option>
								<option value="false">リモート不可</option>
							</select>
						</div>

						<div>
							<label htmlFor="statusFilter" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">
								ステータス
							</label>
							<select
								id="statusFilter"
								value={filters.status || "all"}
								onChange={(e) =>
									setFilters({
										...filters,
										status: e.target.value === "all" ? undefined : e.target.value,
									})
								}
								className="input-touch mt-1 block w-full rounded-md border border-neutral-300 bg-white focus:border-brand-500 focus:ring-brand-500 dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100"
							>
								<option value="all">すべて</option>
								<option value="open">募集中</option>
								<option value="closed">募集終了</option>
								<option value="filled">決定済み</option>
							</select>
						</div>
					</div>

					<div className="mt-6">
						<TouchOptimizedButton variant="primary" onClick={() => { setPage(1); fetchJobs(); }}>
							検索
						</TouchOptimizedButton>
					</div>
				</div>

				{/* 案件一覧 */}
				{loading ? (
					<div className="flex items-center justify-center py-12">
						<div className="text-lg text-neutral-600 dark:text-neutral-400">読み込み中...</div>
					</div>
				) : jobs.length === 0 ? (
					<div className="card-elevated p-12 text-center">
						<p className="text-neutral-600 dark:text-neutral-400">案件が見つかりませんでした</p>
					</div>
				) : (
					<div className="space-y-4">
						{jobs.map((job) => (
							<div
								key={job.id}
								className="card-interactive cursor-pointer"
								onClick={() => router.push(`/freelancer/jobs/${job.id}`)}
							>
								<div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
									<div className="flex-1">
										<div className="mb-3 flex flex-wrap items-center gap-3">
											<h3 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">
												{job.title}
											</h3>
											<span
												className={`rounded-full px-3 py-1 text-xs font-medium ${
													job.status === "open"
														? "bg-brand-100 text-brand-800 dark:bg-brand-900 dark:text-brand-100"
														: job.status === "filled"
															? "bg-neutral-100 text-neutral-800 dark:bg-neutral-800 dark:text-neutral-100"
															: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100"
												}`}
											>
												{job.status === "open" ? "募集中" : job.status === "filled" ? "決定済み" : "募集終了"}
											</span>
											{appliedJobIds.has(job.id) && (
												<span className="rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-800 dark:bg-green-900 dark:text-green-200">
													応募済み
												</span>
											)}
										</div>

										<p className="mb-4 line-clamp-2 text-neutral-600 dark:text-neutral-400">
											{job.description}
										</p>

										<div className="grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
											<div>
												<span className="font-medium text-neutral-700 dark:text-neutral-300">勤務地:</span>
												<span className="ml-2 text-neutral-600 dark:text-neutral-400">{job.jobLocation}</span>
											</div>
											<div>
												<span className="font-medium text-neutral-700 dark:text-neutral-300">単価:</span>
												<span className="ml-2 font-semibold text-brand-600 dark:text-brand-400">
													{(job.salary?.min ?? job.jobUnitPriceMin ?? 0).toLocaleString()}円
													{(job.salary?.max ?? job.jobUnitPriceMax ?? 0) !== (job.salary?.min ?? job.jobUnitPriceMin ?? 0) && (
														<> - {(job.salary?.max ?? job.jobUnitPriceMax ?? 0).toLocaleString()}円</>
													)}
												</span>
											</div>
											<div>
												<span className="font-medium text-neutral-700 dark:text-neutral-300">リモート:</span>
												<span className="ml-2 text-neutral-600 dark:text-neutral-400">
													{job.remoteAllowed ? "可" : "不可"}
												</span>
											</div>
											<div>
												<span className="font-medium text-neutral-700 dark:text-neutral-300">開始日:</span>
												<span className="ml-2 text-neutral-600 dark:text-neutral-400">
													{job.startDate || "未定"}
												</span>
											</div>
										</div>

										{job.company && (
											<div className="mt-4 text-sm">
												<span className="font-medium text-neutral-700 dark:text-neutral-300">企業:</span>
												<span className="ml-2 text-neutral-600 dark:text-neutral-400">{job.company.name}</span>
											</div>
										)}
									</div>

									<div className="flex flex-row gap-2 md:flex-col" onClick={(e) => e.stopPropagation()}>
										<TouchOptimizedButton
											variant="secondary"
											size="md"
											onClick={() => router.push(`/freelancer/jobs/${job.id}`)}
										>
											詳細
										</TouchOptimizedButton>
										{job.status === "open" && !appliedJobIds.has(job.id) && (
											<TouchOptimizedButton
												variant="primary"
												size="md"
												onClick={() => handleApply(job.id)}
											>
												応募
											</TouchOptimizedButton>
										)}
										{appliedJobIds.has(job.id) && (
											<TouchOptimizedButton
												variant="secondary"
												size="md"
												disabled
												className="opacity-60 cursor-not-allowed"
											>
												応募済み
											</TouchOptimizedButton>
										)}
									</div>
								</div>
							</div>
						))}
					</div>
				)}

				{/* ページネーション */}
				{jobs.length > 0 && (
					<div className="mt-8 flex items-center justify-center gap-4">
						<TouchOptimizedButton
							variant="secondary"
							size="md"
							onClick={() => setPage((p) => Math.max(1, p - 1))}
							disabled={page === 1}
						>
							前へ
						</TouchOptimizedButton>
						<span className="px-4 py-2 text-neutral-700 dark:text-neutral-300">ページ {page}</span>
						<TouchOptimizedButton
							variant="secondary"
							size="md"
							onClick={() => setPage((p) => p + 1)}
							disabled={jobs.length < limit}
						>
							次へ
						</TouchOptimizedButton>
					</div>
				)}
			</div>
		</div>
	);
}
