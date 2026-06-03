"use client";

/**
 * @etzhayyim/etzhayyim-hrse#AdminOrganizationsConnect
 * 組織管理ページ（Connect-Web版）
 */

import { useUser } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { getOrganizationMetadata, type OrganizationPublicMetadata } from "@/lib/clerk-metadata-client";
import { useAdminServiceClient, type ClerkOrganization } from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import {
	ListClerkOrganizationsRequestSchema,
	UpdateClerkOrganizationMetadataRequestSchema,
} from "@/gen/proto/hrse/v1/admin_pb";

export default function OrganizationsAdminPage() {
	const { user: currentUser, isLoaded } = useUser();
	const router = useRouter();
	const adminClient = useAdminServiceClient();

	const [organizations, setOrganizations] = useState<ClerkOrganization[]>([]);
	const [loading, setLoading] = useState(true);
	const [editingOrg, setEditingOrg] = useState<string | null>(null);
	const [editForm, setEditForm] = useState<Partial<OrganizationPublicMetadata>>({});

	const fetchOrganizations = useCallback(async () => {
		setLoading(true);
		try {
			const res = await adminClient.listClerkOrganizations(
				create(ListClerkOrganizationsRequestSchema, { limit: 100, offset: 0 })
			);
			setOrganizations(res.organizations || []);
		} catch (error) {
			console.error("Failed to fetch organizations:", error);
		} finally {
			setLoading(false);
		}
	}, [adminClient]);

	useEffect(() => {
		if (isLoaded && currentUser) {
			fetchOrganizations();
		}
	}, [isLoaded, currentUser, fetchOrganizations]);

	const handleEdit = (org: ClerkOrganization) => {
		const metadata = (org.publicMetadata as Record<string, unknown>) || {};
		setEditingOrg(org.id);
		setEditForm({
			orgType: metadata.orgType as "agency" | "company" | undefined,
			agencyId: metadata.agencyId as string | undefined,
		});
	};

	const handleSave = async (orgId: string) => {
		try {
			await adminClient.updateClerkOrganizationMetadata(
				create(UpdateClerkOrganizationMetadataRequestSchema, {
					organizationId: orgId,
					metadata: {
						orgType: editForm.orgType || undefined,
						agencyId: editForm.agencyId || undefined,
					},
				})
			);

			await fetchOrganizations();
			setEditingOrg(null);
			alert("組織メタデータを更新しました");
		} catch (error) {
			console.error("Failed to update organization:", error);
			alert(`更新に失敗しました: ${error instanceof Error ? error.message : "Unknown error"}`);
		}
	};

	if (!isLoaded) {
		return (
			<div className="flex min-h-screen items-center justify-center">
				<div className="text-lg">読み込み中...</div>
			</div>
		);
	}

	if (!currentUser) {
		router.push("/auth/signin");
		return null;
	}

	if (loading) {
		return (
			<div className="flex min-h-screen items-center justify-center">
				<div className="text-lg">読み込み中...</div>
			</div>
		);
	}

	return (
		<div className="min-h-screen bg-gray-50 p-4 md:p-8 dark:bg-neutral-950">
			<div className="mx-auto max-w-7xl">
				<div className="mb-8 flex items-center gap-3">
					<h1 className="text-3xl font-bold text-gray-900 dark:text-neutral-100">組織管理</h1>
					<span className="rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-800 dark:bg-green-900 dark:text-green-200">
						Connect-Web
					</span>
				</div>

				<div className="overflow-x-auto rounded-lg bg-white shadow dark:bg-neutral-900">
					<table className="min-w-full divide-y divide-gray-200 dark:divide-neutral-800">
						<thead className="bg-gray-50 dark:bg-neutral-800">
							<tr>
								<th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-neutral-400">ID</th>
								<th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-neutral-400">名前</th>
								<th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-neutral-400">組織タイプ</th>
								<th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-neutral-400">エージェンシーID</th>
								<th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-neutral-400">操作</th>
							</tr>
						</thead>
						<tbody className="divide-y divide-gray-200 bg-white dark:divide-neutral-800 dark:bg-neutral-900">
						{organizations.map((org) => {
							const metadata = (org.publicMetadata as Record<string, unknown>) || {};
							const isEditing = editingOrg === org.id;

								return (
									<tr key={org.id} className="hover:bg-gray-50 dark:hover:bg-neutral-800">
										<td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900 dark:text-neutral-100">{org.id}</td>
										<td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900 dark:text-neutral-100">{org.name || "-"}</td>
										<td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900 dark:text-neutral-100">
											{isEditing ? (
												<select
													value={editForm.orgType || ""}
													onChange={(e) => setEditForm({ ...editForm, orgType: e.target.value ? (e.target.value as "agency" | "company") : undefined })}
													className="rounded border border-gray-300 px-2 py-1 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100"
												>
													<option value="">未設定</option>
													<option value="agency">agency</option>
													<option value="company">company</option>
												</select>
											) : (
												(metadata.orgType as string | undefined) || "-"
											)}
										</td>
										<td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900 dark:text-neutral-100">
											{isEditing ? (
												<input
													type="text"
													value={editForm.agencyId || ""}
													onChange={(e) => setEditForm({ ...editForm, agencyId: e.target.value || undefined })}
													className="rounded border border-gray-300 px-2 py-1 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100"
												/>
											) : (
												(metadata.agencyId as string | undefined) || "-"
											)}
										</td>
										<td className="whitespace-nowrap px-6 py-4 text-sm">
											{isEditing ? (
												<div className="flex gap-2">
													<button onClick={() => handleSave(org.id)} className="rounded bg-blue-600 px-3 py-1 text-white hover:bg-blue-700">
														保存
													</button>
													<button onClick={() => setEditingOrg(null)} className="rounded bg-gray-300 px-3 py-1 hover:bg-gray-400 dark:bg-neutral-700 dark:hover:bg-neutral-600">
														キャンセル
													</button>
												</div>
											) : (
												<button onClick={() => handleEdit(org)} className="rounded bg-blue-600 px-3 py-1 text-white hover:bg-blue-700">
													編集
												</button>
											)}
										</td>
									</tr>
								);
							})}
						</tbody>
					</table>
				</div>
			</div>
		</div>
	);
}
