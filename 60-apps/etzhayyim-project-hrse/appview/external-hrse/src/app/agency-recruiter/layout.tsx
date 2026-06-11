"use client";

/**
 * @etzhayyim/etzhayyim-hrse#AgencyRecruiterLayout
 * エージェンシー所属リクルーター向けレイアウト
 */

import { useUser } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { getUserMetadata } from "@/lib/clerk-metadata-client";

export default function AgencyRecruiterLayout({
	children,
}: {
	children: React.ReactNode;
}) {
	const { user, isLoaded } = useUser();
	const router = useRouter();

	useEffect(() => {
		if (!isLoaded) return;

		if (!user) {
			router.push("/auth/signin");
			return;
		}

		// ユーザータイプをチェック
		const metadata = getUserMetadata(user.publicMetadata as Record<string, unknown>);

		// システム管理者（@etzhayyim.com）の場合は常にアクセス可能
		const isSystemAdmin = user.emailAddresses?.some(
			(email) => email.emailAddress?.includes("@etzhayyim.com")
		);

		if (!isSystemAdmin && metadata.userType !== "agency_recruiter") {
			// エージェンシー所属リクルーターでない場合はリダイレクト
			router.push("/");
		}
	}, [user, isLoaded, router]);

	if (!isLoaded) {
		return (
			<div className="flex min-h-screen items-center justify-center">
				<div className="text-lg text-neutral-600 dark:text-neutral-400">
					読み込み中...
				</div>
			</div>
		);
	}

	return <>{children}</>;
}
