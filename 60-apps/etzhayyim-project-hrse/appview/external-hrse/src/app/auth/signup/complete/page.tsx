"use client";

/**
 * @etzhayyim/etzhayyim-hrse#SignUpCompleteConnect
 * サインアップ完了後の処理ページ（Connect-Web版）
 */

import { useUser } from "@clerk/nextjs";
import { useSearchParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState, useMemo } from "react";
import { useAgencyServiceClient } from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import { GetAgencyProfileRequestSchema } from "@/gen/proto/hrse/v1/agency_pb";
import { saveUserTypeAction } from "@/lib/clerk-user-type-actions";
import type { UserType } from "@/lib/clerk-user-type";

export default function SignUpCompletePage() {
	const { user, isLoaded } = useUser();
	const searchParams = useSearchParams();
	const router = useRouter();
	const agencyClient = useAgencyServiceClient();

	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const [clerkOrgId, setClerkOrgId] = useState<string | null>(null);
	const [orgIdResolved, setOrgIdResolved] = useState(false);

	// URLパラメータからユーザータイプを取得
	const userTypeParam = searchParams.get("userType") || "job_seeker";
	// agency_recruiter はメール招待経由でのみ登録されるため、直接サインアップでは含めない
	const validUserTypes: UserType[] = ["job_seeker", "corporate_recruiter", "agency_recruiter", "agency"];

	// ユーザータイプを決定
	// - 明示的に設定されたuserTypeはそのまま保持
	// - 組織メンバーシップがあり、userType未設定の場合は agency_recruiter（招待経由の新規ユーザー）
	const userType: UserType = useMemo(() => {
		const hasOrgMembership = user?.organizationMemberships && user.organizationMemberships.length > 0;

		// 明示的に設定されたuserTypeはそのまま保持
		// corporate_recruiter は組織メンバーシップがあっても corporate_recruiter のまま
		if (validUserTypes.includes(userTypeParam as UserType)) {
			return userTypeParam as UserType;
		}

		// 組織メンバーシップがあり、userType未設定の場合は agency_recruiter（招待経由の新規ユーザー）
		if (hasOrgMembership) {
			console.log("[SignUpComplete] Unknown userType with org membership, setting to agency_recruiter");
			return "agency_recruiter";
		}

		return "job_seeker";
	}, [userTypeParam, user?.organizationMemberships]);

	// Agencyプロファイルを取得（agencyタイプの場合のみ）
	const fetchAgencyProfile = useCallback(async () => {
		if (!user?.id || userType !== "agency") return;

		try {
			const res = await agencyClient.getAgencyProfile(
				create(GetAgencyProfileRequestSchema, {})
			);
			if (res.agency?.clerkOrgId) {
				setClerkOrgId(res.agency.clerkOrgId);
			}
		} catch (err) {
			console.error("Failed to fetch agency profile:", err);
		} finally {
			setOrgIdResolved(true);
		}
	}, [user?.id, userType, agencyClient]);

	// agency_recruiter の場合、ユーザーの組織メンバーシップから組織IDを取得
	useEffect(() => {
		if (!user?.id || userType !== "agency_recruiter") return;

		// Clerk の organizationMemberships から組織IDを取得
		// 招待を承諾した場合、ユーザーには組織メンバーシップが付与されている
		const memberships = user.organizationMemberships;
		if (memberships && memberships.length > 0) {
			// 最初の組織メンバーシップを使用（招待経由なので1つのはず）
			const orgId = memberships[0].organization.id;
			console.log("[SignUpComplete] Found organization from membership:", orgId);
			setClerkOrgId(orgId);
		}
		setOrgIdResolved(true);
	}, [user?.id, user?.organizationMemberships, userType]);

	useEffect(() => {
		if (user?.id && userType === "agency") {
			fetchAgencyProfile();
		}
	}, [user?.id, userType, fetchAgencyProfile]);

	useEffect(() => {
		async function handleComplete() {
			if (!isLoaded) return;

			if (!user) {
				router.push("/auth/signin");
				return;
			}

			try {
				setLoading(true);
				setError(null);

				// ユーザータイプをメタデータに保存
				const result = await saveUserTypeAction(user.id, userType);

				if (!result.success) {
					throw new Error(result.error || "Failed to save user type");
				}

				// クライアント側のユーザーデータをリロードしてメタデータを反映
				// これにより、リダイレクト先のレイアウトで正しいuserTypeが取得できる
				await user.reload();

				// ユーザータイプに応じて適切なページにリダイレクト
				switch (userType) {
					case "job_seeker":
						router.push("/job-seeker/profile");
						break;
					case "corporate_recruiter":
						router.push("/corporate-recruiter/profile");
						break;
					case "agency_recruiter":
						// エージェンシー所属リクルーター（メール招待経由）
						if (clerkOrgId) {
							router.push(`/${clerkOrgId}/agency-recruiter/profile`);
						} else {
							// orgIdがない場合はエラー（通常は発生しない）
							console.error("[SignUpComplete] No org ID found for agency_recruiter");
							router.push("/agency-recruiter/profile");
						}
						break;
					case "agency":
						if (clerkOrgId) {
							router.push(`/${clerkOrgId}/agency/profile`);
						} else {
							router.push("/agency/profile");
						}
						break;
					default:
						router.push("/job-seeker/profile");
				}
			} catch (err) {
				console.error("Failed to save user type:", err);
				setError("ユーザータイプの保存に失敗しました");
				setTimeout(() => {
					router.push("/job-seeker/profile");
				}, 2000);
			} finally {
				setLoading(false);
			}
		}

		// agency または agency_recruiter の場合は orgId の解決を待つ
		if ((userType === "agency" || userType === "agency_recruiter") && !orgIdResolved && user?.id) {
			return;
		}

		handleComplete();
	}, [user, isLoaded, userType, router, clerkOrgId, orgIdResolved]);

	if (!isLoaded || loading) {
		return (
			<div className="flex min-h-screen items-center justify-center bg-neutral-50 dark:bg-neutral-950">
				<div className="text-center">
					<div className="mb-4 inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-brand-600 border-r-transparent dark:border-brand-400"></div>
					<p className="text-neutral-900 dark:text-neutral-100">
						アカウントを設定しています...
					</p>
				</div>
			</div>
		);
	}

	if (error) {
		return (
			<div className="flex min-h-screen items-center justify-center bg-neutral-50 dark:bg-neutral-950">
				<div className="text-center">
					<p className="mb-4 text-red-600 dark:text-red-400">{error}</p>
					<p className="text-sm text-neutral-600 dark:text-neutral-400">
						プロファイルページにリダイレクトします...
					</p>
				</div>
			</div>
		);
	}

	return null;
}
