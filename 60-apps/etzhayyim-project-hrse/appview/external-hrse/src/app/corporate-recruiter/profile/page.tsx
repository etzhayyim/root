"use client";

/**
 * @etzhayyim/etzhayyim-hrse#CorporateRecruiterProfile
 * 企業担当リクルーター向けプロファイルページ
 * DBに保存する機能を実装
 */

import { useUser } from "@clerk/nextjs";
import { useState, useCallback, useEffect } from "react";
import { TouchOptimizedButton } from "@/components/TouchOptimizedButton";
import { useAgencyServiceClient, type Recruiter } from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import {
	GetRecruiterByUserIdRequestSchema,
	CreateRecruiterProfileRequestSchema,
	UpdateRecruiterProfileRequestSchema,
} from "@/gen/proto/hrse/v1/agency_pb";

interface CompanyInfo {
	id?: string;
	name: string;
	industry: string;
	employeeCount: string;
	location: string;
	website: string;
	description: string;
}

interface ContactPersonInfo {
	departmentName: string;
	position: string;
	phoneNumber: string;
}

interface CorporateRecruiterProfileData {
	company: CompanyInfo;
	contact: ContactPersonInfo;
}

const initialProfileData: CorporateRecruiterProfileData = {
	company: {
		name: "",
		industry: "",
		employeeCount: "",
		location: "",
		website: "",
		description: "",
	},
	contact: {
		departmentName: "",
		position: "",
		phoneNumber: "",
	},
};

