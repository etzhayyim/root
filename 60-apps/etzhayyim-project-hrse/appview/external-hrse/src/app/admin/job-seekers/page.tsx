"use client";

/**
 * @etzhayyim/etzhayyim-hrse#AdminJobSeekersConnect
 * 求職者管理ページ（Connect-Web版）
 */

import { useUser } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { TouchOptimizedButton } from "@/components/TouchOptimizedButton";
import { useJobSeekerServiceClient, type JobSeeker } from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import {
	SearchJobSeekersRequestSchema,
	GetJobSeekerProfileRequestSchema,
} from "@/gen/proto/hrse/v1/job_seeker_pb";
import Link from "next/link";

export default function JobSeekersAdminPage() {
	const { user, isLoaded } = useUser();
	const router = useRouter();
	const jobSeekerClient = useJobSeekerServiceClient();

	const [jobSeekers, setJobSeekers] = useState<JobSeeker[]>([]);
	const [selectedJobSeeker, setSelectedJobSeeker] = useState<JobSeeker | null>(null);
	const [loading, setLoading] = useState(true);
	const [currentPage, setCurrentPage] = useState(1);
	const [error, setError] = useState<string | null>(null);
	const itemsPerPage = 20;

	const fetchJobSeekers = useCallback(async () => {
		setLoading(true);
		try {
			const res = await jobSeekerClient.searchJobSeekers(
				create(SearchJobSeekersRequestSchema, {
					limit: itemsPerPage,
					offset: (currentPage - 1) * itemsPerPage,
				})
			);
			setJobSeekers(res.jobSeekers || []);
		} catch (err) {
			console.error("Failed to fetch job seekers:", err);
			setError(err instanceof Error ? err.message : "求職者の取得に失敗しました");
		} finally {
			setLoading(false);
		}
	}, [jobSeekerClient, currentPage]);

	const fetchJobSeekerDetails = useCallback(async (jobSeekerId: string) => {
		try {
			const res = await jobSeekerClient.getJobSeekerProfile(
				create(GetJobSeekerProfileRequestSchema, { id: jobSeekerId })
			);
			if (res.jobSeeker) {
				setSelectedJobSeeker(res.jobSeeker);
			}
		} catch (err) {
			console.error("Failed to fetch job seeker details:", err);
		}
	}, [jobSeekerClient]);

	useEffect(() => {
		if (isLoaded && user) {
			fetchJobSeekers();
		}
	}, [isLoaded, user, fetchJobSeekers]);

	const handleSelectJobSeeker = (jobSeeker: JobSeeker) => {
		setSelectedJobSeeker(jobSeeker);
		setError(null);
	};

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

	return (
		<div className="min-h-screen bg-gray-50 p-4 md:p-8 dark:bg-neutral-950">
			<div className="mx-auto max-w-7xl">
				<div className="mb-6 flex items-center justify-between">
					<div className="flex items-center gap-3">
						<h1 className="text-3xl font-bold text-gray-900 dark:text-neutral-100">求職者管理</h1>
						<span className="rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-800 dark:bg-green-900 dark:text-green-200">
							Connect-Web
						</span>
					</div>
					<Link href="/admin">
						<TouchOptimizedButton variant="secondary" size="sm">管理者トップへ</TouchOptimizedButton>
					</Link>
				</div>

				{error && (
					<div className="mb-4 rounded-lg bg-red-50 p-4 text-red-800 dark:bg-red-900/20 dark:text-red-400">{error}</div>
				)}

				<div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
					{/* 左側: 求職者一覧 */}
					<div className="rounded-lg bg-white shadow dark:bg-neutral-900">
						<div className="border-b border-gray-200 p-4 dark:border-neutral-800">
							<h2 className="text-xl font-semibold text-gray-900 dark:text-neutral-100">求職者一覧</h2>
						</div>

						{jobSeekers.length === 0 ? (
							<div className="p-12 text-center">
								<p className="text-gray-600 dark:text-neutral-400">求職者がありません</p>
							</div>
						) : (
							<div className="divide-y divide-gray-200 dark:divide-neutral-800">
								{jobSeekers.map((jobSeeker) => (
									<button
										key={jobSeeker.id}
										type="button"
										onClick={() => handleSelectJobSeeker(jobSeeker)}
										className={`w-full p-4 text-left transition-colors hover:bg-gray-50 dark:hover:bg-neutral-800 ${
											selectedJobSeeker?.id === jobSeeker.id ? "bg-blue-50 dark:bg-blue-900/20" : ""
										}`}
									>
										<div className="font-semibold text-gray-900 dark:text-neutral-100">ID: {jobSeeker.id}</div>
										{jobSeeker.specializations && jobSeeker.specializations.length > 0 && (
											<div className="mt-1 text-sm text-gray-600 dark:text-neutral-400">
												専門分野: {jobSeeker.specializations.map((s) => s.nameJa).join(", ")}
											</div>
										)}
										{jobSeeker.certifications && jobSeeker.certifications.length > 0 && (
											<div className="mt-1 text-sm text-gray-600 dark:text-neutral-400">
												資格: {jobSeeker.certifications.map((c) => c.nameJa).join(", ")}
											</div>
										)}
									</button>
								))}
							</div>
						)}

						{/* ページネーション */}
						{jobSeekers.length > 0 && (
							<div className="border-t border-gray-200 p-4 dark:border-neutral-800">
								<div className="flex items-center justify-between">
									<TouchOptimizedButton
										variant="secondary"
										size="sm"
										onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
										disabled={currentPage === 1}
									>
										前へ
									</TouchOptimizedButton>
									<span className="text-sm text-gray-600 dark:text-neutral-400">ページ {currentPage}</span>
									<TouchOptimizedButton
										variant="secondary"
										size="sm"
										onClick={() => setCurrentPage((p) => p + 1)}
										disabled={jobSeekers.length < itemsPerPage}
									>
										次へ
									</TouchOptimizedButton>
								</div>
							</div>
						)}
					</div>

					{/* 右側: 詳細表示 */}
					<div className="rounded-lg bg-white shadow dark:bg-neutral-900">
						<div className="border-b border-gray-200 p-4 dark:border-neutral-800">
							<h2 className="text-xl font-semibold text-gray-900 dark:text-neutral-100">詳細</h2>
						</div>

						{selectedJobSeeker ? (
							<div className="p-6">
								<div className="space-y-4">
									<div>
										<label className="block text-sm font-medium text-gray-700 dark:text-neutral-300">ID</label>
										<div className="mt-1 text-sm text-gray-900 dark:text-neutral-100">{selectedJobSeeker.id}</div>
									</div>
									<div>
										<label className="block text-sm font-medium text-gray-700 dark:text-neutral-300">ユーザーID</label>
										<div className="mt-1 text-sm text-gray-900 dark:text-neutral-100">{selectedJobSeeker.userId}</div>
									</div>
									<div>
										<label className="block text-sm font-medium text-gray-700 dark:text-neutral-300">雇用形態</label>
										<div className="mt-1 text-sm text-gray-900 dark:text-neutral-100">{selectedJobSeeker.employmentType}</div>
									</div>
									{selectedJobSeeker.nationality && (
										<div>
											<label className="block text-sm font-medium text-gray-700 dark:text-neutral-300">国籍</label>
											<div className="mt-1 text-sm text-gray-900 dark:text-neutral-100">{selectedJobSeeker.nationality.nameJa}</div>
										</div>
									)}
									{selectedJobSeeker.workPermit && (
										<div>
											<label className="block text-sm font-medium text-gray-700 dark:text-neutral-300">在留資格</label>
											<div className="mt-1 text-sm text-gray-900 dark:text-neutral-100">{selectedJobSeeker.workPermit.nameJa}</div>
										</div>
									)}
									<div>
										<label className="block text-sm font-medium text-gray-700 dark:text-neutral-300">希望単価（最小）</label>
										<div className="mt-1 text-sm text-gray-900 dark:text-neutral-100">
											¥{(selectedJobSeeker.desiredUnitPriceMin ?? 0).toLocaleString()}
										</div>
									</div>
									<div>
										<label className="block text-sm font-medium text-gray-700 dark:text-neutral-300">希望単価（最大）</label>
										<div className="mt-1 text-sm text-gray-900 dark:text-neutral-100">
											¥{(selectedJobSeeker.desiredUnitPriceMax ?? 0).toLocaleString()}
										</div>
									</div>
									<div>
										<label className="block text-sm font-medium text-gray-700 dark:text-neutral-300">希望勤務日数/週</label>
										<div className="mt-1 text-sm text-gray-900 dark:text-neutral-100">{selectedJobSeeker.desiredWorkdaysPerWeek}日</div>
									</div>
									<div>
										<label className="block text-sm font-medium text-gray-700 dark:text-neutral-300">リモート希望</label>
										<div className="mt-1 text-sm text-gray-900 dark:text-neutral-100">{selectedJobSeeker.remotePreference}</div>
									</div>
									{selectedJobSeeker.specializations && selectedJobSeeker.specializations.length > 0 && (
										<div>
											<label className="block text-sm font-medium text-gray-700 dark:text-neutral-300">専門分野</label>
											<div className="mt-1 text-sm text-gray-900 dark:text-neutral-100">
												{selectedJobSeeker.specializations.map((s) => s.nameJa).join(", ")}
											</div>
										</div>
									)}
									{selectedJobSeeker.certifications && selectedJobSeeker.certifications.length > 0 && (
										<div>
											<label className="block text-sm font-medium text-gray-700 dark:text-neutral-300">資格</label>
											<div className="mt-1 text-sm text-gray-900 dark:text-neutral-100">
												{selectedJobSeeker.certifications.map((c) => c.nameJa).join(", ")}
											</div>
										</div>
									)}
									{selectedJobSeeker.languages && selectedJobSeeker.languages.length > 0 && (
										<div>
											<label className="block text-sm font-medium text-gray-700 dark:text-neutral-300">言語</label>
											<div className="mt-1 text-sm text-gray-900 dark:text-neutral-100">
												{selectedJobSeeker.languages.map((l) => l.nameJa).join(", ")}
											</div>
										</div>
									)}
								</div>
							</div>
						) : (
							<div className="flex items-center justify-center p-12">
								<p className="text-gray-600 dark:text-neutral-400">左側のリストから求職者を選択してください</p>
							</div>
						)}
					</div>
				</div>
			</div>
		</div>
	);
}
