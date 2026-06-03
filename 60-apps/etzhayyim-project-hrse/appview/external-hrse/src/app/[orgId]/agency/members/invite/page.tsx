"use client";

/**
 * @etzhayyim/etzhayyim-hrse#OrgAgencyMembersInviteConnect
 * エージェンシーメンバー招待ページ（Connect-Web版）
 */

import { useUser } from "@clerk/nextjs";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { RequireAuth } from "@/lib/auth-helpers-client";
import { useAgencyServiceClient, type Agency } from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import {
	GetAgencyByClerkOrgIdRequestSchema,
	InviteRecruiterRequestSchema,
} from "@/gen/proto/hrse/v1/agency_pb";
import { TouchOptimizedButton } from "@/components/TouchOptimizedButton";

export default function AgencyMembersInvitePage() {
	return (
		<RequireAuth>
			<AgencyMembersInviteContent />
		</RequireAuth>
	);
}

function AgencyMembersInviteContent() {
	const { user, isLoaded } = useUser();
	const params = useParams();
	const orgId = params?.orgId as string | undefined;
	const agencyClient = useAgencyServiceClient();

	const [profile, setProfile] = useState<Agency | null>(null);
	const [loading, setLoading] = useState(true);
	const [inviteEmail, setInviteEmail] = useState("");
	const [inviteRole, setInviteRole] = useState("org:member");
	const [inviting, setInviting] = useState(false);
	const [success, setSuccess] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const [alreadyInvited, setAlreadyInvited] = useState(false);

	// プロファイル取得
	const fetchProfile = useCallback(async () => {
		if (!orgId) return;

		setLoading(true);
		try {
			const res = await agencyClient.getAgencyByClerkOrgId(
				create(GetAgencyByClerkOrgIdRequestSchema, { clerkOrgId: orgId })
			);
			if (res.agency) {
				setProfile(res.agency);
			}
		} catch (err) {
			console.error("Failed to fetch profile:", err);
		} finally {
			setLoading(false);
		}
	}, [orgId, agencyClient]);

	useEffect(() => {
		fetchProfile();
	}, [fetchProfile]);

	const handleInviteRecruiter = async (e: React.FormEvent) => {
		e.preventDefault();
		if (!profile || !inviteEmail.trim()) return;

		setInviting(true);
		setError(null);
		setSuccess(false);
		setAlreadyInvited(false);

		try {
			await agencyClient.inviteRecruiter(
				create(InviteRecruiterRequestSchema, {
					agencyId: profile.id,
					emailAddress: inviteEmail.trim(),
					role: inviteRole,
				})
			);

			setSuccess(true);
			setInviteEmail("");
			setInviteRole("org:member");

			await fetchProfile();

			setTimeout(() => {
				setSuccess(false);
			}, 3000);
		} catch (err) {
			console.error("Failed to invite recruiter:", err);
			const message = err instanceof Error ? err.message : "リクルーターの招待に失敗しました";

			// すでに招待済み/メンバー登録済みの場合は警告として表示
			if (message.includes("すでにメンバー") || message.includes("すでに招待") || message.includes("already_a_member")) {
				setAlreadyInvited(true);
			} else {
				setError(message);
			}
		} finally {
			setInviting(false);
		}
	};

	if (loading || !isLoaded) {
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
				<div className="mb-6">
					<Link
						href={`/${orgId || ""}/agency/members`}
						className="text-brand-600 dark:text-brand-400 hover:underline mb-4 inline-block"
					>
						← メンバー一覧に戻る
					</Link>
					<div className="flex items-center gap-3">
						<h1 className="text-3xl font-bold text-neutral-900 dark:text-neutral-100">
							メンバーを招待
						</h1>
						<span className="rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-800 dark:bg-green-900 dark:text-green-200">
							Connect-Web
						</span>
					</div>
				</div>

				{success && (
					<div className="mb-6 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 p-4">
						<p className="text-green-800 dark:text-green-200 font-medium">
							招待メールを送信しました
						</p>
					</div>
				)}

				{alreadyInvited && (
					<div className="mb-6 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 p-4">
						<div className="flex items-start gap-3">
							<svg className="w-5 h-5 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
								<path fillRule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
							</svg>
							<div>
								<p className="text-amber-800 dark:text-amber-200 font-medium">
									すでに招待済みです
								</p>
								<p className="text-amber-700 dark:text-amber-300 text-sm mt-1">
									このメールアドレスはすでにメンバーとして登録されているか、招待が送信されています。
								</p>
							</div>
						</div>
					</div>
				)}

				{error && (
					<div className="mb-6 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-4">
						<p className="text-red-800 dark:text-red-200 font-medium">{error}</p>
					</div>
				)}

				<form onSubmit={handleInviteRecruiter} className="rounded-lg bg-white p-6 shadow-md dark:bg-neutral-900 dark:border dark:border-neutral-800">
					<div className="space-y-6">
						<div>
							<label htmlFor="inviteEmail" className="block text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
								メールアドレス <span className="text-red-600 dark:text-red-400">*</span>
							</label>
							<input
								id="inviteEmail"
								type="email"
								value={inviteEmail}
								onChange={(e) => setInviteEmail(e.target.value)}
								className="mt-1 block w-full min-h-[44px] rounded-md border-2 border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-800 px-4 py-3 text-base text-neutral-900 dark:text-neutral-100"
								placeholder="recruiter@example.com"
								required
								disabled={inviting}
							/>
						</div>

						<div>
							<label htmlFor="inviteRole" className="block text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
								ロール
							</label>
							<select
								id="inviteRole"
								value={inviteRole}
								onChange={(e) => setInviteRole(e.target.value)}
								className="mt-1 block w-full min-h-[44px] rounded-md border-2 border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-800 px-4 py-3 text-base text-neutral-900 dark:text-neutral-100"
								disabled={inviting}
							>
								<option value="org:member">メンバー</option>
								<option value="org:admin">管理者</option>
							</select>
						</div>

						<div className="flex justify-end gap-4">
							<Link href={`/${orgId || ""}/agency/members`}>
								<TouchOptimizedButton type="button" variant="secondary" size="md" disabled={inviting}>
									キャンセル
								</TouchOptimizedButton>
							</Link>
							<TouchOptimizedButton
								type="submit"
								variant="primary"
								size="md"
								disabled={inviting || !inviteEmail.trim()}
							>
								{inviting ? "招待中..." : "招待を送信"}
							</TouchOptimizedButton>
						</div>
					</div>
				</form>
			</div>
		</div>
	);
}
