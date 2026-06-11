"use client";

/**
 * @etzhayyim/etzhayyim-hrse#AdminJobDetailConnect
 * 管理画面向け案件詳細ページ（Connect-Web版）
 */

import { useUser } from "@clerk/nextjs";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { TouchOptimizedButton } from "@/components/TouchOptimizedButton";
import { useJobServiceClient, type Job } from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import { GetJobRequestSchema } from "@/gen/proto/hrse/v1/job_pb";

export default function AdminJobDetailPage() {
	const { user, isLoaded } = useUser();
	const router = useRouter();
	const params = useParams();
	const jobId = params.id as string;
	const jobClient = useJobServiceClient();

	const [loading, setLoading] = useState(true);
	const [job, setJob] = useState<Job | null>(null);
	const [error, setError] = useState<string | null>(null);

	const fetchJob = useCallback(async () => {
		if (!jobId) return;

		setLoading(true);
		setError(null);
		try {
			const res = await jobClient.getJob(create(GetJobRequestSchema, { id: jobId }));
			if (res.job) {
				setJob(res.job);
			}
		} catch (err) {
			console.error("Failed to fetch job:", err);
			setError(err instanceof Error ? err.message : "案件の取得に失敗しました");
		} finally {
			setLoading(false);
		}
	}, [jobId, jobClient]);

	useEffect(() => {
		if (isLoaded && jobId) {
			fetchJob();
		}
	}, [isLoaded, jobId, fetchJob]);

	if (!isLoaded || loading) {
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

	if (error) {
		return (
			<div className="flex min-h-screen items-center justify-center">
				<div className="text-lg text-red-600">エラーが発生しました: {error}</div>
			</div>
		);
	}

	if (!job) {
		return (
			<div className="flex min-h-screen items-center justify-center">
				<div className="text-lg">案件が見つかりませんでした</div>
			</div>
		);
	}

	const getStatusLabel = (status: string) => {
		switch (status) {
			case "open": return "募集中";
			case "filled": return "決定済み";
			case "closed": return "募集終了";
			default: return status;
		}
	};

	const getStatusColor = (status: string) => {
		switch (status) {
			case "open": return "bg-brand-100 text-brand-800";
			case "filled": return "bg-neutral-100 text-neutral-800";
			case "closed": return "bg-red-100 text-red-800";
			default: return "bg-neutral-100 text-neutral-800";
		}
	};

	return (
		<div className="min-h-screen bg-gradient-to-b from-neutral-50 to-white px-4 py-6 md:px-8 md:py-10 lg:px-12 dark:from-neutral-950 dark:to-neutral-900">
			<div className="mx-auto max-w-6xl">
				{/* ヘッダー */}
				<div className="mb-8 flex items-center justify-between">
					<TouchOptimizedButton
						variant="secondary"
						size="md"
						onClick={() => router.back()}
						className="flex items-center gap-2"
					>
						<svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
						</svg>
						戻る
					</TouchOptimizedButton>
					<span className="rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-800 dark:bg-green-900 dark:text-green-200">
						Connect-Web
					</span>
				</div>

				{/* メインカード */}
				<div className="mb-8 overflow-hidden rounded-2xl bg-white shadow-lg ring-1 ring-neutral-200/50 dark:bg-neutral-900 dark:ring-neutral-800">
					<div className="border-b border-neutral-100 bg-gradient-to-r from-neutral-50 to-white px-8 py-6 dark:border-neutral-800 dark:from-neutral-900 dark:to-neutral-800">
						<div className="flex items-start justify-between gap-4">
							<div className="flex-1">
								<h1 className="mb-3 text-3xl font-bold tracking-tight text-neutral-900 dark:text-neutral-100 md:text-4xl">
									{job.title}
								</h1>
								<div className="flex flex-wrap items-center gap-3">
									<span className={`inline-flex items-center rounded-full px-4 py-1.5 text-sm font-semibold shadow-sm ${getStatusColor(job.status)}`}>
										{getStatusLabel(job.status)}
									</span>
								</div>
							</div>
						</div>
					</div>

					<div className="px-8 py-6 dark:text-neutral-200">
						<h2 className="mb-4 text-lg font-semibold text-neutral-900 dark:text-neutral-100">案件説明</h2>
						<p className="whitespace-pre-wrap text-base leading-7 text-neutral-700 dark:text-neutral-300">{job.description}</p>
					</div>
				</div>

				{/* 情報グリッド */}
				<div className="mb-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
					{/* 基本情報 */}
					<div className="overflow-hidden rounded-xl bg-white shadow-md ring-1 ring-neutral-200/50 dark:bg-neutral-900 dark:ring-neutral-800">
						<div className="border-b border-neutral-100 bg-neutral-50/50 px-6 py-4 dark:border-neutral-800 dark:bg-neutral-800/50">
							<h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">基本情報</h2>
						</div>
						<dl className="divide-y divide-neutral-100 px-6 py-4 dark:divide-neutral-800">
							<div className="py-3">
								<dt className="mb-1 text-xs font-medium uppercase tracking-wide text-neutral-500 dark:text-neutral-400">勤務地</dt>
								<dd className="text-base font-medium text-neutral-900 dark:text-neutral-100">{job.jobLocation}</dd>
							</div>
							<div className="py-3">
								<dt className="mb-1 text-xs font-medium uppercase tracking-wide text-neutral-500 dark:text-neutral-400">単価</dt>
								<dd className="text-base font-semibold text-neutral-900 dark:text-neutral-100">
									{(job.salary?.min ?? job.jobUnitPriceMin ?? 0).toLocaleString()}円
									{(job.salary?.max ?? job.jobUnitPriceMax ?? 0) !== (job.salary?.min ?? job.jobUnitPriceMin ?? 0) && (
										<span className="text-neutral-600 dark:text-neutral-400"> 〜 {(job.salary?.max ?? job.jobUnitPriceMax ?? 0).toLocaleString()}円</span>
									)}
								</dd>
							</div>
							<div className="py-3">
								<dt className="mb-1 text-xs font-medium uppercase tracking-wide text-neutral-500 dark:text-neutral-400">リモート</dt>
								<dd className="text-base font-medium text-neutral-900 dark:text-neutral-100">
									<span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
										job.remoteAllowed ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200" : "bg-neutral-100 text-neutral-800 dark:bg-neutral-800 dark:text-neutral-200"
									}`}>
										{job.remoteAllowed ? "可" : "不可"}
									</span>
								</dd>
							</div>
							<div className="py-3">
								<dt className="mb-1 text-xs font-medium uppercase tracking-wide text-neutral-500 dark:text-neutral-400">開始日</dt>
								<dd className="text-base font-medium text-neutral-900 dark:text-neutral-100">{job.startDate || "未定"}</dd>
							</div>
							{job.endDate && (
								<div className="py-3">
									<dt className="mb-1 text-xs font-medium uppercase tracking-wide text-neutral-500 dark:text-neutral-400">終了日</dt>
									<dd className="text-base font-medium text-neutral-900 dark:text-neutral-100">{job.endDate}</dd>
								</div>
							)}
						</dl>
					</div>

					{/* システム情報 */}
					<div className="overflow-hidden rounded-xl bg-white shadow-md ring-1 ring-neutral-200/50 dark:bg-neutral-900 dark:ring-neutral-800">
						<div className="border-b border-neutral-100 bg-neutral-50/50 px-6 py-4 dark:border-neutral-800 dark:bg-neutral-800/50">
							<h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">システム情報</h2>
						</div>
						<dl className="divide-y divide-neutral-100 px-6 py-4 dark:divide-neutral-800">
							<div className="py-3">
								<dt className="mb-1 text-xs font-medium uppercase tracking-wide text-neutral-500 dark:text-neutral-400">Job ID</dt>
								<dd className="break-all font-mono text-sm text-neutral-700 dark:text-neutral-300">{job.id}</dd>
							</div>
							<div className="py-3">
								<dt className="mb-1 text-xs font-medium uppercase tracking-wide text-neutral-500 dark:text-neutral-400">Posted By ID</dt>
								<dd className="break-all font-mono text-sm text-neutral-700 dark:text-neutral-300">{job.postedById}</dd>
							</div>
							<div className="py-3">
								<dt className="mb-1 text-xs font-medium uppercase tracking-wide text-neutral-500 dark:text-neutral-400">Company ID</dt>
								<dd className="break-all font-mono text-sm text-neutral-700 dark:text-neutral-300">{job.companyId}</dd>
							</div>
							<div className="py-3">
								<dt className="mb-1 text-xs font-medium uppercase tracking-wide text-neutral-500 dark:text-neutral-400">作成日時</dt>
								<dd className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
									{job.createdAt?.seconds ? new Date(Number(job.createdAt.seconds) * 1000).toLocaleString("ja-JP") : "-"}
								</dd>
							</div>
							<div className="py-3">
								<dt className="mb-1 text-xs font-medium uppercase tracking-wide text-neutral-500 dark:text-neutral-400">更新日時</dt>
								<dd className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
									{job.updatedAt?.seconds ? new Date(Number(job.updatedAt.seconds) * 1000).toLocaleString("ja-JP") : "-"}
								</dd>
							</div>
						</dl>
					</div>
				</div>

				{/* 要件セクション */}
				<div className="overflow-hidden rounded-xl bg-white shadow-md ring-1 ring-neutral-200/50 dark:bg-neutral-900 dark:ring-neutral-800">
					<div className="border-b border-neutral-100 bg-neutral-50/50 px-6 py-4 dark:border-neutral-800 dark:bg-neutral-800/50">
						<h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">要件</h2>
					</div>
					<div className="px-6 py-6">
						<div className="space-y-6">
							{job.requiredSpecializations && job.requiredSpecializations.length > 0 && (
								<div>
									<h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-neutral-500 dark:text-neutral-400">専門分野</h3>
									<div className="flex flex-wrap gap-2">
										{job.requiredSpecializations.map((req) => (
											<span key={req.id} className="inline-flex items-center rounded-lg bg-blue-50 px-3 py-1.5 text-sm font-medium text-blue-700 ring-1 ring-inset ring-blue-600/20 dark:bg-blue-900/20 dark:text-blue-300">
												{req.nameJa || req.nameEn || req.id}
											</span>
										))}
									</div>
								</div>
							)}
							{job.requiredCertifications && job.requiredCertifications.length > 0 && (
								<div>
									<h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-neutral-500 dark:text-neutral-400">資格</h3>
									<div className="flex flex-wrap gap-2">
										{job.requiredCertifications.map((req) => (
											<span key={req.id} className="inline-flex items-center rounded-lg bg-red-50 px-3 py-1.5 text-sm font-medium text-red-700 ring-1 ring-inset ring-red-600/20 dark:bg-red-900/20 dark:text-red-300">
												{req.nameJa || req.nameEn || req.id}
											</span>
										))}
									</div>
								</div>
							)}
							{job.requiredLanguages && job.requiredLanguages.length > 0 && (
								<div>
									<h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-neutral-500 dark:text-neutral-400">言語</h3>
									<div className="flex flex-wrap gap-2">
										{job.requiredLanguages.map((req) => (
											<span key={req.id} className="inline-flex items-center rounded-lg bg-green-50 px-3 py-1.5 text-sm font-medium text-green-700 ring-1 ring-inset ring-green-600/20 dark:bg-green-900/20 dark:text-green-300">
												{req.nameJa || req.nameEn || req.id}
											</span>
										))}
									</div>
								</div>
							)}
							{(!job.requiredSpecializations || job.requiredSpecializations.length === 0) &&
								(!job.requiredCertifications || job.requiredCertifications.length === 0) &&
								(!job.requiredLanguages || job.requiredLanguages.length === 0) && (
									<div className="py-8 text-center">
										<p className="text-sm text-neutral-500 dark:text-neutral-400">要件情報がありません</p>
									</div>
								)}
						</div>
					</div>
				</div>
			</div>
		</div>
	);
}
