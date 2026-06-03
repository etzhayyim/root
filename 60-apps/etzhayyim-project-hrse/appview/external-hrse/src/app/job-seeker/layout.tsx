import { redirect } from "next/navigation";
import { getUserAuthInfo, determineEffectiveUserType } from "@/lib/auth-helpers";

/**
 * 求職者ページ用レイアウト
 * 求職者とシステム管理者のみアクセス可能
 */
export default async function JobSeekerLayout({
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

	// 求職者はアクセス可能
	if (effectiveUserType === "job_seeker") {
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
	if (effectiveUserType === "corporate_recruiter") {
		redirect("/corporate-recruiter");
	}

	// デフォルトはホームへ
	redirect("/");
}

