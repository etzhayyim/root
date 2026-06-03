"use client";

/**
 * @etzhayyim/etzhayyim-hrse#OrgRecruiterProfileConnect
 * Organization リクルータープロファイル作成/編集ページ（Connect-Web版）
 */

import { useUser } from "@clerk/nextjs";
import { useRouter, useParams } from "next/navigation";
import { useCallback, useEffect, useState, useTransition } from "react";
import { RequireAuth } from "@/lib/auth-helpers-client";
import {
	useAgencyServiceClient,
	type Recruiter,
	type Agency,
} from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import {
	GetRecruiterProfileRequestSchema,
	GetAgencyByClerkOrgIdRequestSchema,
	CreateRecruiterRequestSchema,
	UpdateRecruiterRequestSchema,
} from "@/gen/proto/hrse/v1/agency_pb";

export default function RecruiterProfilePage() {
	return (
		<RequireAuth>
			<RecruiterProfileContent />
		</RequireAuth>
	);
}

function RecruiterProfileContent() {
	const { user, isLoaded } = useUser();
	const router = useRouter();
	const params = useParams();
	const orgId = params?.orgId as string | undefined;
	const agencyClient = useAgencyServiceClient();
	const [isPending, startTransition] = useTransition();

	const [loading, setLoading] = useState(true);
	const [agency, setAgency] = useState<Agency | null>(null);
	const [profile, setProfile] = useState<Recruiter | null>(null);
	const [formData, setFormData] = useState({
		position: "",
		role: "standard",
	});
	const [formState, setFormState] = useState<{
		success: boolean;
		error: string | null;
	}>({
		success: false,
		error: null,
	});

	// orgIdからagencyを取得
	const fetchAgency = useCallback(async () => {
		if (!orgId) {
			console.log("[Recruiter Profile] No orgId provided");
			return;
		}

		setLoading(true);
		setFormState({ success: false, error: null });
		try {
			const res = await agencyClient.getAgencyByClerkOrgId(
				create(GetAgencyByClerkOrgIdRequestSchema, { clerkOrgId: orgId })
			);
			if (res.agency) {
				setAgency(res.agency);
			} else {
				setFormState({
					success: false,
					error: "エージェンシーが見つかりません。先にエージェンシープロファイルを作成してください。",
				});
			}
		} catch (error) {
			console.error("[Recruiter Profile] Failed to fetch agency:", error);
			const errorMessage = error instanceof Error ? error.message : "エージェンシーの取得に失敗しました";
			setFormState({ success: false, error: errorMessage });
		} finally {
			setLoading(false);
		}
	}, [orgId, agencyClient]);

	// プロファイル取得
	const fetchProfile = useCallback(async () => {
		if (!user?.id || !agency) return;

		try {
			const res = await agencyClient.getRecruiterProfile(
				create(GetRecruiterProfileRequestSchema, {})
			);
			if (res.recruiter) {
				setProfile(res.recruiter);
				setFormData({
					position: res.recruiter.position || "",
					role: res.recruiter.role,
				});
			}
		} catch (error) {
			console.error("[Recruiter Profile] Failed to fetch profile:", error);
			// プロファイルが存在しない場合はエラーにしない（新規作成可能）
		}
	}, [user?.id, agency, agencyClient]);

	useEffect(() => {
		fetchAgency();
	}, [fetchAgency]);

	useEffect(() => {
		if (user?.id && agency) {
			fetchProfile();
		}
	}, [user?.id, agency, fetchProfile]);

	const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
		e.preventDefault();
		if (!user?.id || !agency) return;

		setFormState({ success: false, error: null });
		setLoading(true);

		try {
			if (profile) {
				await agencyClient.updateRecruiter(
					create(UpdateRecruiterRequestSchema, {
						id: profile.id,
						position: formData.position || undefined,
						role: formData.role,
					})
				);
			} else {
				await agencyClient.createRecruiter(
					create(CreateRecruiterRequestSchema, {
						agencyId: agency.id,
						position: formData.position || undefined,
						role: formData.role,
					})
				);
			}

			startTransition(() => {
				setFormState({ success: true, error: null });
			});

			await fetchProfile();

			setTimeout(() => {
				startTransition(() => {
					setFormState((prev) => ({ ...prev, success: false }));
				});
			}, 3000);
		} catch (error) {
			console.error("Failed to save profile:", error);
			const errorMessage = error instanceof Error ? error.message : "プロファイルの保存に失敗しました";
			startTransition(() => {
				setFormState({ success: false, error: errorMessage });
			});
		} finally {
			setLoading(false);
		}
	};

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

	if (!agency) {
		return (
			<div className="min-h-screen bg-neutral-50 p-4 md:p-8 dark:bg-neutral-950">
				<div className="mx-auto max-w-4xl">
					<div className="mb-6 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-4">
						<p className="text-red-800 dark:text-red-200 font-medium">
							{formState.error || "エージェンシーが見つかりません"}
						</p>
					</div>
					<div className="rounded-lg bg-white p-6 shadow-md dark:bg-neutral-900 dark:border dark:border-neutral-800">
						<p className="text-neutral-600 dark:text-neutral-400">
							先にエージェンシープロファイルを作成してください。
						</p>
					</div>
				</div>
			</div>
		);
	}

	return (
		<div className="min-h-screen bg-neutral-50 p-4 md:p-8 dark:bg-neutral-950">
			<div className="mx-auto max-w-4xl">
				{profile && (
					<div className="mb-6 rounded-lg border border-neutral-200 bg-white p-4 text-sm text-neutral-800 shadow-sm dark:border-neutral-800 dark:bg-neutral-900 dark:text-neutral-100">
						<h2 className="mb-3 text-lg font-semibold">現在のリクルーター情報</h2>
						<div className="space-y-1">
							<div>エージェンシー: {agency.name}</div>
							<div>役職: {profile.position ?? "未設定"}</div>
							<div>ロール: {profile.role}</div>
						</div>
					</div>
				)}

				<div className="mb-8 flex items-center gap-3">
					<h1 className="text-3xl font-bold text-neutral-900 dark:text-neutral-100">
						リクルータープロファイル
					</h1>
					<span className="rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-800 dark:bg-green-900 dark:text-green-200">
						Connect-Web
					</span>
				</div>

				{formState.success && (
					<div className="mb-6 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 p-4">
						<p className="text-green-800 dark:text-green-200 font-medium">プロファイルを保存しました</p>
					</div>
				)}

				{formState.error && (
					<div className="mb-6 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-4">
						<p className="text-red-800 dark:text-red-200 font-medium">{formState.error}</p>
					</div>
				)}

				<div className="mb-6 rounded-lg border border-neutral-200 bg-white p-4 text-sm text-neutral-800 shadow-sm dark:border-neutral-800 dark:bg-neutral-900 dark:text-neutral-100">
					<div className="font-semibold mb-2">エージェンシー:</div>
					<div>{agency.name}</div>
				</div>

				<form onSubmit={handleSubmit} className="space-y-6">
					<div className="rounded-lg bg-white p-6 shadow-md dark:bg-neutral-900 dark:border dark:border-neutral-800">
						<h2 className="mb-6 text-xl font-semibold text-neutral-900 dark:text-neutral-100">基本情報</h2>
						<div className="space-y-6">
							<div>
								<label htmlFor="position" className="block text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
									役職
								</label>
								<input
									id="position"
									type="text"
									value={formData.position}
									onChange={(e) => setFormData({ ...formData, position: e.target.value })}
									className="mt-1 block w-full min-h-[44px] rounded-md border-2 border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-800 px-4 py-3 text-base text-neutral-900 dark:text-neutral-100"
									placeholder="例: シニアリクルーター"
								/>
							</div>

							<div>
								<label htmlFor="role" className="block text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
									ロール <span className="text-red-600 dark:text-red-400">*</span>
								</label>
								<select
									id="role"
									value={formData.role}
									onChange={(e) => setFormData({ ...formData, role: e.target.value })}
									className="mt-1 block w-full min-h-[44px] rounded-md border-2 border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-800 px-4 py-3 text-base text-neutral-900 dark:text-neutral-100 focus:border-brand-500 dark:focus:border-brand-400"
									required
								>
									<option value="standard">標準</option>
									<option value="admin">管理者</option>
									<option value="disabled">無効</option>
								</select>
							</div>
						</div>
					</div>

					<div className="flex justify-end gap-4">
						<button
							type="submit"
							disabled={isPending || loading}
							className="rounded-md bg-brand-600 dark:bg-brand-500 px-6 py-3 text-white font-semibold hover:bg-brand-700 dark:hover:bg-brand-600 disabled:opacity-50 disabled:cursor-not-allowed min-h-[44px] transition-colors shadow-md hover:shadow-lg active:scale-[0.98]"
						>
							{loading ? "保存中..." : profile ? "更新" : "作成"}
						</button>
					</div>
				</form>
			</div>
		</div>
	);
}
