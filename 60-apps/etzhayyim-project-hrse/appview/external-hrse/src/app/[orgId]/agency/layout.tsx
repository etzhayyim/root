import { redirect } from "next/navigation";
import { getUserAuthInfo, determineEffectiveUserType } from "@/lib/auth-helpers";

/**
 * [orgId]/agency用レイアウト
 * エージェンシーとシステム管理者のみアクセス可能
 */
export default async function OrgAgencyLayout({
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

	// エージェンシーはアクセス可能
	if (effectiveUserType === "agency") {
		return <>{children}</>;
	}

	// その他のユーザータイプは適切なページにリダイレクト
	if (effectiveUserType === "job_seeker") {
		redirect("/job-seeker/profile");
	}
	if (effectiveUserType === "recruiter") {
		redirect("/");
	}

	// デフォルトはホームへ
	redirect("/");
}

