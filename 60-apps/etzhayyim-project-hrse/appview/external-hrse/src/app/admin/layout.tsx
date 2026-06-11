import { redirect } from "next/navigation";
import { getUserAuthInfo, determineEffectiveUserType } from "@/lib/auth-helpers";

/**
 * 管理者ページ用レイアウト
 * システム管理者（@etzhayyim.com）のみアクセス可能
 */
export default async function AdminLayout({
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

	// システム管理者のみアクセス可能
	if (effectiveUserType === "admin") {
		return <>{children}</>;
	}

	// その他のユーザータイプは適切なページにリダイレクト
	if (effectiveUserType === "job_seeker") {
		redirect("/job-seeker/profile");
	}
	if (effectiveUserType === "agency") {
		redirect("/agency");
	}
	if (effectiveUserType === "recruiter") {
		redirect("/");
	}

	// デフォルトはホームへ
	redirect("/");
}

