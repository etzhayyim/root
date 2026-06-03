"use client";

/**
 * @etzhayyim/etzhayyim-hrse#AgencyProfileConnect
 * エージェンシープロファイル作成/編集ページ（Connect-Web版）
 */

import { useUser } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState, useTransition } from "react";
import { RequireAuth } from "@/lib/auth-helpers-client";
import { useAgencyServiceClient, type Agency } from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import {
	GetAgencyProfileRequestSchema,
	CreateAgencyRequestSchema,
	UpdateAgencyRequestSchema,
} from "@/gen/proto/hrse/v1/agency_pb";

export default function AgencyProfilePage() {
	return (
		<RequireAuth>
			<AgencyProfileContent />
		</RequireAuth>
	);
}

function AgencyProfileContent() {
	const { user, isLoaded } = useUser();
	const router = useRouter();
	const agencyClient = useAgencyServiceClient();
	const [isPending, startTransition] = useTransition();

	const [loading, setLoading] = useState(true);
	const [profile, setProfile] = useState<Agency | null>(null);
	const [formData, setFormData] = useState({
		name: "",
		licenseNumber: "",
		contactEmail: "",
		contactPhone: "",
		address: "",
	});
	const [formState, setFormState] = useState<{
		success: boolean;
		error: string | null;
		fieldErrors: Record<string, string>;
	}>({
		success: false,
		error: null,
		fieldErrors: {},
	});

	// プロファイルを取得
	const fetchProfile = useCallback(async () => {
		if (!user?.id) return;

		setLoading(true);
		try {
			const response = await agencyClient.getAgencyProfile(
				create(GetAgencyProfileRequestSchema, {})
			);

			if (response.agency) {
				setProfile(response.agency);
				setFormData({
					name: response.agency.name,
					licenseNumber: response.agency.licenseNumber || "",
					contactEmail: response.agency.contactEmail || "",
					contactPhone: response.agency.contactPhone || "",
					address: response.agency.address || "",
				});
			}
		} catch (error) {
			console.error("Failed to fetch profile:", error);
		} finally {
			setLoading(false);
		}
	}, [user?.id, agencyClient]);

	useEffect(() => {
		if (user?.id) {
			fetchProfile();
		}
	}, [user?.id, fetchProfile]);

	const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
		e.preventDefault();
		if (!user?.id) return;

		setFormState({ success: false, error: null, fieldErrors: {} });

		const submitData = {
			name: formData.name.trim(),
			licenseNumber: formData.licenseNumber?.trim() || undefined,
			contactEmail: formData.contactEmail?.trim() || undefined,
			contactPhone: formData.contactPhone?.trim() || undefined,
			address: formData.address?.trim() || undefined,
		};

		try {
			if (profile && profile.id) {
				const response = await agencyClient.updateAgency(
					create(UpdateAgencyRequestSchema, {
						id: profile.id,
						name: submitData.name,
						licenseNumber: submitData.licenseNumber,
						contactEmail: submitData.contactEmail,
						contactPhone: submitData.contactPhone,
						address: submitData.address,
					})
				);
				if (response.agency) {
					setProfile(response.agency);
				}
			} else {
				const response = await agencyClient.createAgency(
					create(CreateAgencyRequestSchema, {
						name: submitData.name,
						licenseNumber: submitData.licenseNumber,
						contactEmail: submitData.contactEmail,
						contactPhone: submitData.contactPhone,
						address: submitData.address,
					})
				);
				if (response.agency) {
					setProfile(response.agency);
				}
			}

			startTransition(() => {
				setFormState({ success: true, error: null, fieldErrors: {} });
			});

			// プロファイルを再取得
			await fetchProfile();

			// 成功メッセージは3秒後に消す
			setTimeout(() => {
				startTransition(() => {
					setFormState((prev) => ({ ...prev, success: false }));
				});
			}, 3000);

			// clerkOrgIdが存在する場合は動的ルートにリダイレクト
			if (profile?.clerkOrgId) {
				router.replace(`/${profile.clerkOrgId}/agency/profile`);
			}
		} catch (error) {
			console.error("Failed to save profile:", error);
			const errorMessage = error instanceof Error ? error.message : "プロファイルの保存に失敗しました";
			startTransition(() => {
				setFormState({ success: false, error: errorMessage, fieldErrors: {} });
			});
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

	return (
		<div className="min-h-screen bg-neutral-50 p-4 md:p-8 dark:bg-neutral-950">
			<div className="mx-auto max-w-4xl">
				{profile && (
					<div className="mb-6 rounded-lg border border-neutral-200 bg-white p-4 text-sm text-neutral-800 shadow-sm dark:border-neutral-800 dark:bg-neutral-900 dark:text-neutral-100">
						<h2 className="mb-3 text-lg font-semibold">現在のエージェンシー情報</h2>
						<div className="space-y-1">
							<div>エージェンシー名: {profile.name}</div>
							<div>許可番号: {profile.licenseNumber ?? "未設定"}</div>
							<div>メール: {profile.contactEmail ?? "未設定"}</div>
							<div>電話: {profile.contactPhone ?? "未設定"}</div>
							<div>住所: {profile.address ?? "未設定"}</div>
							<div>Clerk組織ID: {profile.clerkOrgId ?? "未設定"}</div>
						</div>
					</div>
				)}

				<div className="mb-8 flex items-center justify-between">
					<h1 className="text-3xl font-bold text-neutral-900 dark:text-neutral-100">
						エージェンシープロファイル
					</h1>
					<span className="rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-800 dark:bg-green-900 dark:text-green-200">
						Connect-Web
					</span>
				</div>

				{/* 成功メッセージ */}
				{formState.success && (
					<div className="mb-6 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 p-4">
						<p className="text-green-800 dark:text-green-200 font-medium">
							プロファイルを保存しました
						</p>
					</div>
				)}

				{/* エラーメッセージ */}
				{formState.error && (
					<div className="mb-6 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-4">
						<p className="text-red-800 dark:text-red-200 font-medium">
							{formState.error}
						</p>
					</div>
				)}

				<form onSubmit={handleSubmit} className="space-y-6">
					<div className="rounded-lg bg-white p-6 shadow-md dark:bg-neutral-900 dark:border dark:border-neutral-800">
						<h2 className="mb-6 text-xl font-semibold text-neutral-900 dark:text-neutral-100">
							基本情報
						</h2>
						<div className="space-y-6">
							<div>
								<label htmlFor="name" className="block text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
									エージェンシー名 <span className="text-red-600 dark:text-red-400">*</span>
								</label>
								<input
									id="name"
									type="text"
									value={formData.name}
									onChange={(e) => setFormData({ ...formData, name: e.target.value })}
									className="mt-1 block w-full min-h-[44px] rounded-md border-2 px-4 py-3 text-base text-neutral-900 dark:text-neutral-100 border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-800 focus:border-brand-500 dark:focus:border-brand-400"
									placeholder="エージェンシー名を入力してください"
									required
								/>
							</div>

							<div>
								<label htmlFor="licenseNumber" className="block text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
									許可番号
								</label>
								<input
									id="licenseNumber"
									type="text"
									value={formData.licenseNumber}
									onChange={(e) => setFormData({ ...formData, licenseNumber: e.target.value })}
									className="mt-1 block w-full min-h-[44px] rounded-md border-2 px-4 py-3 text-base text-neutral-900 dark:text-neutral-100 border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-800 focus:border-brand-500 dark:focus:border-brand-400"
									placeholder="許可番号を入力してください"
								/>
							</div>

							<div>
								<label htmlFor="contactEmail" className="block text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
									連絡先メールアドレス
								</label>
								<input
									id="contactEmail"
									type="email"
									value={formData.contactEmail}
									onChange={(e) => setFormData({ ...formData, contactEmail: e.target.value })}
									className="mt-1 block w-full min-h-[44px] rounded-md border-2 px-4 py-3 text-base text-neutral-900 dark:text-neutral-100 border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-800 focus:border-brand-500 dark:focus:border-brand-400"
									placeholder="contact@example.com"
								/>
							</div>

							<div>
								<label htmlFor="contactPhone" className="block text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
									連絡先電話番号
								</label>
								<input
									id="contactPhone"
									type="tel"
									value={formData.contactPhone}
									onChange={(e) => setFormData({ ...formData, contactPhone: e.target.value })}
									className="mt-1 block w-full min-h-[44px] rounded-md border-2 px-4 py-3 text-base text-neutral-900 dark:text-neutral-100 border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-800 focus:border-brand-500 dark:focus:border-brand-400"
									placeholder="03-1234-5678"
								/>
							</div>

							<div>
								<label htmlFor="address" className="block text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
									住所
								</label>
								<textarea
									id="address"
									value={formData.address}
									onChange={(e) => setFormData({ ...formData, address: e.target.value })}
									rows={3}
									className="mt-1 block w-full min-h-[88px] rounded-md border-2 px-4 py-3 text-base text-neutral-900 dark:text-neutral-100 border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-800 focus:border-brand-500 dark:focus:border-brand-400 resize-y"
									placeholder="住所を入力してください"
								/>
							</div>
						</div>
					</div>

					<div className="flex justify-end gap-4">
						<button
							type="submit"
							disabled={isPending}
							className="rounded-md bg-brand-600 dark:bg-brand-500 px-6 py-3 text-white font-semibold hover:bg-brand-700 dark:hover:bg-brand-600 disabled:opacity-50 disabled:cursor-not-allowed min-h-[44px] transition-colors shadow-md hover:shadow-lg active:scale-[0.98]"
						>
							{isPending ? "保存中..." : profile ? "更新" : "作成"}
						</button>
					</div>
				</form>
			</div>
		</div>
	);
}
