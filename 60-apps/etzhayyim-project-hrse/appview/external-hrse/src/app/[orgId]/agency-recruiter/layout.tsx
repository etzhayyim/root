import { redirect } from "next/navigation";
import { getUserAuthInfo, determineEffectiveUserType } from "@/lib/auth-helpers";

/**
 * [orgId]/agency-recruiter用レイアウト
 * エージェンシー所属リクルーターとシステム管理者のみアクセス可能
 */
export default async function OrgAgencyRecruiterLayout({
	children,
	params,
}: {
	children: React.ReactNode;
	params: Promise<{ orgId: string }>;
}) {
	const { orgId } = await params;
	const authInfo = await getUserAuthInfo();

	// 未認証の場合はサインインページへ
	if (!authInfo.userId) {
		redirect("/auth/signin");
	}

	const effectiveUserType = determineEffectiveUserType(authInfo);

	// システム管理者は全ページアクセス可能（オンボーディングチェック不要）
	if (effectiveUserType === "admin") {
		return <>{children}</>;
	}

	// エージェンシー所属リクルーターの場合
	if (effectiveUserType === "agency_recruiter") {
		return <>{children}</>;
	}

	// その他のユーザータイプは適切なページにリダイレクト
	if (effectiveUserType === "job_seeker") {
		redirect("/job-seeker/profile");
	}
	if (effectiveUserType === "agency") {
		redirect(`/${orgId}/agency`);
	}
	if (effectiveUserType === "corporate_recruiter") {
		redirect("/corporate-recruiter");
	}

	// デフォルトはホームへ
	redirect("/");
}
