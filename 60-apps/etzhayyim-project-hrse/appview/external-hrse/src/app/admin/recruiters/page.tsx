"use client";

/**
 * @etzhayyim/etzhayyim-hrse#AdminRecruitersConnect
 * リクルーター管理ページ（Connect-Web版）
 */

import { useUser } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { TouchOptimizedButton } from "@/components/TouchOptimizedButton";
import { useAgencyServiceClient, type Agency, type Recruiter } from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import {
	ListAgenciesRequestSchema,
	ListRecruitersByAgencyRequestSchema,
	GetRecruiterRequestSchema,
	UpdateRecruiterRequestSchema,
} from "@/gen/proto/hrse/v1/agency_pb";
import Link from "next/link";

export default function RecruitersAdminPage() {
	const { user, isLoaded } = useUser();
	const router = useRouter();
	const agencyClient = useAgencyServiceClient();

	const [agencies, setAgencies] = useState<Agency[]>([]);
	const [recruiters, setRecruiters] = useState<Recruiter[]>([]);
	const [selectedAgencyId, setSelectedAgencyId] = useState<string | null>(null);
	const [selectedRecruiter, setSelectedRecruiter] = useState<Recruiter | null>(null);
	const [isEditing, setIsEditing] = useState(false);
	const [formData, setFormData] = useState({ position: "", role: "standard" as "admin" | "standard" | "disabled" });
	const [error, setError] = useState<string | null>(null);
	const [loading, setLoading] = useState(true);
	const [submitting, setSubmitting] = useState(false);

	const fetchAgencies = useCallback(async () => {
		try {
			const res = await agencyClient.listAgencies(create(ListAgenciesRequestSchema, { limit: 100 }));
			setAgencies(res.agencies || []);
		} catch (err) {
			console.error("Failed to fetch agencies:", err);
		}
	}, [agencyClient]);

	const fetchRecruiters = useCallback(async (agencyId: string) => {
		try {
			const res = await agencyClient.listRecruitersByAgency(create(ListRecruitersByAgencyRequestSchema, { agencyId }));
			setRecruiters(res.recruiters || []);
		} catch (err) {
			console.error("Failed to fetch recruiters:", err);
		}
	}, [agencyClient]);

	const fetchRecruiterDetails = useCallback(async (recruiterId: string) => {
		try {
			const res = await agencyClient.getRecruiter(create(GetRecruiterRequestSchema, { id: recruiterId }));
			if (res.recruiter) {
				setSelectedRecruiter(res.recruiter);
			}
		} catch (err) {
			console.error("Failed to fetch recruiter:", err);
		}
	}, [agencyClient]);

	useEffect(() => {
		if (isLoaded && user) {
			fetchAgencies().then(() => setLoading(false));
		}
	}, [isLoaded, user, fetchAgencies]);

	const handleSelectAgency = (agencyId: string) => {
		setSelectedAgencyId(agencyId);
		setSelectedRecruiter(null);
		setIsEditing(false);
		setError(null);
		fetchRecruiters(agencyId);
	};

	const handleSelectRecruiter = (recruiter: Recruiter) => {
		setSelectedRecruiter(recruiter);
		setIsEditing(false);
		setError(null);
	};

	const handleStartEdit = () => {
		if (selectedRecruiter) {
			setFormData({
				position: selectedRecruiter.position || "",
				role: (selectedRecruiter.role as "admin" | "standard" | "disabled") || "standard",
			});
		}
		setIsEditing(true);
		setError(null);
	};

	const handleUpdate = async () => {
		if (!selectedRecruiter) return;

		setSubmitting(true);
		setError(null);
		try {
			await agencyClient.updateRecruiter(
				create(UpdateRecruiterRequestSchema, {
					id: selectedRecruiter.id,
					position: formData.position || undefined,
					role: formData.role,
				})
			);
			setIsEditing(false);
			if (selectedAgencyId) {
				await fetchRecruiters(selectedAgencyId);
				await fetchRecruiterDetails(selectedRecruiter.id);
			}
		} catch (err) {
			console.error("Failed to update recruiter:", err);
			setError(err instanceof Error ? err.message : "更新に失敗しました");
		} finally {
			setSubmitting(false);
		}
	};

	const handleCancel = () => {
		setIsEditing(false);
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
						<h1 className="text-3xl font-bold text-gray-900 dark:text-neutral-100">リクルーター管理</h1>
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

				<div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
					{/* 左側: エージェンシー一覧 */}
					<div className="rounded-lg bg-white shadow dark:bg-neutral-900">
						<div className="border-b border-gray-200 p-4 dark:border-neutral-800">
							<h2 className="text-xl font-semibold text-gray-900 dark:text-neutral-100">エージェンシー一覧</h2>
						</div>
						{agencies.length === 0 ? (
							<div className="p-12 text-center">
								<p className="text-gray-600 dark:text-neutral-400">エージェンシーがありません</p>
							</div>
						) : (
							<div className="divide-y divide-gray-200 dark:divide-neutral-800">
								{agencies.map((agency) => (
									<button
										key={agency.id}
										type="button"
										onClick={() => handleSelectAgency(agency.id)}
										className={`w-full p-4 text-left transition-colors hover:bg-gray-50 dark:hover:bg-neutral-800 ${
											selectedAgencyId === agency.id ? "bg-blue-50 dark:bg-blue-900/20" : ""
										}`}
									>
										<div className="font-semibold text-gray-900 dark:text-neutral-100">{agency.name}</div>
										{agency.contactEmail && (
											<div className="mt-1 text-sm text-gray-600 dark:text-neutral-400">{agency.contactEmail}</div>
										)}
									</button>
								))}
							</div>
						)}
					</div>

					{/* 中央: リクルーター一覧 */}
					<div className="rounded-lg bg-white shadow dark:bg-neutral-900">
						<div className="border-b border-gray-200 p-4 dark:border-neutral-800">
							<h2 className="text-xl font-semibold text-gray-900 dark:text-neutral-100">リクルーター一覧</h2>
						</div>
						{!selectedAgencyId ? (
							<div className="flex items-center justify-center p-12">
								<p className="text-gray-600 dark:text-neutral-400">エージェンシーを選択してください</p>
							</div>
						) : recruiters.length === 0 ? (
							<div className="p-12 text-center">
								<p className="text-gray-600 dark:text-neutral-400">リクルーターがありません</p>
							</div>
						) : (
							<div className="divide-y divide-gray-200 dark:divide-neutral-800">
								{recruiters.map((recruiter) => (
									<button
										key={recruiter.id}
										type="button"
										onClick={() => handleSelectRecruiter(recruiter)}
										className={`w-full p-4 text-left transition-colors hover:bg-gray-50 dark:hover:bg-neutral-800 ${
											selectedRecruiter?.id === recruiter.id ? "bg-blue-50 dark:bg-blue-900/20" : ""
										}`}
									>
										<div className="font-semibold text-gray-900 dark:text-neutral-100">ID: {recruiter.id}</div>
										{recruiter.position && (
											<div className="mt-1 text-sm text-gray-600 dark:text-neutral-400">役職: {recruiter.position}</div>
										)}
										<div className="mt-1 text-sm text-gray-600 dark:text-neutral-400">ロール: {recruiter.role}</div>
									</button>
								))}
							</div>
						)}
					</div>

					{/* 右側: 詳細・編集フォーム */}
					<div className="rounded-lg bg-white shadow dark:bg-neutral-900">
						<div className="border-b border-gray-200 p-4 dark:border-neutral-800">
							<h2 className="text-xl font-semibold text-gray-900 dark:text-neutral-100">
								{selectedRecruiter ? "詳細・編集" : "詳細"}
							</h2>
						</div>
						{selectedRecruiter ? (
							<div className="p-6">
								{isEditing ? (
									<div className="space-y-4">
										<div>
											<label htmlFor="position" className="block text-sm font-medium text-gray-700 dark:text-neutral-300">役職</label>
											<input
												id="position"
												type="text"
												value={formData.position}
												onChange={(e) => setFormData({ ...formData, position: e.target.value })}
												className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100"
											/>
										</div>
										<div>
											<label htmlFor="role" className="block text-sm font-medium text-gray-700 dark:text-neutral-300">
												ロール <span className="text-red-500">*</span>
											</label>
											<select
												id="role"
												value={formData.role}
												onChange={(e) => setFormData({ ...formData, role: e.target.value as "admin" | "standard" | "disabled" })}
												className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100"
											>
												<option value="admin">管理者</option>
												<option value="standard">標準</option>
												<option value="disabled">無効</option>
											</select>
										</div>
										<div className="flex gap-4">
											<TouchOptimizedButton variant="primary" onClick={handleUpdate} disabled={submitting}>
												{submitting ? "更新中..." : "保存"}
											</TouchOptimizedButton>
											<TouchOptimizedButton variant="secondary" onClick={handleCancel}>キャンセル</TouchOptimizedButton>
										</div>
									</div>
								) : (
									<div className="space-y-4">
										<div>
											<label className="block text-sm font-medium text-gray-700 dark:text-neutral-300">ID</label>
											<div className="mt-1 text-sm text-gray-900 dark:text-neutral-100">{selectedRecruiter.id}</div>
										</div>
										<div>
											<label className="block text-sm font-medium text-gray-700 dark:text-neutral-300">ユーザーID</label>
											<div className="mt-1 text-sm text-gray-900 dark:text-neutral-100">{selectedRecruiter.userId}</div>
										</div>
										{selectedRecruiter.position && (
											<div>
												<label className="block text-sm font-medium text-gray-700 dark:text-neutral-300">役職</label>
												<div className="mt-1 text-sm text-gray-900 dark:text-neutral-100">{selectedRecruiter.position}</div>
											</div>
										)}
										<div>
											<label className="block text-sm font-medium text-gray-700 dark:text-neutral-300">ロール</label>
											<div className="mt-1 text-sm text-gray-900 dark:text-neutral-100">{selectedRecruiter.role}</div>
										</div>
										<div className="flex gap-4 pt-4">
											<TouchOptimizedButton variant="primary" onClick={handleStartEdit}>編集</TouchOptimizedButton>
										</div>
									</div>
								)}
							</div>
						) : (
							<div className="flex items-center justify-center p-12">
								<p className="text-gray-600 dark:text-neutral-400">中央のリストからリクルーターを選択してください</p>
							</div>
						)}
					</div>
				</div>
			</div>
		</div>
	);
}
