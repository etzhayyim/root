"use client";

/**
 * @etzhayyim/etzhayyim-hrse#AdminMasterDataConnect
 * マスターデータ管理ページ（Connect-Web版）
 */

import { useUser } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { TouchOptimizedButton } from "@/components/TouchOptimizedButton";
import { useMasterDataServiceClient } from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import {
	ListCertificationsRequestSchema,
	ListSpecializationsRequestSchema,
	ListLanguagesRequestSchema,
	ListNationalitiesRequestSchema,
	ListWorkPermitsRequestSchema,
} from "@/gen/proto/hrse/v1/job_seeker_pb";

type MasterDataType = "certifications" | "specializations" | "languages" | "nationalities" | "workPermits";

type MasterDataItem = {
	id: string;
	nameEn: string;
	nameJa: string;
};

export default function MasterDataPage() {
	const { user, isLoaded } = useUser();
	const router = useRouter();
	const masterDataClient = useMasterDataServiceClient();

	const [activeTab, setActiveTab] = useState<MasterDataType>("certifications");
	const [loading, setLoading] = useState(true);
	const [data, setData] = useState<MasterDataItem[]>([]);
	const [editingId, setEditingId] = useState<string | null>(null);
	const [isCreating, setIsCreating] = useState(false);
	const [formData, setFormData] = useState({ id: "", nameEn: "", nameJa: "" });
	const [error, setError] = useState<string | null>(null);

	const fetchData = useCallback(async () => {
		setLoading(true);
		setError(null);
		try {
			let items: MasterDataItem[] = [];

			switch (activeTab) {
				case "certifications": {
					const res = await masterDataClient.listCertifications(create(ListCertificationsRequestSchema, {}));
					items = (res.certifications || []).map((c) => ({ id: c.id, nameEn: c.nameEn, nameJa: c.nameJa }));
					break;
				}
				case "specializations": {
					const res = await masterDataClient.listSpecializations(create(ListSpecializationsRequestSchema, {}));
					items = (res.specializations || []).map((s) => ({ id: s.id, nameEn: s.nameEn, nameJa: s.nameJa }));
					break;
				}
				case "languages": {
					const res = await masterDataClient.listLanguages(create(ListLanguagesRequestSchema, {}));
					items = (res.languages || []).map((l) => ({ id: l.id, nameEn: l.nameEn, nameJa: l.nameJa }));
					break;
				}
				case "nationalities": {
					const res = await masterDataClient.listNationalities(create(ListNationalitiesRequestSchema, {}));
					items = (res.nationalities || []).map((n) => ({ id: n.id, nameEn: n.nameEn, nameJa: n.nameJa }));
					break;
				}
				case "workPermits": {
					const res = await masterDataClient.listWorkPermits(create(ListWorkPermitsRequestSchema, {}));
					items = (res.workPermits || []).map((p) => ({ id: p.id, nameEn: p.nameEn, nameJa: p.nameJa }));
					break;
				}
			}

			setData(items);
		} catch (err) {
			console.error("Failed to fetch master data:", err);
			setError(err instanceof Error ? err.message : "データの取得に失敗しました");
		} finally {
			setLoading(false);
		}
	}, [activeTab, masterDataClient]);

	useEffect(() => {
		fetchData();
	}, [fetchData]);

	const handleCreate = async () => {
		alert("マスターデータの作成機能は現在利用できません");
	};

	const handleUpdate = async (id: string) => {
		alert("マスターデータの更新機能は現在利用できません");
	};

	const handleDelete = async (id: string) => {
		if (!confirm("本当に削除しますか？")) return;
		alert("マスターデータの削除機能は現在利用できません");
	};

	const startEdit = (item: MasterDataItem) => {
		setEditingId(item.id);
		setFormData({ id: item.id, nameEn: item.nameEn, nameJa: item.nameJa });
		setIsCreating(false);
	};

	const cancelEdit = () => {
		setEditingId(null);
		setIsCreating(false);
		setFormData({ id: "", nameEn: "", nameJa: "" });
		setError(null);
	};

	const startCreate = () => {
		setIsCreating(true);
		setEditingId(null);
		setFormData({ id: "", nameEn: "", nameJa: "" });
		setError(null);
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

	const tabLabels: Record<MasterDataType, string> = {
		certifications: "資格",
		specializations: "専門分野",
		languages: "言語",
		nationalities: "国籍",
		workPermits: "在留資格",
	};

	return (
		<div className="min-h-screen bg-gray-50 p-4 md:p-8 dark:bg-neutral-950">
			<div className="mx-auto max-w-7xl">
				<div className="mb-8 flex items-center gap-3">
					<h1 className="text-3xl font-bold dark:text-neutral-100">マスターデータ管理</h1>
					<span className="rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-800 dark:bg-green-900 dark:text-green-200">
						Connect-Web
					</span>
				</div>

				{/* タブ */}
				<div className="mb-6 border-b border-gray-200 dark:border-neutral-800">
					<nav className="-mb-px flex space-x-8 overflow-x-auto">
						{(Object.keys(tabLabels) as MasterDataType[]).map((tab) => (
							<button
								key={tab}
								type="button"
								onClick={() => { setActiveTab(tab); cancelEdit(); }}
								className={`min-h-[44px] whitespace-nowrap border-b-2 px-4 py-3 text-base font-medium transition-colors ${
									activeTab === tab
										? "border-blue-500 text-blue-600"
										: "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 dark:text-neutral-400"
								}`}
							>
								{tabLabels[tab]}
							</button>
						))}
					</nav>
				</div>

				{/* エラーメッセージ */}
				{error && (
					<div className="mb-4 rounded-lg bg-red-50 p-4 text-red-800 dark:bg-red-900/20 dark:text-red-400">
						{error}
					</div>
				)}

				{/* 新規作成ボタン */}
				<div className="mb-4 flex justify-end">
					<TouchOptimizedButton variant="primary" onClick={startCreate} disabled={isCreating || editingId !== null}>
						新規作成
					</TouchOptimizedButton>
				</div>

				{/* 新規作成フォーム */}
				{isCreating && (
					<div className="mb-6 rounded-lg bg-white p-6 shadow dark:bg-neutral-900">
						<h2 className="mb-4 text-xl font-semibold dark:text-neutral-100">新規作成</h2>
						<div className="space-y-4">
							<div>
								<label htmlFor="create-id" className="block text-sm font-medium text-gray-700 dark:text-neutral-300">ID</label>
								<input
									id="create-id"
									type="text"
									value={formData.id}
									onChange={(e) => setFormData({ ...formData, id: e.target.value })}
									className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100"
									required
								/>
							</div>
							<div>
								<label htmlFor="create-nameEn" className="block text-sm font-medium text-gray-700 dark:text-neutral-300">英語名</label>
								<input
									id="create-nameEn"
									type="text"
									value={formData.nameEn}
									onChange={(e) => setFormData({ ...formData, nameEn: e.target.value })}
									className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100"
									required
								/>
							</div>
							<div>
								<label htmlFor="create-nameJa" className="block text-sm font-medium text-gray-700 dark:text-neutral-300">日本語名</label>
								<input
									id="create-nameJa"
									type="text"
									value={formData.nameJa}
									onChange={(e) => setFormData({ ...formData, nameJa: e.target.value })}
									className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100"
									required
								/>
							</div>
							<div className="flex gap-4">
								<TouchOptimizedButton variant="primary" onClick={handleCreate} disabled={!formData.id || !formData.nameEn || !formData.nameJa}>
									作成
								</TouchOptimizedButton>
								<TouchOptimizedButton variant="secondary" onClick={cancelEdit}>キャンセル</TouchOptimizedButton>
							</div>
						</div>
					</div>
				)}

				{/* データ一覧 */}
				{loading ? (
					<div className="flex items-center justify-center py-12">
						<div className="text-lg text-gray-600 dark:text-neutral-400">読み込み中...</div>
					</div>
				) : data.length === 0 ? (
					<div className="rounded-lg bg-white p-12 text-center shadow dark:bg-neutral-900">
						<p className="text-gray-600 dark:text-neutral-400">データがありません</p>
					</div>
				) : (
					<div className="overflow-x-auto rounded-lg bg-white shadow dark:bg-neutral-900">
						<table className="min-w-full divide-y divide-gray-200 dark:divide-neutral-800">
							<thead className="bg-gray-50 dark:bg-neutral-800">
								<tr>
									<th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-neutral-400">ID</th>
									<th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-neutral-400">英語名</th>
									<th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-neutral-400">日本語名</th>
									<th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-neutral-400">操作</th>
								</tr>
							</thead>
							<tbody className="divide-y divide-gray-200 bg-white dark:divide-neutral-800 dark:bg-neutral-900">
								{data.map((item) => (
									<tr key={item.id}>
										{editingId === item.id ? (
											<>
												<td className="whitespace-nowrap px-6 py-4 text-sm dark:text-neutral-100">{item.id}</td>
												<td className="whitespace-nowrap px-6 py-4 text-sm">
													<input
														type="text"
														value={formData.nameEn}
														onChange={(e) => setFormData({ ...formData, nameEn: e.target.value })}
														className="w-full rounded-md border border-gray-300 px-2 py-1 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100"
													/>
												</td>
												<td className="whitespace-nowrap px-6 py-4 text-sm">
													<input
														type="text"
														value={formData.nameJa}
														onChange={(e) => setFormData({ ...formData, nameJa: e.target.value })}
														className="w-full rounded-md border border-gray-300 px-2 py-1 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100"
													/>
												</td>
												<td className="whitespace-nowrap px-6 py-4 text-right text-sm">
													<div className="flex justify-end gap-2">
														<TouchOptimizedButton variant="primary" size="sm" onClick={() => handleUpdate(item.id)} disabled={!formData.nameEn || !formData.nameJa}>
															保存
														</TouchOptimizedButton>
														<TouchOptimizedButton variant="secondary" size="sm" onClick={cancelEdit}>キャンセル</TouchOptimizedButton>
													</div>
												</td>
											</>
										) : (
											<>
												<td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-gray-900 dark:text-neutral-100">{item.id}</td>
												<td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500 dark:text-neutral-400">{item.nameEn}</td>
												<td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500 dark:text-neutral-400">{item.nameJa}</td>
												<td className="whitespace-nowrap px-6 py-4 text-right text-sm">
													<div className="flex justify-end gap-2">
														<TouchOptimizedButton variant="secondary" size="sm" onClick={() => startEdit(item)} disabled={isCreating || editingId !== null}>編集</TouchOptimizedButton>
														<TouchOptimizedButton variant="danger" size="sm" onClick={() => handleDelete(item.id)} disabled={isCreating || editingId !== null}>削除</TouchOptimizedButton>
													</div>
												</td>
											</>
										)}
									</tr>
								))}
							</tbody>
						</table>
					</div>
				)}
			</div>
		</div>
	);
}
