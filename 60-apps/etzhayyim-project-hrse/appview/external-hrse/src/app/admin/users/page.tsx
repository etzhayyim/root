"use client";

/**
 * @etzhayyim/etzhayyim-hrse#AdminUsersConnect
 * ユーザー管理ページ（Connect-Web版）
 */

import { useUser } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { getUserMetadata, type UserPublicMetadata } from "@/lib/clerk-metadata-client";
import type { UserType } from "@/lib/clerk-user-type";
import { useAdminServiceClient, type ClerkUser } from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import {
	ListClerkUsersRequestSchema,
	UpdateClerkUserMetadataRequestSchema,
} from "@/gen/proto/hrse/v1/admin_pb";

export default function UsersAdminPage() {
	const { user: currentUser, isLoaded } = useUser();
	const router = useRouter();
	const adminClient = useAdminServiceClient();

	const [users, setUsers] = useState<ClerkUser[]>([]);
	const [loading, setLoading] = useState(true);
	const [editingUser, setEditingUser] = useState<string | null>(null);
	const [editForm, setEditForm] = useState<Partial<UserPublicMetadata>>({});

	const fetchUsers = useCallback(async () => {
		setLoading(true);
		try {
			const res = await adminClient.listClerkUsers(
				create(ListClerkUsersRequestSchema, { limit: 100, offset: 0 })
			);
			setUsers(res.users || []);
		} catch (error) {
			console.error("Failed to fetch users:", error);
		} finally {
			setLoading(false);
		}
	}, [adminClient]);

	useEffect(() => {
		if (isLoaded && currentUser) {
			fetchUsers();
		}
	}, [isLoaded, currentUser, fetchUsers]);

	const handleEdit = (user: ClerkUser) => {
		const metadata = (user.publicMetadata as Record<string, unknown>) || {};
		setEditingUser(user.id);
		setEditForm({
			userType: metadata.userType as UserType | undefined,
			recruiterRole: metadata.recruiterRole as "admin" | "standard" | "disabled" | undefined,
			agencyId: metadata.agencyId as string | undefined,
			recruiterCompanyId: metadata.recruiterCompanyId as string | undefined,
		});
	};

	const handleSave = async (userId: string) => {
		try {
			await adminClient.updateClerkUserMetadata(
				create(UpdateClerkUserMetadataRequestSchema, {
					userId,
					metadata: {
						userType: editForm.userType || undefined,
						recruiterRole: editForm.recruiterRole || undefined,
						agencyId: editForm.agencyId || undefined,
						recruiterCompanyId: editForm.recruiterCompanyId || undefined,
					},
				})
			);

			await fetchUsers();
			setEditingUser(null);
			alert("ユーザーメタデータを更新しました");
		} catch (error) {
			console.error("Failed to update user:", error);
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
					<h1 className="text-3xl font-bold text-gray-900 dark:text-neutral-100">ユーザー管理</h1>
					<span className="rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-800 dark:bg-green-900 dark:text-green-200">
						Connect-Web
					</span>
				</div>

				<div className="overflow-x-auto rounded-lg bg-white shadow dark:bg-neutral-900">
					<table className="min-w-full divide-y divide-gray-200 dark:divide-neutral-800">
						<thead className="bg-gray-50 dark:bg-neutral-800">
							<tr>
								<th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-neutral-400">ID</th>
								<th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-neutral-400">メール</th>
								<th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-neutral-400">ユーザータイプ</th>
								<th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-neutral-400">リクルーターロール</th>
								<th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-neutral-400">エージェンシーID</th>
								<th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-neutral-400">操作</th>
							</tr>
						</thead>
						<tbody className="divide-y divide-gray-200 bg-white dark:divide-neutral-800 dark:bg-neutral-900">
						{users.map((user) => {
							const metadata = (user.publicMetadata as Record<string, unknown>) || {};
							const isEditing = editingUser === user.id;

								return (
									<tr key={user.id} className="hover:bg-gray-50 dark:hover:bg-neutral-800">
										<td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900 dark:text-neutral-100">{user.id}</td>
										<td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900 dark:text-neutral-100">
											{user.emailAddresses?.[0] || "-"}
										</td>
										<td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900 dark:text-neutral-100">
											{isEditing ? (
												<select
													value={editForm.userType || ""}
													onChange={(e) => setEditForm({ ...editForm, userType: e.target.value ? (e.target.value as UserType) : undefined })}
													className="rounded border border-gray-300 px-2 py-1 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100"
												>
													<option value="">未設定</option>
													<option value="freelancer">freelancer</option>
													<option value="hire_manager">hire_manager</option>
													<option value="agency">agency</option>
												</select>
											) : (
												(metadata.userType as string | undefined) || "-"
											)}
										</td>
										<td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900 dark:text-neutral-100">
											{isEditing ? (
												<select
													value={editForm.recruiterRole || ""}
													onChange={(e) => setEditForm({ ...editForm, recruiterRole: e.target.value ? (e.target.value as "admin" | "standard" | "disabled") : undefined })}
													className="rounded border border-gray-300 px-2 py-1 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100"
												>
													<option value="">未設定</option>
													<option value="admin">admin</option>
													<option value="standard">standard</option>
													<option value="disabled">disabled</option>
												</select>
											) : (
												(metadata.recruiterRole as string | undefined) || "-"
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
													<button onClick={() => handleSave(user.id)} className="rounded bg-blue-600 px-3 py-1 text-white hover:bg-blue-700">
														保存
													</button>
													<button onClick={() => setEditingUser(null)} className="rounded bg-gray-300 px-3 py-1 hover:bg-gray-400 dark:bg-neutral-700 dark:hover:bg-neutral-600">
														キャンセル
													</button>
												</div>
											) : (
												<button onClick={() => handleEdit(user)} className="rounded bg-blue-600 px-3 py-1 text-white hover:bg-blue-700">
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
