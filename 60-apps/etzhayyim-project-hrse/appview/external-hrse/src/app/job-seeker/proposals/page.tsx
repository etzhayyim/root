"use client";

/**
 * @etzhayyim/etzhayyim-hrse#JobSeekerProposalsConnect
 * 求職者応募管理ページ（Connect-Web版）
 */

import { useUser } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { TouchOptimizedButton } from "@/components/TouchOptimizedButton";
import {
	useJobSeekerServiceClient,
	useHiringServiceClient,
	useJobServiceClient,
	type Proposal,
	type Job,
} from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import { SearchJobSeekersRequestSchema } from "@/gen/proto/hrse/v1/job_seeker_pb";
import { ListProposalsRequestSchema, UpdateProposalRequestSchema } from "@/gen/proto/hrse/v1/hiring_pb";
import { GetJobRequestSchema } from "@/gen/proto/hrse/v1/job_pb";

export default function JobSeekerProposalsPage() {
	const { user, isLoaded } = useUser();
	const router = useRouter();
	const jobSeekerClient = useJobSeekerServiceClient();
	const hiringClient = useHiringServiceClient();
	const jobClient = useJobServiceClient();

	const [loading, setLoading] = useState(true);
	const [jobSeekerId, setJobSeekerId] = useState<string | null>(null);
	const [proposals, setProposals] = useState<Array<Proposal & { job?: Job }>>([]);

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

	// 応募一覧取得
	const fetchProposals = useCallback(async () => {
		if (!jobSeekerId) return;

		setLoading(true);
		try {
			const res = await hiringClient.listProposals(
				create(ListProposalsRequestSchema, {
					jobSeekerId,
					limit: 100,
					offset: 0,
				})
			);

			// 各応募の案件詳細を取得
			const proposalsWithJobs = await Promise.all(
				(res.proposals || []).map(async (proposal) => {
					try {
						const jobRes = await jobClient.getJob(
							create(GetJobRequestSchema, { id: proposal.jobId })
						);
						return { ...proposal, job: jobRes.job };
					} catch {
						return { ...proposal, job: undefined };
					}
				})
			);

			setProposals(proposalsWithJobs);
		} catch (error) {
			console.error("Failed to fetch proposals:", error);
		} finally {
			setLoading(false);
		}
	}, [jobSeekerId, hiringClient, jobClient]);

	useEffect(() => {
		if (user?.id) {
			fetchJobSeekerId();
		}
	}, [user?.id, fetchJobSeekerId]);

	useEffect(() => {
		if (jobSeekerId) {
			fetchProposals();
		}
	}, [jobSeekerId, fetchProposals]);

	const handleWithdraw = async (proposalId: string) => {
		if (!confirm("応募を撤回しますか？")) return;

		try {
			await hiringClient.updateProposal(
				create(UpdateProposalRequestSchema, {
					id: proposalId,
					status: "withdrawn",
				})
			);
			fetchProposals();
		} catch (error) {
			console.error("Failed to withdraw:", error);
			const message = error instanceof Error ? error.message : "応募の撤回に失敗しました";
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

	if (!jobSeekerId && !loading) {
		return (
			<div className="flex min-h-screen items-center justify-center dark:bg-neutral-950">
				<div className="text-center">
					<p className="mb-4 text-lg text-neutral-900 dark:text-neutral-100">
						プロファイルを作成してください
					</p>
					<TouchOptimizedButton variant="primary" onClick={() => router.push("/freelancer/profile")}>
						プロファイル作成
					</TouchOptimizedButton>
				</div>
			</div>
		);
	}

	const getStatusLabel = (status: string) => {
		switch (status) {
			case "pending": return "審査中";
			case "accepted": return "承認済み";
			case "rejected": return "却下";
			case "withdrawn": return "撤回";
			default: return status;
		}
	};

	const getStatusColor = (status: string) => {
		switch (status) {
			case "pending": return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100";
			case "accepted": return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100";
			case "rejected": return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100";
			case "withdrawn": return "bg-neutral-100 text-neutral-800 dark:bg-neutral-800 dark:text-neutral-100";
			default: return "bg-neutral-100 text-neutral-800 dark:bg-neutral-800 dark:text-neutral-100";
		}
	};

	return (
		<div className="min-h-screen bg-neutral-50 p-4 md:p-8 dark:bg-neutral-950">
			<div className="mx-auto max-w-7xl">
				<div className="mb-8 flex items-center justify-between">
					<div className="flex items-center gap-3">
						<h1 className="text-3xl font-bold text-neutral-900 dark:text-neutral-100">応募管理</h1>
						<span className="rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-800 dark:bg-green-900 dark:text-green-200">
							Connect-Web
						</span>
					</div>
					<TouchOptimizedButton variant="primary" onClick={() => router.push("/freelancer/jobs")}>
						案件を探す
					</TouchOptimizedButton>
				</div>

				{loading ? (
					<div className="flex items-center justify-center py-12">
						<div className="text-lg text-neutral-600 dark:text-neutral-400">読み込み中...</div>
					</div>
				) : proposals.length === 0 ? (
					<div className="rounded-lg bg-white p-12 text-center shadow dark:bg-neutral-900 dark:border dark:border-neutral-800">
						<p className="mb-4 text-neutral-600 dark:text-neutral-400">応募がありません</p>
						<TouchOptimizedButton variant="primary" onClick={() => router.push("/freelancer/jobs")}>
							案件を探す
						</TouchOptimizedButton>
					</div>
				) : (
					<div className="space-y-4">
						{proposals.map((proposal) => (
							<div
								key={proposal.id}
								className="rounded-lg bg-white p-6 shadow transition-shadow hover:shadow-lg dark:bg-neutral-900 dark:border dark:border-neutral-800"
							>
								<div className="flex items-start justify-between">
									<div className="flex-1">
										<div className="mb-2 flex items-center gap-4">
											<h3 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">
												{proposal.job?.title || "案件名不明"}
											</h3>
											<span className={`rounded-full px-3 py-1 text-sm font-medium ${getStatusColor(proposal.status)}`}>
												{getStatusLabel(proposal.status)}
											</span>
											{proposal.job && (
												<span
													className={`rounded-full px-3 py-1 text-sm font-medium ${
														proposal.job.status === "open"
															? "bg-brand-100 text-brand-800 dark:bg-brand-900 dark:text-brand-100"
															: proposal.job.status === "filled"
																? "bg-neutral-100 text-neutral-800 dark:bg-neutral-800 dark:text-neutral-100"
																: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100"
													}`}
												>
													{proposal.job.status === "open" ? "募集中" : proposal.job.status === "filled" ? "決定済み" : "募集終了"}
												</span>
											)}
										</div>

										<p className="mb-4 line-clamp-2 text-neutral-600 dark:text-neutral-400">
											{proposal.job?.description || ""}
										</p>

										{proposal.message && (
											<div className="mb-4 rounded-lg bg-neutral-50 p-4 dark:bg-neutral-800">
												<p className="text-sm font-medium text-neutral-700 dark:text-neutral-300">応募メッセージ:</p>
												<p className="mt-1 text-sm text-neutral-600 dark:text-neutral-400">{proposal.message}</p>
											</div>
										)}

										{proposal.job?.company && (
											<div className="mb-2 text-sm text-neutral-600 dark:text-neutral-400">
												企業: {proposal.job.company.name}
											</div>
										)}

										<div className="text-sm text-neutral-500 dark:text-neutral-500">
											応募日: {proposal.createdAt?.seconds ? new Date(Number(proposal.createdAt.seconds) * 1000).toLocaleDateString("ja-JP") : "-"}
										</div>
									</div>

									<div className="ml-4 flex flex-col gap-2">
										<TouchOptimizedButton
											variant="secondary"
											size="sm"
											onClick={() => router.push(`/freelancer/jobs/${proposal.jobId}`)}
										>
											詳細
										</TouchOptimizedButton>
										{proposal.status === "pending" && (
											<TouchOptimizedButton variant="danger" size="sm" onClick={() => handleWithdraw(proposal.id)}>
												撤回
											</TouchOptimizedButton>
										)}
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
