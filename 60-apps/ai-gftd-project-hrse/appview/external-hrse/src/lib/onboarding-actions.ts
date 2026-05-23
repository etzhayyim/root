"use server";

import { getClerkClient } from "./clerk";
import type { UserType } from "./clerk-user-type";

/**
 * オンボーディング完了アクション
 * ユーザーのオンボーディング完了状態とuserTypeをClerkのpublicMetadataに保存
 */
export async function completeOnboardingAction(
	userId: string,
	userType: UserType,
): Promise<{ success: boolean; error?: string }> {
	try {
		const clerkClient = await getClerkClient();

		// 既存のメタデータを取得してマージ
		const user = await clerkClient.users.getUser(userId);
		const existingMetadata = (user.publicMetadata as Record<string, unknown>) || {};

		await clerkClient.users.updateUserMetadata(userId, {
			publicMetadata: {
				...existingMetadata,
				userType,
				onboardingCompleted: true,
				onboardingCompletedAt: new Date().toISOString(),
			},
		});

		return { success: true };
	} catch (error) {
		console.error("Failed to complete onboarding:", error);
		return {
			success: false,
			error: error instanceof Error ? error.message : "Failed to complete onboarding",
		};
	}
}

/**
 * オンボーディング完了状態を確認
 */
export async function checkOnboardingStatusAction(
	userId: string,
): Promise<{ completed: boolean; userType?: UserType }> {
	try {
		const clerkClient = await getClerkClient();
		const user = await clerkClient.users.getUser(userId);
		const publicMetadata = user.publicMetadata as Record<string, unknown> | undefined;

		return {
			completed: !!publicMetadata?.onboardingCompleted,
			userType: publicMetadata?.userType as UserType | undefined,
		};
	} catch (error) {
		console.error("Failed to check onboarding status:", error);
		return { completed: false };
	}
}

