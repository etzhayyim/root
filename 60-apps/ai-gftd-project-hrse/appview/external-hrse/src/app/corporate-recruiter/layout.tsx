import { redirect } from "next/navigation";
import { getUserAuthInfo, determineEffectiveUserType } from "@/lib/auth-helpers";

/**
 * 企業担当リクルーター向けレイアウト
 * 企業担当リクルーターとシステム管理者のみアクセス可能
 */
export default async function CorporateRecruiterLayout({
	children,
}: {
	children: React.ReactNode;
}) {
	const authInfo = await getUserAuthInfo();

	// 未認証の場合はサインインページへ
	if (!authInfo.userId) {
		redirect("/auth/signin");
	}

	const effectiveUserType = determineEffectiveUserType(authInfo);

	// システム管理者は全ページアクセス可能
	if (effectiveUserType === "admin") {
		return <>{children}</>;
	}

	// 企業担当リクルーターはアクセス可能
	if (effectiveUserType === "corporate_recruiter") {
		return <>{children}</>;
	}

	// その他のユーザータイプは適切なページにリダイレクト
	if (effectiveUserType === "agency") {
		if (authInfo.clerkOrgId) {
			redirect(`/${authInfo.clerkOrgId}/agency`);
		}
		redirect("/agency");
	}
	if (effectiveUserType === "agency_recruiter") {
		if (authInfo.clerkOrgId) {
			redirect(`/${authInfo.clerkOrgId}/agency-recruiter/profile`);
		}
		redirect("/agency-recruiter/profile");
	}
	if (effectiveUserType === "job_seeker") {
		redirect("/job-seeker/profile");
	}

	// デフォルトはホームへ
	redirect("/");
}
