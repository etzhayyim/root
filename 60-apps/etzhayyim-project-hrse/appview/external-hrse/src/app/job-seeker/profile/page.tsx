"use client";

/**
 * @etzhayyim/etzhayyim-hrse#JobSeekerProfileConnect
 * 求職者プロファイル作成/編集ページ（Connect-Web版）
 */

import { useUser } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { RequireAuth } from "@/lib/auth-helpers-client";
import { MultiSelect } from "@/components/MultiSelect";
import { TouchOptimizedButton } from "@/components/TouchOptimizedButton";
import { SKILL_CATEGORIES, type SkillLevel } from "@/lib/skills";
import { SkillSelector } from "@/components/SkillSelector";

// 来月の1日を取得する関数
function getNextMonthFirstDay(): string {
	const now = new Date();
	// 来月の年と月を計算
	let year = now.getFullYear();
	let month = now.getMonth(); // 0-11の範囲

	// 来月に進める
	month += 1;

	// 12月を超えた場合は来年1月になる
	if (month > 11) {
		year += 1;
		month = 0; // 1月は0
	}

	// YYYY-MM-DD形式で返す（monthは0-11なので+1して1-12に変換）
	const monthStr = String(month + 1).padStart(2, "0");
	return `${year}-${monthStr}-01`;
}

// 半年後の最後の日を取得する関数
function getSixMonthsLaterLastDay(): string {
	const now = new Date();
	// 半年後の月の最後の日を計算（現在の月 + 7ヶ月の0日 = 現在の月 + 6ヶ月の最終日）
	const sixMonthsLater = new Date(now.getFullYear(), now.getMonth() + 7, 0);
	const year = sixMonthsLater.getFullYear();
	const month = String(sixMonthsLater.getMonth() + 1).padStart(2, "0");
	const day = String(sixMonthsLater.getDate()).padStart(2, "0");
	return `${year}-${month}-${day}`;
}
import {
	useJobSeekerServiceClient,
	useMasterDataServiceClient,
	type JobSeeker,
} from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import {
	GetJobSeekerProfileRequestSchema,
	CreateJobSeekerProfileRequestSchema,
	UpdateJobSeekerProfileRequestSchema,
	SearchJobSeekersRequestSchema,
	ListNationalitiesRequestSchema,
	ListWorkPermitsRequestSchema,
	ListCertificationsRequestSchema,
	ListSpecializationsRequestSchema,
	ListLanguagesRequestSchema,
} from "@/gen/proto/hrse/v1/job_seeker_pb";

export default function JobSeekerProfilePage() {
	return (
		<RequireAuth>
			<JobSeekerProfileContent />
		</RequireAuth>
	);
}

