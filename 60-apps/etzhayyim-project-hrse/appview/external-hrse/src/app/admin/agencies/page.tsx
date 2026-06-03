"use client";

/**
 * @etzhayyim/etzhayyim-hrse#AdminAgenciesConnect
 * エージェンシー管理ページ（Connect-Web版）
 */

import { useUser } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { TouchOptimizedButton } from "@/components/TouchOptimizedButton";
import { useAgencyServiceClient, type Agency } from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import {
	ListAgenciesRequestSchema,
	CreateAgencyRequestSchema,
	UpdateAgencyRequestSchema,
} from "@/gen/proto/hrse/v1/agency_pb";
import Link from "next/link";

export default function AgenciesAdminPage() {
	const { user, isLoaded } = useUser();
	const router = useRouter();
	const agencyClient = useAgencyServiceClient();

	const [agencies, setAgencies] = useState<Agency[]>([]);
	const [loading, setLoading] = useState(true);
	const [selectedAgency, setSelectedAgency] = useState<Agency | null>(null);
	const [isEditing, setIsEditing] = useState(false);
	const [isCreating, setIsCreating] = useState(false);
	const [formData, setFormData] = useState({
		name: "",
		licenseNumber: "",
		contactEmail: "",
		contactPhone: "",
		address: "",
	});
	const [error, setError] = useState<string | null>(null);
	const [submitting, setSubmitting] = useState(false);

	const fetchAgencies = useCallback(async () => {
		setLoading(true);
		try {
			const res = await agencyClient.listAgencies(create(ListAgenciesRequestSchema, { limit: 100 }));
			setAgencies(res.agencies || []);
		} catch (err) {
			console.error("Failed to fetch agencies:", err);
			setError(err instanceof Error ? err.message : "エージェンシーの取得に失敗しました");
		} finally {
			setLoading(false);
		}
	}, [agencyClient]);

	useEffect(() => {
		if (isLoaded && user) {
			fetchAgencies();
		}
	}, [isLoaded, user, fetchAgencies]);

	useEffect(() => {
		if (selectedAgency && !isCreating) {
			setFormData({
				name: selectedAgency.name || "",
				licenseNumber: selectedAgency.licenseNumber || "",
				contactEmail: selectedAgency.contactEmail || "",
				contactPhone: selectedAgency.contactPhone || "",
				address: selectedAgency.address || "",
			});
		}
	}, [selectedAgency, isCreating]);

	const handleCreate = async () => {
		setSubmitting(true);
		setError(null);
		try {
			await agencyClient.createAgency(
				create(CreateAgencyRequestSchema, {
					name: formData.name,
					licenseNumber: formData.licenseNumber || undefined,
					contactEmail: formData.contactEmail || undefined,
					contactPhone: formData.contactPhone || undefined,
					address: formData.address || undefined,
				})
			);
			setIsCreating(false);
			setFormData({ name: "", licenseNumber: "", contactEmail: "", contactPhone: "", address: "" });
			await fetchAgencies();
		} catch (err) {
			console.error("Failed to create agency:", err);
			setError(err instanceof Error ? err.message : "作成に失敗しました");
		} finally {
			setSubmitting(false);
		}
	};

	const handleUpdate = async () => {
		if (!selectedAgency) return;

		setSubmitting(true);
		setError(null);
		try {
			const res = await agencyClient.updateAgency(
				create(UpdateAgencyRequestSchema, {
					id: selectedAgency.id,
					name: formData.name,
					licenseNumber: formData.licenseNumber || undefined,
					contactEmail: formData.contactEmail || undefined,
					contactPhone: formData.contactPhone || undefined,
					address: formData.address || undefined,
				})
			);
			setIsEditing(false);
			if (res.agency) {
				setSelectedAgency(res.agency);
			}
			await fetchAgencies();
		} catch (err) {
			console.error("Failed to update agency:", err);
			setError(err instanceof Error ? err.message : "更新に失敗しました");
		} finally {
			setSubmitting(false);
		}
	};

	const handleSelectAgency = (agency: Agency) => {
		setSelectedAgency(agency);
		setIsEditing(false);
		setIsCreating(false);
		setError(null);
	};

	const handleStartEdit = () => {
		setIsEditing(true);
		setIsCreating(false);
		setError(null);
	};

	const handleStartCreate = () => {
		setIsCreating(true);
		setIsEditing(false);
		setSelectedAgency(null);
		setFormData({ name: "", licenseNumber: "", contactEmail: "", contactPhone: "", address: "" });
		setError(null);
	};

	const handleCancel = () => {
		setIsEditing(false);
		setIsCreating(false);
		setError(null);
		if (selectedAgency) {
			setFormData({
				name: selectedAgency.name || "",
				licenseNumber: selectedAgency.licenseNumber || "",
				contactEmail: selectedAgency.contactEmail || "",
				contactPhone: selectedAgency.contactPhone || "",
				address: selectedAgency.address || "",
			});
		}
	};

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

	return (
		<div className="min-h-screen bg-gray-50 p-4 md:p-8 dark:bg-neutral-950">
			<div className="mx-auto max-w-7xl">
				<div className="mb-6 flex items-center justify-between">
					<div className="flex items-center gap-3">
						<h1 className="text-3xl font-bold text-gray-900 dark:text-neutral-100">エージェンシー管理</h1>
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
					{/* 左側: エージェンシー一覧 */}
					<div className="rounded-lg bg-white shadow dark:bg-neutral-900">
						<div className="border-b border-gray-200 p-4 dark:border-neutral-800">
							<div className="flex items-center justify-between">
								<h2 className="text-xl font-semibold text-gray-900 dark:text-neutral-100">エージェンシー一覧</h2>
								<TouchOptimizedButton variant="primary" size="sm" onClick={handleStartCreate} disabled={isEditing || isCreating}>
									新規作成
								</TouchOptimizedButton>
							</div>
						</div>

						{loading ? (
							<div className="flex items-center justify-center py-12">
								<div className="text-lg text-gray-600 dark:text-neutral-400">読み込み中...</div>
							</div>
						) : agencies.length === 0 ? (
							<div className="p-12 text-center">
								<p className="text-gray-600 dark:text-neutral-400">エージェンシーがありません</p>
							</div>
						) : (
							<div className="divide-y divide-gray-200 dark:divide-neutral-800">
								{agencies.map((agency) => (
									<button
										key={agency.id}
										type="button"
										onClick={() => handleSelectAgency(agency)}
										className={`w-full p-4 text-left transition-colors hover:bg-gray-50 dark:hover:bg-neutral-800 ${
											selectedAgency?.id === agency.id ? "bg-blue-50 dark:bg-blue-900/20" : ""
										}`}
									>
										<div className="font-semibold text-gray-900 dark:text-neutral-100">{agency.name}</div>
										{agency.contactEmail && (
											<div className="mt-1 text-sm text-gray-600 dark:text-neutral-400">{agency.contactEmail}</div>
										)}
										<div className="mt-1 text-xs text-gray-500 dark:text-neutral-500">ID: {agency.id}</div>
									</button>
								))}
							</div>
						)}
					</div>

					{/* 右側: 詳細・編集フォーム */}
					<div className="rounded-lg bg-white shadow dark:bg-neutral-900">
						<div className="border-b border-gray-200 p-4 dark:border-neutral-800">
							<h2 className="text-xl font-semibold text-gray-900 dark:text-neutral-100">
								{isCreating ? "新規作成" : selectedAgency ? "詳細・編集" : "詳細"}
							</h2>
						</div>

						{isCreating || (selectedAgency && isEditing) ? (
							<div className="p-6">
								<div className="space-y-4">
									<div>
										<label htmlFor="name" className="block text-sm font-medium text-gray-700 dark:text-neutral-300">
											エージェンシー名 <span className="text-red-500">*</span>
										</label>
										<input
											id="name"
											type="text"
											value={formData.name}
											onChange={(e) => setFormData({ ...formData, name: e.target.value })}
											className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100"
											required
										/>
									</div>
									<div>
										<label htmlFor="licenseNumber" className="block text-sm font-medium text-gray-700 dark:text-neutral-300">許可番号</label>
										<input
											id="licenseNumber"
											type="text"
											value={formData.licenseNumber}
											onChange={(e) => setFormData({ ...formData, licenseNumber: e.target.value })}
											className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100"
										/>
									</div>
									<div>
										<label htmlFor="contactEmail" className="block text-sm font-medium text-gray-700 dark:text-neutral-300">連絡先メールアドレス</label>
										<input
											id="contactEmail"
											type="email"
											value={formData.contactEmail}
											onChange={(e) => setFormData({ ...formData, contactEmail: e.target.value })}
											className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100"
										/>
									</div>
									<div>
										<label htmlFor="contactPhone" className="block text-sm font-medium text-gray-700 dark:text-neutral-300">連絡先電話番号</label>
										<input
											id="contactPhone"
											type="tel"
											value={formData.contactPhone}
											onChange={(e) => setFormData({ ...formData, contactPhone: e.target.value })}
											className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100"
										/>
									</div>
									<div>
										<label htmlFor="address" className="block text-sm font-medium text-gray-700 dark:text-neutral-300">住所</label>
										<textarea
											id="address"
											value={formData.address}
											onChange={(e) => setFormData({ ...formData, address: e.target.value })}
											rows={3}
											className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100"
										/>
									</div>
									<div className="flex gap-4">
										<TouchOptimizedButton
											variant="primary"
											onClick={isCreating ? handleCreate : handleUpdate}
											disabled={!formData.name || submitting}
										>
											{submitting ? (isCreating ? "作成中..." : "更新中...") : isCreating ? "作成" : "保存"}
										</TouchOptimizedButton>
										<TouchOptimizedButton variant="secondary" onClick={handleCancel}>キャンセル</TouchOptimizedButton>
									</div>
								</div>
							</div>
						) : selectedAgency ? (
							<div className="p-6">
								<div className="space-y-4">
									<div>
										<label className="block text-sm font-medium text-gray-700 dark:text-neutral-300">ID</label>
										<div className="mt-1 text-sm text-gray-900 dark:text-neutral-100">{selectedAgency.id}</div>
									</div>
									<div>
										<label className="block text-sm font-medium text-gray-700 dark:text-neutral-300">エージェンシー名</label>
										<div className="mt-1 text-sm text-gray-900 dark:text-neutral-100">{selectedAgency.name}</div>
									</div>
									{selectedAgency.licenseNumber && (
										<div>
											<label className="block text-sm font-medium text-gray-700 dark:text-neutral-300">許可番号</label>
											<div className="mt-1 text-sm text-gray-900 dark:text-neutral-100">{selectedAgency.licenseNumber}</div>
										</div>
									)}
									{selectedAgency.contactEmail && (
										<div>
											<label className="block text-sm font-medium text-gray-700 dark:text-neutral-300">連絡先メールアドレス</label>
											<div className="mt-1 text-sm text-gray-900 dark:text-neutral-100">{selectedAgency.contactEmail}</div>
										</div>
									)}
									{selectedAgency.contactPhone && (
										<div>
											<label className="block text-sm font-medium text-gray-700 dark:text-neutral-300">連絡先電話番号</label>
											<div className="mt-1 text-sm text-gray-900 dark:text-neutral-100">{selectedAgency.contactPhone}</div>
										</div>
									)}
									{selectedAgency.address && (
										<div>
											<label className="block text-sm font-medium text-gray-700 dark:text-neutral-300">住所</label>
											<div className="mt-1 text-sm text-gray-900 dark:text-neutral-100">{selectedAgency.address}</div>
										</div>
									)}
									<div className="flex gap-4 pt-4">
										<TouchOptimizedButton variant="primary" onClick={handleStartEdit}>編集</TouchOptimizedButton>
									</div>
								</div>
							</div>
						) : (
							<div className="flex items-center justify-center p-12">
								<p className="text-gray-600 dark:text-neutral-400">左側のリストからエージェンシーを選択してください</p>
							</div>
						)}
					</div>
				</div>
			</div>
		</div>
	);
}
