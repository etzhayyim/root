import type { UserType } from "./clerk-user-type";

/**
 * Clerkメタデータ管理ヘルパー（クライアント用）
 * ユーザーと組織のロール・タイプ情報をClerkのメタデータから取得
 */

// ユーザーのpublicMetadata型定義
export interface UserPublicMetadata {
	userType?: UserType;
	recruiterRole?: "admin" | "standard" | "disabled";
	agencyId?: string;
	recruiterCompanyId?: string;
}

// 組織のpublicMetadata型定義
export interface OrganizationPublicMetadata {
	orgType?: "agency" | "company";
	agencyId?: string;
}

/**
 * ユーザーのpublicMetadataから情報を取得（クライアント用）
 */
export function getUserMetadata(
	publicMetadata: Record<string, unknown> | undefined,
): UserPublicMetadata {
	if (!publicMetadata) return {};
	return {
		userType: publicMetadata.userType as UserType | undefined,
		recruiterRole: publicMetadata.recruiterRole as "admin" | "standard" | "disabled" | undefined,
		agencyId: publicMetadata.agencyId as string | undefined,
		recruiterCompanyId: publicMetadata.recruiterCompanyId as string | undefined,
	};
}

/**
 * 組織のpublicMetadataから情報を取得（クライアント用）
 */
export function getOrganizationMetadata(
	publicMetadata: Record<string, unknown> | undefined,
): OrganizationPublicMetadata {
	if (!publicMetadata) return {};
	return {
		orgType: publicMetadata.orgType as "agency" | "company" | undefined,
		agencyId: publicMetadata.agencyId as string | undefined,
	};
}