export default function CorporateRecruiterProfilePage() {
	const { user, isLoaded } = useUser();
	const agencyClient = useAgencyServiceClient();
	const [profileData, setProfileData] = useState<CorporateRecruiterProfileData>(initialProfileData);
	const [recruiterProfile, setRecruiterProfile] = useState<Recruiter | null>(null);
	const [loading, setLoading] = useState(true);
	const [saving, setSaving] = useState(false);
	const [saveSuccess, setSaveSuccess] = useState(false);
	const [error, setError] = useState<string | null>(null);

	// プロファイルデータをAPIから取得
	const fetchProfile = useCallback(async () => {
		if (!user?.id) return;

		try {
			const response = await agencyClient.getRecruiterByUserId(
				create(GetRecruiterByUserIdRequestSchema, {
					userId: user.id,
				})
			);
			if (response.recruiter) {
				setRecruiterProfile(response.recruiter);
				// APIレスポンスからフォームデータを設定
				setProfileData({
					company: {
						id: response.recruiter.company?.id || "",
						name: response.recruiter.company?.name || "",
						industry: response.recruiter.company?.industry || "",
						employeeCount: response.recruiter.company?.employeeCount || "",
						location: response.recruiter.company?.location || "",
						website: response.recruiter.company?.website || "",
						description: response.recruiter.company?.description || "",
					},
					contact: {
						departmentName: response.recruiter.departmentName || "",
						position: response.recruiter.position || "",
						phoneNumber: response.recruiter.phoneNumber || "",
					},
				});
			}
		} catch (err) {
			console.error("[Corporate Recruiter Profile] Failed to fetch profile:", err);
			// プロファイルが存在しない場合はエラーにしない（新規作成可能）
		} finally {
			setLoading(false);
		}
	}, [user?.id, agencyClient]);

	useEffect(() => {
		if (user?.id) {
			fetchProfile();
		}
	}, [user?.id, fetchProfile]);

	const handleCompanyChange = useCallback((field: keyof CompanyInfo, value: string) => {
		setProfileData((prev) => ({
			...prev,
			company: {
				...prev.company,
				[field]: value,
			},
		}));
	}, []);

	const handleContactChange = useCallback((field: keyof ContactPersonInfo, value: string) => {
		setProfileData((prev) => ({
			...prev,
			contact: {
				...prev.contact,
				[field]: value,
			},
		}));
	}, []);

	const handleSave = async () => {
		if (!user?.id) return;
		if (!profileData.company.name.trim()) {
			setError("会社名は必須です");
			return;
		}

		setSaving(true);
		setError(null);
		setSaveSuccess(false);

		try {
			// デバッグ: フォームデータを確認
			console.log("[CorporateRecruiterProfile] profileData:", profileData);

			if (recruiterProfile?.id) {
				// 既存プロファイルを更新 - オプショナルフィールドは条件付きで追加
				const updateRequestInit: {
					id: string;
					companyName?: string;
					industry?: string;
					employeeCount?: string;
					location?: string;
					website?: string;
					description?: string;
					departmentName?: string;
					position?: string;
					phoneNumber?: string;
				} = {
					id: recruiterProfile.id,
				};
				if (profileData.company.name) updateRequestInit.companyName = profileData.company.name;
				if (profileData.company.industry) updateRequestInit.industry = profileData.company.industry;
				if (profileData.company.employeeCount) updateRequestInit.employeeCount = profileData.company.employeeCount;
				if (profileData.company.location) updateRequestInit.location = profileData.company.location;
				if (profileData.company.website) updateRequestInit.website = profileData.company.website;
				if (profileData.company.description) updateRequestInit.description = profileData.company.description;
				if (profileData.contact.departmentName) updateRequestInit.departmentName = profileData.contact.departmentName;
				if (profileData.contact.position) updateRequestInit.position = profileData.contact.position;
				if (profileData.contact.phoneNumber) updateRequestInit.phoneNumber = profileData.contact.phoneNumber;

				console.log("[CorporateRecruiterProfile] updateRequestInit:", updateRequestInit);
				const updateMessage = create(UpdateRecruiterProfileRequestSchema, updateRequestInit);
				console.log("[CorporateRecruiterProfile] updateMessage (protobuf):", updateMessage);
				console.log("[CorporateRecruiterProfile] updateMessage.industry:", updateMessage.industry);

				const response = await agencyClient.updateRecruiterProfile(updateMessage);
				console.log("[CorporateRecruiterProfile] updateResponse:", response);
				if (response.recruiter) {
					setRecruiterProfile(response.recruiter);
				}
			} else {
				// 新規プロファイルを作成 - オプショナルフィールドは条件付きで追加
				const createRequestInit: {
					userId: string;
					companyName: string;
					industry?: string;
					employeeCount?: string;
					location?: string;
					website?: string;
					description?: string;
					departmentName?: string;
					position?: string;
					phoneNumber?: string;
				} = {
					userId: user.id,
					companyName: profileData.company.name,
				};
				if (profileData.company.industry) createRequestInit.industry = profileData.company.industry;
				if (profileData.company.employeeCount) createRequestInit.employeeCount = profileData.company.employeeCount;
				if (profileData.company.location) createRequestInit.location = profileData.company.location;
				if (profileData.company.website) createRequestInit.website = profileData.company.website;
				if (profileData.company.description) createRequestInit.description = profileData.company.description;
				if (profileData.contact.departmentName) createRequestInit.departmentName = profileData.contact.departmentName;
				if (profileData.contact.position) createRequestInit.position = profileData.contact.position;
				if (profileData.contact.phoneNumber) createRequestInit.phoneNumber = profileData.contact.phoneNumber;

				console.log("[CorporateRecruiterProfile] createRequestInit:", createRequestInit);
				const createMessage = create(CreateRecruiterProfileRequestSchema, createRequestInit);
				console.log("[CorporateRecruiterProfile] createMessage (protobuf):", createMessage);
				console.log("[CorporateRecruiterProfile] createMessage.industry:", createMessage.industry);

				const response = await agencyClient.createRecruiterProfile(createMessage);
				console.log("[CorporateRecruiterProfile] createResponse:", response);
				if (response.recruiter) {
					setRecruiterProfile(response.recruiter);
				}
			}

			setSaveSuccess(true);
			setTimeout(() => setSaveSuccess(false), 3000);
		} catch (err) {
			console.error("Failed to save profile:", err);
			const errorMessage = err instanceof Error ? err.message : "プロファイルの保存に失敗しました";
			setError(errorMessage);
		} finally {
			setSaving(false);
		}
	};

	if (!isLoaded || loading) {
		return (
			<div className="flex min-h-screen items-center justify-center">
				<div className="text-lg text-neutral-600 dark:text-neutral-400">
					読み込み中...
				</div>
			</div>
		);
	}

	return (
		<div className="min-h-screen bg-neutral-50 p-4 md:p-8 dark:bg-neutral-950">
			<div className="mx-auto max-w-4xl">
				{/* ヘッダー */}
				<div className="mb-8">
					<h1 className="text-3xl font-bold text-neutral-900 dark:text-neutral-100">
						プロファイル設定
					</h1>
					<p className="mt-2 text-neutral-600 dark:text-neutral-400">
						企業情報と担当者情報を設定してください
					</p>
				</div>

				{/* プロファイルフォーム */}
				<div className="space-y-6">
					{/* 企業情報 */}
					<div className="rounded-lg bg-white p-6 shadow dark:bg-neutral-900">
						<h2 className="mb-4 text-xl font-semibold text-neutral-900 dark:text-neutral-100">
							企業情報
						</h2>
						<div className="grid gap-4 md:grid-cols-2">
							<div>
								<label className="mb-1 block text-sm font-medium text-neutral-700 dark:text-neutral-300">
									会社名 <span className="text-red-500">*</span>
								</label>
								<input
									type="text"
									value={profileData.company.name}
									onChange={(e) => handleCompanyChange("name", e.target.value)}
									className="w-full rounded-md border border-neutral-300 px-3 py-2 text-neutral-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100"
									placeholder="株式会社○○○"
								/>
							</div>
							<div>
								<label className="mb-1 block text-sm font-medium text-neutral-700 dark:text-neutral-300">
									業種
								</label>
								<select
									value={profileData.company.industry}
									onChange={(e) => handleCompanyChange("industry", e.target.value)}
									className="w-full rounded-md border border-neutral-300 px-3 py-2 text-neutral-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100"
								>
									<option value="">選択してください</option>
									<option value="IT">IT・通信</option>
									<option value="manufacturing">製造業</option>
									<option value="finance">金融・保険</option>
									<option value="retail">小売・流通</option>
									<option value="service">サービス業</option>
									<option value="healthcare">医療・福祉</option>
									<option value="education">教育</option>
									<option value="construction">建設・不動産</option>
									<option value="other">その他</option>
								</select>
							</div>
							<div>
								<label className="mb-1 block text-sm font-medium text-neutral-700 dark:text-neutral-300">
									従業員数
								</label>
								<select
									value={profileData.company.employeeCount}
									onChange={(e) => handleCompanyChange("employeeCount", e.target.value)}
									className="w-full rounded-md border border-neutral-300 px-3 py-2 text-neutral-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100"
								>
									<option value="">選択してください</option>
									<option value="1-10">1〜10名</option>
									<option value="11-50">11〜50名</option>
									<option value="51-100">51〜100名</option>
									<option value="101-500">101〜500名</option>
									<option value="501-1000">501〜1000名</option>
									<option value="1001+">1001名以上</option>
								</select>
							</div>
							<div>
								<label className="mb-1 block text-sm font-medium text-neutral-700 dark:text-neutral-300">
									所在地
								</label>
								<input
									type="text"
									value={profileData.company.location}
									onChange={(e) => handleCompanyChange("location", e.target.value)}
									className="w-full rounded-md border border-neutral-300 px-3 py-2 text-neutral-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100"
									placeholder="東京都渋谷区"
								/>
							</div>
							<div className="md:col-span-2">
								<label className="mb-1 block text-sm font-medium text-neutral-700 dark:text-neutral-300">
									会社ウェブサイト
								</label>
								<input
									type="url"
									value={profileData.company.website}
									onChange={(e) => handleCompanyChange("website", e.target.value)}
									className="w-full rounded-md border border-neutral-300 px-3 py-2 text-neutral-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100"
									placeholder="https://example.com"
								/>
							</div>
							<div className="md:col-span-2">
								<label className="mb-1 block text-sm font-medium text-neutral-700 dark:text-neutral-300">
									会社概要
								</label>
								<textarea
									value={profileData.company.description}
									onChange={(e) => handleCompanyChange("description", e.target.value)}
									rows={4}
									className="w-full rounded-md border border-neutral-300 px-3 py-2 text-neutral-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100"
									placeholder="会社の事業内容や特徴をご記入ください"
								/>
							</div>
						</div>
					</div>

					{/* 担当者情報 */}
					<div className="rounded-lg bg-white p-6 shadow dark:bg-neutral-900">
						<h2 className="mb-4 text-xl font-semibold text-neutral-900 dark:text-neutral-100">
							担当者情報
						</h2>
						<div className="grid gap-4 md:grid-cols-2">
							<div>
								<label className="mb-1 block text-sm font-medium text-neutral-700 dark:text-neutral-300">
									部署名
								</label>
								<input
									type="text"
									value={profileData.contact.departmentName}
									onChange={(e) => handleContactChange("departmentName", e.target.value)}
									className="w-full rounded-md border border-neutral-300 px-3 py-2 text-neutral-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100"
									placeholder="人事部"
								/>
							</div>
							<div>
								<label className="mb-1 block text-sm font-medium text-neutral-700 dark:text-neutral-300">
									役職
								</label>
								<input
									type="text"
									value={profileData.contact.position}
									onChange={(e) => handleContactChange("position", e.target.value)}
									className="w-full rounded-md border border-neutral-300 px-3 py-2 text-neutral-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100"
									placeholder="採用担当"
								/>
							</div>
							<div>
								<label className="mb-1 block text-sm font-medium text-neutral-700 dark:text-neutral-300">
									電話番号
								</label>
								<input
									type="tel"
									value={profileData.contact.phoneNumber}
									onChange={(e) => handleContactChange("phoneNumber", e.target.value)}
									className="w-full rounded-md border border-neutral-300 px-3 py-2 text-neutral-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100"
									placeholder="03-1234-5678"
								/>
							</div>
							<div>
								<label className="mb-1 block text-sm font-medium text-neutral-700 dark:text-neutral-300">
									メールアドレス
								</label>
								<input
									type="email"
									value={user?.primaryEmailAddress?.emailAddress || ""}
									disabled
									className="w-full rounded-md border border-neutral-300 bg-neutral-100 px-3 py-2 text-neutral-500 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-400"
								/>
								<p className="mt-1 text-xs text-neutral-500 dark:text-neutral-400">
									メールアドレスはClerkアカウント設定から変更できます
								</p>
							</div>
						</div>
					</div>

					{/* 保存ボタン */}
					<div className="flex items-center justify-end gap-4">
						{error && (
							<p className="text-sm text-red-600 dark:text-red-400">{error}</p>
						)}
						{saveSuccess && (
							<p className="text-sm text-green-600 dark:text-green-400">
								保存しました
							</p>
						)}
						<TouchOptimizedButton
							variant="primary"
							onClick={handleSave}
							disabled={saving}
						>
							{saving ? "保存中..." : "プロファイルを保存"}
						</TouchOptimizedButton>
					</div>
				</div>
			</div>
		</div>
	);
}
