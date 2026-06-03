import { auth, clerkClient } from "@clerk/nextjs/server";
import type { UserType } from "./clerk-user-type";

export interface UserAuthInfo {
	userId: string | null;
	userType: UserType | undefined;
	isSystemAdmin: boolean;
	agencyId: string | undefined;
	recruiterRole: "admin" | "standard" | "disabled" | undefined;
	orgType: "agency" | "company" | undefined;
	// 招待経由でエージェンシーに所属した場合の情報
	clerkOrgId: string | undefined;
	isOrgMember: boolean;
	// オンボーディング完了状態
	onboardingCompleted: boolean;
}

/**
 * サーバーサイドでユーザーの認証情報とタイプを取得
 */
export async function getUserAuthInfo(): Promise<UserAuthInfo> {
	const authResult = await auth();
	const { userId, orgId } = authResult;

	if (!userId) {
		return {
			userId: null,
			userType: undefined,
			isSystemAdmin: false,
			agencyId: undefined,
			recruiterRole: undefined,
			orgType: undefined,
			clerkOrgId: undefined,
			isOrgMember: false,
			onboardingCompleted: false,
		};
	}

	try {
		const client = await clerkClient();
		const user = await client.users.getUser(userId);

		// システム管理者チェック（@etzhayyim.com ドメイン）
		const isSystemAdmin = user.emailAddresses?.some((email) =>
			email.emailAddress?.includes("@etzhayyim.com")
		) ?? false;

		const publicMetadata = user.publicMetadata as Record<string, unknown> | undefined;
		const userType = publicMetadata?.userType as UserType | undefined;
		const agencyId = publicMetadata?.agencyId as string | undefined;
		const recruiterRole = publicMetadata?.recruiterRole as "admin" | "standard" | "disabled" | undefined;
		const onboardingCompleted = !!publicMetadata?.onboardingCompleted;

		// 組織メンバーシップをチェック（招待経由のユーザー検出用）
		// アクティブ組織（orgId）がなくても、ユーザーの組織メンバーシップを確認
		// 新規招待ユーザーはアクティブ組織が設定されていない可能性があるため
		const userOrgMemberships = await client.users.getOrganizationMembershipList({ userId });
		const hasOrgMembership = userOrgMemberships.data && userOrgMemberships.data.length > 0;
		const isOrgMember = !!orgId || hasOrgMembership;

		// アクティブ組織がない場合、最初のメンバーシップの組織IDを使用
		let effectiveClerkOrgId = orgId ?? undefined;
		if (!effectiveClerkOrgId && hasOrgMembership) {
			effectiveClerkOrgId = userOrgMemberships.data[0].organization.id;
		}

		return {
			userId,
			userType,
			isSystemAdmin,
			agencyId,
			recruiterRole,
			orgType: undefined, // 組織情報は別途取得が必要
			clerkOrgId: effectiveClerkOrgId,
			isOrgMember,
			onboardingCompleted,
		};
	} catch (error) {
		console.error("Failed to get user auth info:", error);
		return {
			userId,
			userType: undefined,
			isSystemAdmin: false,
			agencyId: undefined,
			recruiterRole: undefined,
			orgType: undefined,
			clerkOrgId: undefined,
			isOrgMember: false,
			onboardingCompleted: false,
		};
	}
}

/**
 * ユーザータイプを判定（未設定の場合は他の情報から推測）
 *
 * 優先順位:
 * 1. システム管理者（@etzhayyim.com ドメイン）
 * 2. 明示的に設定されたuserType（agency, agencyRecruiter, corporateRecruiter, jobSeeker）はそのまま保持
 * 3. userType未設定で組織メンバーシップがある場合は agencyRecruiter（招待経由の新規ユーザー）
 * 4. recruiterRole から推測
 * 5. agencyId から推測
 * 6. デフォルトは jobSeeker
 */
export function determineEffectiveUserType(info: UserAuthInfo): "jobSeeker" | "corporateRecruiter" | "agencyRecruiter" | "agency" | "admin" {
	// システム管理者の場合
	if (info.isSystemAdmin) {
		return "admin";
	}

	// 明示的にuserTypeが設定されている場合はそのまま保持
	// corporateRecruiter は組織メンバーシップがあっても corporateRecruiter のまま
	if (info.userType === "agency" || info.userType === "agencyRecruiter" || info.userType === "corporateRecruiter" || info.userType === "jobSeeker") {
		return info.userType;
	}

	// 組織メンバーの場合（エージェンシーに招待されたユーザー）
	// userType が未設定の場合は agencyRecruiter として扱う（招待経由の新規ユーザー）
	if (info.isOrgMember && info.clerkOrgId && !info.userType) {
		return "agencyRecruiter";
	}

	// recruiterRoleがある場合はエージェンシー所属リクルーター
	if (info.recruiterRole && info.recruiterRole !== "disabled") {
		return "agencyRecruiter";
	}

	// agencyIdがある場合はエージェンシー
	if (info.agencyId) {
		return "agency";
	}

	// デフォルトは求職者
	return "jobSeeker";
}
