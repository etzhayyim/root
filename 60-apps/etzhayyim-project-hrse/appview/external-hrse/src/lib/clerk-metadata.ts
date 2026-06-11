"use server";

import { getClerkClient } from "./clerk";
import type { UserPublicMetadata, OrganizationPublicMetadata } from "./clerk-metadata-client";

/**
 * Clerkメタデータ管理ヘルパー（サーバー専用）
 * ユーザーと組織のロール・タイプ情報をClerkのメタデータに保存
 */

// 型を再エクスポート
export type { UserPublicMetadata, OrganizationPublicMetadata };

/**
 * ユーザーのメタデータを更新（サーバー専用）
 */
export async function updateUserMetadata(
	userId: string,
	metadata: Partial<UserPublicMetadata>,
): Promise<void> {
	const clerkClient = await getClerkClient();

	try {
		const user = await clerkClient.users.getUser(userId);
		const existingMetadata = (user.publicMetadata as Record<string, unknown>) || {};

		await clerkClient.users.updateUserMetadata(userId, {
			publicMetadata: {
				...existingMetadata,
				...metadata,
			},
		});
	} catch (error) {
		console.error("Failed to update user metadata:", error);
		throw new Error("Failed to update user metadata");
	}
}

/**
 * 組織のメタデータを更新（サーバー専用）
 */
export async function updateOrganizationMetadata(
	organizationId: string,
	metadata: Partial<OrganizationPublicMetadata>,
): Promise<void> {
	const clerkClient = await getClerkClient();

	try {
		const org = await clerkClient.organizations.getOrganization({
			organizationId,
		});
		const existingMetadata = (org.publicMetadata as Record<string, unknown>) || {};

		await clerkClient.organizations.updateOrganization(organizationId, {
			publicMetadata: {
				...existingMetadata,
				...metadata,
			},
		});
	} catch (error) {
		console.error("Failed to update organization metadata:", error);
		throw new Error("Failed to update organization metadata");
	}
}
