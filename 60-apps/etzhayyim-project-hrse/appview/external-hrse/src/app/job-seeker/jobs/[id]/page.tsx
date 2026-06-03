"use client";

/**
 * @etzhayyim/etzhayyim-hrse#JobSeekerJobDetailConnect
 * 求職者案件詳細ページ（Connect-Web版）
 */

import { useUser } from "@clerk/nextjs";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { TouchOptimizedButton } from "@/components/TouchOptimizedButton";
import {
	useJobServiceClient,
	useJobSeekerServiceClient,
	useHiringServiceClient,
	useMatchingServiceClient,
	type Job,
	type MatchScore,
} from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import { GetJobRequestSchema } from "@/gen/proto/hrse/v1/job_pb";
import { SearchJobSeekersRequestSchema } from "@/gen/proto/hrse/v1/job_seeker_pb";
import { CreateProposalRequestSchema } from "@/gen/proto/hrse/v1/hiring_pb";
import { GetMatchScoreRequestSchema } from "@/gen/proto/hrse/v1/matching_pb";

export default function JobDetailPage() {
	const { user, isLoaded } = useUser();
	const router = useRouter();
	const params = useParams();
	const jobId = params.id as string;

	const jobClient = useJobServiceClient();
	const jobSeekerClient = useJobSeekerServiceClient();
	const hiringClient = useHiringServiceClient();
	const matchingClient = useMatchingServiceClient();

	const [loading, setLoading] = useState(true);
	const [applying, setApplying] = useState(false);
	const [job, setJob] = useState<Job | null>(null);
	const [jobSeekerId, setJobSeekerId] = useState<string | null>(null);
	const [matchScore, setMatchScore] = useState<MatchScore | null>(null);
	const [proposalMessage, setProposalMessage] = useState("");

	// 求職者ID取得
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

	// 案件詳細取得
	const fetchJob = useCallback(async () => {
		if (!jobId) return;

		setLoading(true);
		try {
			const res = await jobClient.getJob(create(GetJobRequestSchema, { id: jobId }));
			if (res.job) {
				setJob(res.job);
			}
		} catch (error) {
			console.error("Failed to fetch job:", error);
		} finally {
			setLoading(false);
		}
	}, [jobId, jobClient]);

	// マッチスコア取得
	const fetchMatchScore = useCallback(async () => {
		if (!jobSeekerId || !jobId) return;

		try {
			const res = await matchingClient.getMatchScore(
				create(GetMatchScoreRequestSchema, {
					jobSeekerId,
					jobId,
				})
			);
			if (res.matchScore) {
				setMatchScore(res.matchScore);
			}
		} catch (error) {
			console.error("Failed to fetch match score:", error);
		}
	}, [jobSeekerId, jobId, matchingClient]);

	useEffect(() => {
		if (user?.id) {
			fetchJobSeekerId();
		}
	}, [user?.id, fetchJobSeekerId]);

	useEffect(() => {
		if (isLoaded) {
			fetchJob();
		}
	}, [isLoaded, fetchJob]);

	useEffect(() => {
		if (jobSeekerId && jobId) {
			fetchMatchScore();
		}
	}, [jobSeekerId, jobId, fetchMatchScore]);

	const handleApply = async () => {
		if (!jobSeekerId) {
			alert("プロファイルを作成してください");
			router.push("/job-seeker/profile");
			return;
		}

		setApplying(true);
		try {
			await hiringClient.createProposal(
				create(CreateProposalRequestSchema, {
					jobId,
					jobSeekerId,
					message: proposalMessage || undefined,
				})
			);
			alert("応募が完了しました");
			router.push("/job-seeker/proposals");
		} catch (error) {
			console.error("Failed to apply:", error);
			const message = error instanceof Error ? error.message : "応募に失敗しました";
			alert(message);
		} finally {
			setApplying(false);
		}
	};

	if (!isLoaded || loading) {
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

	if (!job) {
		return (
			<div className="flex min-h-screen items-center justify-center dark:bg-neutral-950 dark:text-neutral-100">
				<div className="text-lg">案件が見つかりませんでした</div>
			</div>
		);
	}

	return (
		<div className="min-h-screen bg-neutral-50 p-4 md:p-8 dark:bg-neutral-950">
			<div className="mx-auto max-w-4xl">
				<div className="mb-6">
					<TouchOptimizedButton variant="secondary" size="sm" onClick={() => router.back()}>
						← 戻る
					</TouchOptimizedButton>
				</div>

				<div className="mb-6 rounded-lg bg-white p-6 shadow dark:bg-neutral-900 dark:border dark:border-neutral-800">
					<div className="mb-4 flex items-center justify-between">
						<div className="flex items-center gap-3">
							<h1 className="text-3xl font-bold text-neutral-900 dark:text-neutral-100">{job.title}</h1>
							<span className="rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-800 dark:bg-green-900 dark:text-green-200">
								Connect-Web
							</span>
						</div>
						<span
							className={`rounded-full px-3 py-1 text-sm font-medium ${
								job.status === "open"
									? "bg-brand-100 text-brand-800 dark:bg-brand-900 dark:text-brand-100"
									: job.status === "filled"
										? "bg-neutral-100 text-neutral-800 dark:bg-neutral-800 dark:text-neutral-100"
										: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100"
							}`}
						>
							{job.status === "open" ? "募集中" : job.status === "filled" ? "決定済み" : "募集終了"}
						</span>
					</div>

					{matchScore && (
						<div className="mb-6 rounded-lg bg-green-50 p-4 dark:bg-green-900/20 dark:border dark:border-green-800">
							<div className="mb-2 flex items-center justify-between">
								<span className="text-lg font-semibold text-green-800 dark:text-green-400">マッチングスコア</span>
								<span className="text-2xl font-bold text-green-800 dark:text-green-400">
									{Math.round(matchScore.score * 100)}%
								</span>
							</div>
							{matchScore.breakdown && (
								<div className="grid grid-cols-2 gap-2 text-sm md:grid-cols-3">
									<div>
										<span className="text-neutral-600 dark:text-neutral-400">資格:</span>
										<span className="ml-2 font-medium text-neutral-900 dark:text-neutral-100">
											{Math.round(matchScore.breakdown.certificationMatch * 100)}%
										</span>
									</div>
									<div>
										<span className="text-neutral-600 dark:text-neutral-400">専門分野:</span>
										<span className="ml-2 font-medium text-neutral-900 dark:text-neutral-100">
											{Math.round(matchScore.breakdown.specializationMatch * 100)}%
										</span>
									</div>
									<div>
										<span className="text-neutral-600 dark:text-neutral-400">言語:</span>
										<span className="ml-2 font-medium text-neutral-900 dark:text-neutral-100">
											{Math.round(matchScore.breakdown.languageMatch * 100)}%
										</span>
									</div>
									<div>
										<span className="text-neutral-600 dark:text-neutral-400">単価:</span>
										<span className="ml-2 font-medium text-neutral-900 dark:text-neutral-100">
											{Math.round(matchScore.breakdown.priceRangeMatch * 100)}%
										</span>
									</div>
									<div>
										<span className="text-neutral-600 dark:text-neutral-400">リモート:</span>
										<span className="ml-2 font-medium text-neutral-900 dark:text-neutral-100">
											{Math.round(matchScore.breakdown.remoteMatch * 100)}%
										</span>
									</div>
									<div>
										<span className="text-neutral-600 dark:text-neutral-400">在留資格:</span>
										<span className="ml-2 font-medium text-neutral-900 dark:text-neutral-100">
											{Math.round(matchScore.breakdown.workPermitMatch * 100)}%
										</span>
									</div>
								</div>
							)}
						</div>
					)}

					<div className="prose max-w-none dark:prose-invert">
						<h2 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">案件説明</h2>
						<p className="whitespace-pre-wrap text-neutral-700 dark:text-neutral-300">{job.description}</p>
					</div>
				</div>

				<div className="mb-6 grid grid-cols-1 gap-6 md:grid-cols-2">
					{/* 基本情報 */}
					<div className="rounded-lg bg-white p-6 shadow dark:bg-neutral-900 dark:border dark:border-neutral-800">
						<h2 className="mb-4 text-xl font-semibold text-neutral-900 dark:text-neutral-100">基本情報</h2>
						<dl className="space-y-2">
							<div>
								<dt className="font-medium text-neutral-700 dark:text-neutral-300">勤務地</dt>
								<dd className="text-neutral-600 dark:text-neutral-400">{job.jobLocation}</dd>
							</div>
							<div>
								<dt className="font-medium text-neutral-700 dark:text-neutral-300">単価</dt>
								<dd className="text-neutral-600 dark:text-neutral-400">
									{(job.salary?.min ?? job.jobUnitPriceMin ?? 0).toLocaleString()}円
									{(job.salary?.max ?? job.jobUnitPriceMax ?? 0) !== (job.salary?.min ?? job.jobUnitPriceMin ?? 0) && (
										<> - {(job.salary?.max ?? job.jobUnitPriceMax ?? 0).toLocaleString()}円</>
									)}
								</dd>
							</div>
							<div>
								<dt className="font-medium text-neutral-700 dark:text-neutral-300">リモート</dt>
								<dd className="text-neutral-600 dark:text-neutral-400">{job.remoteAllowed ? "可" : "不可"}</dd>
							</div>
							<div>
								<dt className="font-medium text-neutral-700 dark:text-neutral-300">開始日</dt>
								<dd className="text-neutral-600 dark:text-neutral-400">{job.startDate || "未定"}</dd>
							</div>
							{job.endDate && (
								<div>
									<dt className="font-medium text-neutral-700 dark:text-neutral-300">終了日</dt>
									<dd className="text-neutral-600 dark:text-neutral-400">{job.endDate}</dd>
								</div>
							)}
							{job.company && (
								<div>
									<dt className="font-medium text-neutral-700 dark:text-neutral-300">企業</dt>
									<dd className="text-neutral-600 dark:text-neutral-400">{job.company.name}</dd>
								</div>
							)}
						</dl>
					</div>

					{/* 要件 */}
					<div className="rounded-lg bg-white p-6 shadow dark:bg-neutral-900 dark:border dark:border-neutral-800">
						<h2 className="mb-4 text-xl font-semibold text-neutral-900 dark:text-neutral-100">要件</h2>
						{job.requiredSpecializations && job.requiredSpecializations.length > 0 && (
							<div className="mb-4">
								<dt className="mb-2 font-medium text-neutral-700 dark:text-neutral-300">専門分野</dt>
								<dd className="flex flex-wrap gap-2">
									{job.requiredSpecializations.map((spec) => (
										<span
											key={spec.id}
											className="rounded-full bg-brand-100 px-3 py-1 text-sm text-brand-800 dark:bg-brand-900 dark:text-brand-100"
										>
											{spec.nameJa || spec.id}
										</span>
									))}
								</dd>
							</div>
						)}
						{job.requiredCertifications && job.requiredCertifications.length > 0 && (
							<div className="mb-4">
								<dt className="mb-2 font-medium text-neutral-700 dark:text-neutral-300">資格</dt>
								<dd className="flex flex-wrap gap-2">
									{job.requiredCertifications.map((cert) => (
										<span
											key={cert.id}
											className="rounded-full bg-neutral-100 px-3 py-1 text-sm text-neutral-800 dark:bg-neutral-800 dark:text-neutral-100"
										>
											{cert.nameJa || cert.id}
										</span>
									))}
								</dd>
							</div>
						)}
						{job.requiredLanguages && job.requiredLanguages.length > 0 && (
							<div>
								<dt className="mb-2 font-medium text-neutral-700 dark:text-neutral-300">言語</dt>
								<dd className="flex flex-wrap gap-2">
									{job.requiredLanguages.map((lang) => (
										<span
											key={lang.id}
											className="rounded-full bg-green-100 px-3 py-1 text-sm text-green-800 dark:bg-green-900 dark:text-green-100"
										>
											{lang.nameJa || lang.id}
										</span>
									))}
								</dd>
							</div>
						)}
					</div>
				</div>

				{/* 応募フォーム */}
				{job.status === "open" && (
					<div className="rounded-lg bg-white p-6 shadow dark:bg-neutral-900 dark:border dark:border-neutral-800">
						<h2 className="mb-4 text-xl font-semibold text-neutral-900 dark:text-neutral-100">応募</h2>
						<div className="space-y-4">
							<div>
								<label htmlFor="proposalMessage" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">
									応募メッセージ（任意）
								</label>
								<textarea
									id="proposalMessage"
									value={proposalMessage}
									onChange={(e) => setProposalMessage(e.target.value)}
									rows={4}
									className="input-touch mt-1 block w-full rounded-md border border-neutral-300 bg-white px-3 py-2 dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100"
									placeholder="自己紹介やアピールポイントを入力してください"
								/>
							</div>
							<div className="flex justify-end">
								<TouchOptimizedButton
									variant="primary"
									size="lg"
									onClick={handleApply}
									disabled={applying || !jobSeekerId}
								>
									{applying ? "応募中..." : "応募する"}
								</TouchOptimizedButton>
							</div>
						</div>
					</div>
				)}
			</div>
		</div>
	);
}
