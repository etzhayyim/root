"use client";

/**
 * @etzhayyim/etzhayyim-hrse#OrgAgencyMembersConnect
 * エージェンシーメンバー管理ページ（Connect-Web版）
 */

import Link from "next/link";
import { useParams } from "next/navigation";
import { useUser } from "@clerk/nextjs";
import { useCallback, useEffect, useState } from "react";
import { RequireAuth } from "@/lib/auth-helpers-client";
import { useAgencyServiceClient, type Agency } from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import { GetAgencyByClerkOrgIdRequestSchema } from "@/gen/proto/hrse/v1/agency_pb";
import { TouchOptimizedButton } from "@/components/TouchOptimizedButton";

export default function AgencyMembersPage() {
	return (
		<RequireAuth>
			<AgencyMembersContent />
		</RequireAuth>
	);
}

function AgencyMembersContent() {
	const params = useParams();
	const orgId = params?.orgId as string | undefined;
	const { user, isLoaded } = useUser();
	const agencyClient = useAgencyServiceClient();

	const [loading, setLoading] = useState(true);
	const [profile, setProfile] = useState<Agency | null>(null);

	const fetchProfile = useCallback(async () => {
		if (!orgId || !isLoaded) return;

		setLoading(true);
		try {
			const res = await agencyClient.getAgencyByClerkOrgId(
				create(GetAgencyByClerkOrgIdRequestSchema, { clerkOrgId: orgId })
			);
			if (res.agency) {
				setProfile(res.agency);
			}
		} catch (error) {
			console.error("Failed to fetch profile:", error);
		} finally {
			setLoading(false);
		}
	}, [orgId, isLoaded, agencyClient]);

	useEffect(() => {
		fetchProfile();
	}, [fetchProfile]);

	if (!isLoaded || loading) {
		return (
			<div className="flex min-h-screen items-center justify-center">
				<div className="text-lg">読み込み中...</div>
			</div>
		);
	}

	if (!user) {
		return null;
	}

	if (!profile) {
		return (
			<div className="min-h-screen bg-neutral-50 p-4 md:p-8 dark:bg-neutral-950">
				<div className="mx-auto max-w-4xl">
					<div className="rounded-lg bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 p-6">
						<p className="text-yellow-800 dark:text-yellow-200 font-medium mb-4">
							エージェンシープロファイルが作成されていません。
						</p>
						<Link href={`/${orgId || ""}/agency/profile`}>
							<TouchOptimizedButton variant="primary" size="md">
								プロファイルを作成
							</TouchOptimizedButton>
						</Link>
					</div>
				</div>
			</div>
		);
	}

	return (
		<div className="min-h-screen bg-neutral-50 p-4 md:p-8 dark:bg-neutral-950">
			<div className="mx-auto max-w-4xl">
				<div className="mb-6 flex items-center justify-between">
					<h1 className="text-3xl font-bold text-neutral-900 dark:text-neutral-100">
						メンバー管理
					</h1>
					<Link href={`/${orgId || ""}/agency/members/invite`}>
						<TouchOptimizedButton variant="primary" size="md">
							メンバーを招待
						</TouchOptimizedButton>
					</Link>
				</div>

				{/* 登録済みメンバー一覧 */}
				<div className="rounded-lg bg-white p-6 shadow-md dark:bg-neutral-900 dark:border dark:border-neutral-800">
					<h2 className="mb-4 text-xl font-semibold text-neutral-900 dark:text-neutral-100">
						登録済みメンバー
					</h2>
					{profile.recruiters && profile.recruiters.length > 0 ? (
						<div className="space-y-2">
							{profile.recruiters.map((recruiter) => (
								<div
									key={recruiter.id}
									className="flex items-center justify-between rounded-md border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 p-4"
								>
									<div className="flex-1">
										<div className="font-medium text-neutral-900 dark:text-neutral-100">
											{recruiter.position || "リクルーター"}
										</div>
										<div className="text-sm text-neutral-600 dark:text-neutral-400">
											ロール: {recruiter.role}
										</div>
									</div>
								</div>
							))}
						</div>
					) : (
						<p className="text-neutral-600 dark:text-neutral-400">
							登録済みのメンバーはいません。
						</p>
					)}
				</div>
			</div>
		</div>
	);
}