function JobSeekerProfileContent() {
	const { user, isLoaded } = useUser();
	const router = useRouter();
	const jobSeekerClient = useJobSeekerServiceClient();
	const masterDataClient = useMasterDataServiceClient();

	const [loading, setLoading] = useState(false);
	const [profile, setProfile] = useState<JobSeeker | null>(null);
	const [formData, setFormData] = useState({
		nationalityId: "",
		workPermitId: "",
		availableFrom: "",
		desiredUnitPriceMin: "",
		desiredUnitPriceMax: "",
		desiredWorkdaysPerWeek: "3",
		remotePreference: "hybrid" as "full" | "hybrid" | "none",
		certificationIds: [] as string[],
		specializationIds: [] as string[],
		languageIds: [] as string[],
		name: "",
		age: "",
		gender: "",
		nearestStation: "",
		desiredRegion: "",
		canWorkWeekends: false,
		canWorkOvertime: false,
		canTravel: false,
		workingHours: "",
		skills: {} as Record<string, SkillLevel>,
		otherSkills: "",
	});
	const [masterData, setMasterData] = useState<{
		certifications: Array<{ id: string; nameJa: string }>;
		specializations: Array<{ id: string; nameJa: string }>;
		languages: Array<{ id: string; nameJa: string }>;
		nationalities: Array<{ id: string; nameJa: string }>;
		workPermits: Array<{ id: string; nameJa: string }>;
	}>({
		certifications: [],
		specializations: [],
		languages: [],
		nationalities: [],
		workPermits: [],
	});

	// マスターデータを取得
	const fetchMasterData = useCallback(async () => {
		try {
			const [natsRes, permitsRes, certsRes, specsRes, langsRes] = await Promise.all([
				masterDataClient.listNationalities(create(ListNationalitiesRequestSchema, {})),
				masterDataClient.listWorkPermits(create(ListWorkPermitsRequestSchema, {})),
				masterDataClient.listCertifications(create(ListCertificationsRequestSchema, {})),
				masterDataClient.listSpecializations(create(ListSpecializationsRequestSchema, {})),
				masterDataClient.listLanguages(create(ListLanguagesRequestSchema, {})),
			]);

			setMasterData({
				nationalities: (natsRes.nationalities || []).map((n) => ({ id: n.id, nameJa: n.nameJa })),
				workPermits: (permitsRes.workPermits || []).map((p) => ({ id: p.id, nameJa: p.nameJa })),
				certifications: (certsRes.certifications || []).map((c) => ({ id: c.id, nameJa: c.nameJa })),
				specializations: (specsRes.specializations || []).map((s) => ({ id: s.id, nameJa: s.nameJa })),
				languages: (langsRes.languages || []).map((l) => ({ id: l.id, nameJa: l.nameJa })),
			});
		} catch (error) {
			console.error("Failed to fetch master data:", error);
		}
	}, [masterDataClient]);

	// プロファイルを取得
	const fetchProfile = useCallback(async () => {
		if (!user?.id) return;

		try {
			const searchRes = await jobSeekerClient.searchJobSeekers(
				create(SearchJobSeekersRequestSchema, { limit: 1000 })
			);

			const found = searchRes.jobSeekers?.find((js) => js.userId === user.id);

			if (found) {
				const profileRes = await jobSeekerClient.getJobSeekerProfile(
					create(GetJobSeekerProfileRequestSchema, { id: found.id })
				);

				if (profileRes.jobSeeker) {
					const js = profileRes.jobSeeker;
					setProfile(js);
					setFormData({
						nationalityId: js.nationalityId,
						workPermitId: js.workPermitId || "",
						availableFrom: js.availableFrom,
						// 円を万円に変換（÷10000）
						desiredUnitPriceMin: (js.desiredUnitPriceMin / 10000).toString(),
						desiredUnitPriceMax: (js.desiredUnitPriceMax / 10000).toString(),
						desiredWorkdaysPerWeek: js.desiredWorkdaysPerWeek.toString(),
						remotePreference: js.remotePreference as "full" | "hybrid" | "none",
						certificationIds: js.certifications?.map((c) => c.id) || [],
						specializationIds: js.specializations?.map((s) => s.id) || [],
						languageIds: js.languages?.map((l) => l.id) || [],
						name: js.name || "",
						age: js.age?.toString() || "",
						gender: js.gender || "",
						nearestStation: js.nearestStation || "",
						desiredRegion: js.desiredRegion || "",
						canWorkWeekends: js.canWorkWeekends || false,
						canWorkOvertime: js.canWorkOvertime || false,
						canTravel: js.canTravel || false,
						workingHours: js.workingHours || "",
						skills: (js.skills || {}) as Record<string, SkillLevel>,
						otherSkills: js.skills?.["other"] || "",
					});
				}
			}
		} catch (error) {
			console.error("Failed to fetch profile:", error);
		}
	}, [user?.id, jobSeekerClient]);

	useEffect(() => {
		fetchMasterData();
	}, [fetchMasterData]);

	useEffect(() => {
		if (user?.id) {
			fetchProfile();
		}
	}, [user?.id, fetchProfile]);

	// プロファイルが存在せず、デフォルト値を設定
	useEffect(() => {
		// プロファイルが存在せず、マスターデータが読み込まれた場合のみ実行
		if (!profile && masterData.nationalities.length > 0) {
			setFormData((prev) => {
				// 既に値が設定されている場合は更新しない
				if (prev.availableFrom && prev.nationalityId) {
					return prev;
				}

				const updates: Partial<typeof prev> = {};

				// 稼働開始日が空の場合、来月の1日を設定
				if (!prev.availableFrom) {
					updates.availableFrom = getNextMonthFirstDay();
				}

				// 国籍が空の場合、日本（JP）を設定
				if (!prev.nationalityId) {
					const japan = masterData.nationalities.find((nat) => nat.id === "JP");
					if (japan) {
						updates.nationalityId = japan.id;
					}
				}

				// 更新がある場合のみ返す
				if (Object.keys(updates).length > 0) {
					return { ...prev, ...updates };
				}
				return prev;
			});
		}
	}, [profile, masterData.nationalities]);

	const handleSubmit = async (e: React.FormEvent) => {
		e.preventDefault();
		if (!user?.id) return;

		setLoading(true);
		try {
			// skillsにotherキーをマージ
			const skillsToSave: Record<string, string> = { ...formData.skills };
			if (formData.otherSkills) {
				skillsToSave["other"] = formData.otherSkills;
			} else {
				delete skillsToSave["other"];
			}

			if (profile) {
				const updateData: any = {
					id: profile.id,
					nationalityId: formData.nationalityId,
					availableFrom: formData.availableFrom,
					desiredUnitPriceMin: Number.parseFloat(formData.desiredUnitPriceMin) * 10000,
					desiredUnitPriceMax: Number.parseFloat(formData.desiredUnitPriceMax) * 10000,
					desiredWorkdaysPerWeek: Number.parseInt(formData.desiredWorkdaysPerWeek, 10),
					remotePreference: formData.remotePreference,
					certificationIds: formData.certificationIds,
					specializationIds: formData.specializationIds,
					languageIds: formData.languageIds,
					canWorkWeekends: formData.canWorkWeekends,
					canWorkOvertime: formData.canWorkOvertime,
					canTravel: formData.canTravel,
					skills: skillsToSave,
				};
				if (formData.workPermitId) updateData.workPermitId = formData.workPermitId;
				if (formData.name) updateData.name = formData.name;
				if (formData.age) updateData.age = Number.parseInt(formData.age, 10);
				if (formData.gender) updateData.gender = formData.gender;
				if (formData.nearestStation) updateData.nearestStation = formData.nearestStation;
				if (formData.desiredRegion) updateData.desiredRegion = formData.desiredRegion;
				if (formData.workingHours) updateData.workingHours = formData.workingHours;

				const response = await jobSeekerClient.updateJobSeekerProfile(
					create(UpdateJobSeekerProfileRequestSchema, updateData)
				);
				if (response.jobSeeker) {
					setProfile(response.jobSeeker);
				}
			} else {
				const createData: any = {
					userId: user.id,
					employmentType: "freelance",
					nationalityId: formData.nationalityId,
					availableFrom: formData.availableFrom,
					desiredUnitPriceMin: Number.parseFloat(formData.desiredUnitPriceMin) * 10000,
					desiredUnitPriceMax: Number.parseFloat(formData.desiredUnitPriceMax) * 10000,
					desiredWorkdaysPerWeek: Number.parseInt(formData.desiredWorkdaysPerWeek, 10),
					remotePreference: formData.remotePreference,
					certificationIds: formData.certificationIds,
					specializationIds: formData.specializationIds,
					languageIds: formData.languageIds,
					canWorkWeekends: formData.canWorkWeekends,
					canWorkOvertime: formData.canWorkOvertime,
					canTravel: formData.canTravel,
					skills: skillsToSave,
				};
				if (formData.workPermitId) createData.workPermitId = formData.workPermitId;
				if (formData.name) createData.name = formData.name;
				if (formData.age) createData.age = Number.parseInt(formData.age, 10);
				if (formData.gender) createData.gender = formData.gender;
				if (formData.nearestStation) createData.nearestStation = formData.nearestStation;
				if (formData.desiredRegion) createData.desiredRegion = formData.desiredRegion;
				if (formData.workingHours) createData.workingHours = formData.workingHours;

				const response = await jobSeekerClient.createJobSeekerProfile(
					create(CreateJobSeekerProfileRequestSchema, createData)
				);
				if (response.jobSeeker) {
					setProfile(response.jobSeeker);
				}
			}

			router.push("/job-seeker/jobs");
		} catch (error) {
			console.error("Failed to save profile:", error);
			alert("プロファイルの保存に失敗しました");
		} finally {
			setLoading(false);
		}
	};

	if (!isLoaded) {
		return <div className="p-8 dark:text-neutral-100">読み込み中...</div>;
	}

	if (!user) {
		return null;
	}

	return (
		<div className="min-h-screen bg-neutral-50 p-4 md:p-8 dark:bg-neutral-950">
			<div className="mx-auto max-w-4xl">
				<div className="mb-8 flex items-center justify-between">
					<h1 className="text-3xl font-bold text-neutral-900 dark:text-neutral-100">
						求職者プロファイル
					</h1>
					<span className="rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-800 dark:bg-green-900 dark:text-green-200">
						Connect-Web
					</span>
				</div>

				<form onSubmit={handleSubmit} className="space-y-6">
					{/* 基本情報 */}
					<div className="rounded-lg bg-white p-6 shadow dark:bg-neutral-900 dark:border dark:border-neutral-800">
						<h2 className="mb-4 text-xl font-semibold text-neutral-900 dark:text-neutral-100">
							基本情報
						</h2>
						<div className="space-y-4">
							<div>
								<label htmlFor="nationalityId" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">
									国籍 <span className="text-red-500">*</span>
								</label>
								<select
									id="nationalityId"
									value={formData.nationalityId}
									onChange={(e) => setFormData({ ...formData, nationalityId: e.target.value })}
									className="mt-1 block w-full min-h-[44px] rounded-md border border-neutral-300 px-3 py-2 text-base dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100"
									required
								>
									<option value="">選択してください</option>
									{masterData.nationalities.map((nat) => (
										<option key={nat.id} value={nat.id}>{nat.nameJa}</option>
									))}
								</select>
							</div>

							<div>
								<label htmlFor="workPermitId" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">
									在留資格（任意）
								</label>
								<select
									id="workPermitId"
									value={formData.workPermitId}
									onChange={(e) => setFormData({ ...formData, workPermitId: e.target.value })}
									className="mt-1 block w-full min-h-[44px] rounded-md border border-neutral-300 px-3 py-2 text-base dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100"
								>
									<option value="">選択してください</option>
									{masterData.workPermits.map((permit) => (
										<option key={permit.id} value={permit.id}>{permit.nameJa}</option>
									))}
								</select>
							</div>

							<div>
								<label htmlFor="availableFrom" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">
									稼働開始日 <span className="text-red-500">*</span>
								</label>
								<div className="relative mt-1">
									<input
										id="availableFrom"
										type="date"
										value={formData.availableFrom}
										onChange={(e) => setFormData({ ...formData, availableFrom: e.target.value })}
										min={getNextMonthFirstDay()}
										max={getSixMonthsLaterLastDay()}
										className="block w-full min-h-[44px] rounded-md border border-neutral-300 px-3 py-2 text-base dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
										required
									/>
									<button
										type="button"
										onClick={() => {
											const input = document.getElementById("availableFrom") as HTMLInputElement;
											if (input) {
												input.showPicker?.();
											}
										}}
										className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-500 hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-200"
										aria-label="カレンダーを開く"
									>
										<svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
										</svg>
									</button>
								</div>
							</div>
						</div>
					</div>

					{/* 個人情報 */}
					<div className="rounded-lg bg-white p-6 shadow dark:bg-neutral-900 dark:border dark:border-neutral-800">
						<h2 className="mb-4 text-xl font-semibold text-neutral-900 dark:text-neutral-100">
							個人情報
						</h2>
						<div className="space-y-4">
							<div>
								<label htmlFor="name" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">
									氏名
								</label>
								<input
									id="name"
									type="text"
									value={formData.name}
									onChange={(e) => setFormData({ ...formData, name: e.target.value })}
									className="mt-1 block w-full min-h-[44px] rounded-md border border-neutral-300 px-3 py-2 text-base dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100"
									placeholder="例: 山田 太郎"
								/>
							</div>

							<div className="grid grid-cols-2 gap-4">
								<div>
									<label htmlFor="age" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">
										年齢
									</label>
									<input
										id="age"
										type="number"
										value={formData.age}
										onChange={(e) => setFormData({ ...formData, age: e.target.value })}
										className="mt-1 block w-full min-h-[44px] rounded-md border border-neutral-300 px-3 py-2 text-base dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100"
										placeholder="例: 30"
										min="18"
										max="100"
									/>
								</div>

								<div>
									<label htmlFor="gender" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">
										性別
									</label>
									<select
										id="gender"
										value={formData.gender}
										onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
										className="mt-1 block w-full min-h-[44px] rounded-md border border-neutral-300 px-3 py-2 text-base dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100"
									>
										<option value="">選択してください</option>
										<option value="male">男性</option>
										<option value="female">女性</option>
										<option value="other">その他</option>
									</select>
								</div>
							</div>

							<div>
								<label htmlFor="nearestStation" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">
									最寄駅
								</label>
								<input
									id="nearestStation"
									type="text"
									value={formData.nearestStation}
									onChange={(e) => setFormData({ ...formData, nearestStation: e.target.value })}
									className="mt-1 block w-full min-h-[44px] rounded-md border border-neutral-300 px-3 py-2 text-base dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100"
									placeholder="例: 山手線渋谷駅"
								/>
							</div>

							<div>
								<label htmlFor="desiredRegion" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">
									希望地域
								</label>
								<input
									id="desiredRegion"
									type="text"
									value={formData.desiredRegion}
									onChange={(e) => setFormData({ ...formData, desiredRegion: e.target.value })}
									className="mt-1 block w-full min-h-[44px] rounded-md border border-neutral-300 px-3 py-2 text-base dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100"
									placeholder="例: 東京都23区内"
								/>
							</div>

							<div className="space-y-3">
								<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">
									勤務条件
								</label>
								<div className="space-y-2">
									<label className="flex items-center space-x-2">
										<input
											type="checkbox"
											checked={formData.canWorkWeekends}
											onChange={(e) => setFormData({ ...formData, canWorkWeekends: e.target.checked })}
											className="h-5 w-5 rounded border-neutral-300 text-brand-600 focus:ring-brand-500 dark:border-neutral-600 dark:bg-neutral-800"
										/>
										<span className="text-neutral-700 dark:text-neutral-300">休日作業可</span>
									</label>
									<label className="flex items-center space-x-2">
										<input
											type="checkbox"
											checked={formData.canWorkOvertime}
											onChange={(e) => setFormData({ ...formData, canWorkOvertime: e.target.checked })}
											className="h-5 w-5 rounded border-neutral-300 text-brand-600 focus:ring-brand-500 dark:border-neutral-600 dark:bg-neutral-800"
										/>
										<span className="text-neutral-700 dark:text-neutral-300">残業可</span>
									</label>
									<label className="flex items-center space-x-2">
										<input
											type="checkbox"
											checked={formData.canTravel}
											onChange={(e) => setFormData({ ...formData, canTravel: e.target.checked })}
											className="h-5 w-5 rounded border-neutral-300 text-brand-600 focus:ring-brand-500 dark:border-neutral-600 dark:bg-neutral-800"
										/>
										<span className="text-neutral-700 dark:text-neutral-300">出張可</span>
									</label>
								</div>
							</div>
						</div>
					</div>

					{/* 希望条件 */}
					<div className="rounded-lg bg-white p-6 shadow dark:bg-neutral-900 dark:border dark:border-neutral-800">
						<h2 className="mb-4 text-xl font-semibold text-neutral-900 dark:text-neutral-100">
							希望条件
						</h2>
						<div className="space-y-4">
							<div className="grid grid-cols-2 gap-4">
								<div>
									<label htmlFor="desiredUnitPriceMin" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">
										希望単価（最小） <span className="text-red-500">*</span>
									</label>
									<div className="relative mt-1">
										<input
											id="desiredUnitPriceMin"
											type="number"
											value={formData.desiredUnitPriceMin}
											onChange={(e) => setFormData({ ...formData, desiredUnitPriceMin: e.target.value })}
											className="block w-full min-h-[44px] rounded-md border border-neutral-300 px-3 py-2 pr-12 text-base dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
											required
											min="0"
											step="0.1"
											placeholder="例: 30"
										/>
										<span className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-500 dark:text-neutral-400 pointer-events-none">
											万円
										</span>
									</div>
									<p className="mt-1 text-xs text-neutral-500 dark:text-neutral-400">月額</p>
								</div>
								<div>
									<label htmlFor="desiredUnitPriceMax" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">
										希望単価（最大） <span className="text-red-500">*</span>
									</label>
									<div className="relative mt-1">
										<input
											id="desiredUnitPriceMax"
											type="number"
											value={formData.desiredUnitPriceMax}
											onChange={(e) => setFormData({ ...formData, desiredUnitPriceMax: e.target.value })}
											className="block w-full min-h-[44px] rounded-md border border-neutral-300 px-3 py-2 pr-12 text-base dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
											required
											min="0"
											step="0.1"
											placeholder="例: 50"
										/>
										<span className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-500 dark:text-neutral-400 pointer-events-none">
											万円
										</span>
									</div>
									<p className="mt-1 text-xs text-neutral-500 dark:text-neutral-400">月額</p>
								</div>
							</div>

							<div>
								<label htmlFor="desiredWorkdaysPerWeek" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">
									週あたり稼働日数 <span className="text-red-500">*</span>
								</label>
								<select
									id="desiredWorkdaysPerWeek"
									value={formData.desiredWorkdaysPerWeek}
									onChange={(e) => setFormData({ ...formData, desiredWorkdaysPerWeek: e.target.value })}
									className="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2 dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100"
									required
								>
									<option value="1">1日</option>
									<option value="2">2日</option>
									<option value="3">3日</option>
									<option value="4">4日</option>
									<option value="5">5日</option>
								</select>
							</div>

							<div>
								<label htmlFor="remotePreference" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">
									リモート希望 <span className="text-red-500">*</span>
								</label>
								<select
									id="remotePreference"
									value={formData.remotePreference}
									onChange={(e) => setFormData({ ...formData, remotePreference: e.target.value as "full" | "hybrid" | "none" })}
									className="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2 dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100"
									required
								>
									<option value="full">フルリモート</option>
									<option value="hybrid">ハイブリッド</option>
									<option value="none">リモート不可</option>
								</select>
							</div>
						</div>
					</div>

					{/* 資格・専門分野・言語 */}
					<div className="rounded-lg bg-white p-6 shadow dark:bg-neutral-900 dark:border dark:border-neutral-800">
						<h2 className="mb-4 text-xl font-semibold text-neutral-900 dark:text-neutral-100">
							資格・専門分野・言語
						</h2>
						<div className="space-y-4">
							<MultiSelect
								label="資格"
								options={masterData.certifications.map((c) => ({ id: c.id, name: c.nameJa }))}
								selectedIds={formData.certificationIds}
								onChange={(ids) => setFormData({ ...formData, certificationIds: ids })}
								required
							/>
							<MultiSelect
								label="専門分野"
								options={masterData.specializations.map((s) => ({ id: s.id, name: s.nameJa }))}
								selectedIds={formData.specializationIds}
								onChange={(ids) => setFormData({ ...formData, specializationIds: ids })}
								required
							/>
							<MultiSelect
								label="言語"
								options={masterData.languages.map((l) => ({ id: l.id, name: l.nameJa }))}
								selectedIds={formData.languageIds}
								onChange={(ids) => setFormData({ ...formData, languageIds: ids })}
								required
							/>
						</div>
					</div>

					{/* 業務スキル */}
					<div className="rounded-lg bg-white p-6 shadow dark:bg-neutral-900 dark:border dark:border-neutral-800">
						<h2 className="mb-4 text-xl font-semibold text-neutral-900 dark:text-neutral-100">
							業務スキル
						</h2>
						<div className="mb-4">
							<p className="mb-2 text-sm text-neutral-600 dark:text-neutral-400">
								各スキルのレベルを選択してください
							</p>
							<ul className="space-y-1 text-sm text-neutral-600 dark:text-neutral-400">
								<li>【A】業務の独立遂行。業務課題発見・解決。後進教育</li>
								<li>【B】業務の独立遂行</li>
								<li>【C】業務を上位者指導のもと遂行</li>
								<li>【D】実務を通じた学習経験あり</li>
								<li>【E】学習経験あり</li>
							</ul>
						</div>
						<div className="space-y-6">
							{SKILL_CATEGORIES.map((category) => (
								<SkillSelector
									key={category.id}
									categoryName={category.nameJa}
									skills={category.skills}
									selectedSkills={formData.skills}
									onChange={(skills) => setFormData({ ...formData, skills })}
								/>
							))}
						</div>
						<div className="mt-6">
							<label htmlFor="otherSkills" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">
								その他
							</label>
							<textarea
								id="otherSkills"
								value={formData.otherSkills}
								onChange={(e) => setFormData({ ...formData, otherSkills: e.target.value })}
								className="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2 text-base dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
								rows={4}
								placeholder="上記以外のスキルや補足事項があればご記入ください"
							/>
						</div>
					</div>

					<div className="flex justify-end gap-4">
						<TouchOptimizedButton variant="secondary" onClick={() => router.back()}>
							キャンセル
						</TouchOptimizedButton>
						<TouchOptimizedButton type="submit" variant="primary" disabled={loading}>
							{loading ? "保存中..." : profile ? "更新" : "作成"}
						</TouchOptimizedButton>
					</div>
				</form>
			</div>
		</div>
	);
}
