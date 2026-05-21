import { getClerkClient } from "./clerk";

/**
 * Clerk User Type管理ヘルパー
 * ユーザータイプ（jobSeeker, recruiter, agency）をClerkのpublicMetadataに保存・取得
 */

export type UserType = "jobSeeker" | "corporateRecruiter" | "agencyRecruiter" | "agency";

/**
 * ユーザータイプを取得するヘルパー関数
 * @param publicMetadata - ClerkのpublicMetadata
 * @returns ユーザータイプ（未設定の場合は'jobSeeker'を返す）
 */
function getUserTypeFromMetadata(
	publicMetadata: Record<string, unknown> | undefined,
): UserType {
	const userType = publicMetadata?.userType as UserType | undefined;
	return userType || "jobSeeker";
}

/**
 * ユーザータイプを保存（サーバー専用）
 * @param userId - Clerk User ID
 * @param userType - ユーザータイプ
 */
export async function saveUserType(
	userId: string,
	userType: UserType,
): Promise<void> {
	const clerkClient = await getClerkClient();

	try {
		// 既存のメタデータを取得してマージ
		const user = await clerkClient.users.getUser(userId);
		const existingMetadata = (user.publicMetadata as Record<string, unknown>) || {};

		await clerkClient.users.updateUserMetadata(userId, {
			publicMetadata: {
				...existingMetadata,
				userType,
			},
		});
	} catch (error) {
		console.error("Failed to save user type:", error);
		throw new Error("Failed to save user type");
	}
}

/**
 * ユーザータイプを取得（サーバー専用）
 * @param userId - Clerk User ID
 * @returns ユーザータイプ（未設定の場合は'freelancer'を返す）
 */
export async function getUserType(userId: string): Promise<UserType> {
	const clerkClient = await getClerkClient();

	try {
		const user = await clerkClient.users.getUser(userId);
		return getUserTypeFromMetadata(
			user.publicMetadata as Record<string, unknown> | undefined,
		);
	} catch (error) {
		console.error("Failed to get user type:", error);
		// エラー時はデフォルトで求職者を返す
		return "jobSeeker";
	}
}
