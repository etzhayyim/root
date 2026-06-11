"use client";

/**
 * @etzhayyim/etzhayyim-hrse#AgencyMembersRedirectConnect
 * エージェンシーメンバー管理ページ（リダイレクト用、Connect-Web版）
 */

import { RequireAuth } from "@/lib/auth-helpers-client";
import { useUser, useOrganization } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function AgencyMembersPage() {
	return (
		<RequireAuth>
			<AgencyMembersContent />
		</RequireAuth>
	);
}

function AgencyMembersContent() {
	const { user, isLoaded } = useUser();
	const { organization, isLoaded: isOrgLoaded } = useOrganization();
	const router = useRouter();

	const clerkOrgId = organization?.id || user?.organizationMemberships?.[0]?.organization?.id;

	useEffect(() => {
		if (!isLoaded || !isOrgLoaded) return;

		if (clerkOrgId) {
			router.replace(`/${clerkOrgId}/agency/members`);
		}
	}, [isLoaded, isOrgLoaded, clerkOrgId, router]);

	return (
		<div className="flex min-h-screen items-center justify-center">
			<div className="text-lg">読み込み中...</div>
		</div>
	);
}
