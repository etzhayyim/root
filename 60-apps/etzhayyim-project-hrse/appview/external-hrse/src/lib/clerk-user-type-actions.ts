"use server";

import { saveUserType, type UserType } from "./clerk-user-type";
import { auth } from "@clerk/nextjs/server";

/**
 * サーバーアクション: ユーザータイプを保存
 * クライアントコンポーネントから呼び出し可能
 */
export async function saveUserTypeAction(
	userId: string,
	userType: UserType,
): Promise<{ success: boolean; error?: string }> {
	try {
		await saveUserType(userId, userType);
		return { success: true };
	} catch (error) {
		console.error("Failed to save user type:", error);
		return {
			success: false,
			error: error instanceof Error ? error.message : "Failed to save user type",
		};
	}
}

/**
 * サーバーアクション: 現在のユーザーのユーザータイプを更新
 * 自分自身のuserTypeを更新する場合に使用
 */
export async function updateMyUserTypeAction(
	userType: UserType,
): Promise<{ success: boolean; error?: string }> {
	try {
		const { userId } = await auth();

		if (!userId) {
			return {
				success: false,
				error: "Not authenticated",
			};
		}

		await saveUserType(userId, userType);
		return { success: true };
	} catch (error) {
		console.error("Failed to update user type:", error);
		return {
			success: false,
			error: error instanceof Error ? error.message : "Failed to update user type",
		};
	}
}
