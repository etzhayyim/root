"use client";

/**
 * @etzhayyim/etzhayyim-hrse#CorporateRecruiterJobs
 * 企業担当リクルーター向け案件管理ページ
 */

import { useUser } from "@clerk/nextjs";
import { useState, useCallback, useEffect } from "react";
import { TouchOptimizedButton } from "@/components/TouchOptimizedButton";
import { MultiSelect } from "@/components/MultiSelect";
import { SkillSelector } from "@/components/SkillSelector";
import { SKILL_CATEGORIES, type SkillLevel } from "@/lib/skills";
import { useJobServiceClient, useAgencyServiceClient, useMasterDataServiceClient, type Job, type Recruiter } from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import {
	CreateJobRequestSchema,
	ListJobsByCompanyRequestSchema,
	UpdateJobRequestSchema,
	PublishJobRequestSchema,
} from "@/gen/proto/hrse/v1/job_pb";
import {
	GetRecruiterByUserIdRequestSchema,
} from "@/gen/proto/hrse/v1/agency_pb";
import {
	ListNationalitiesRequestSchema,
	ListWorkPermitsRequestSchema,
	ListCertificationsRequestSchema,
	ListSpecializationsRequestSchema,
	ListLanguagesRequestSchema,
} from "@/gen/proto/hrse/v1/job_seeker_pb";

interface JobFormData {
	title: string;
	nationalityId: string;
	workPermitId: string;
	nearestStation: string;
	desiredRegion: string;
	canWorkWeekends: boolean;
	canWorkOvertime: boolean;
	canTravel: boolean;
	jobUnitPriceMin: string;
	jobUnitPriceMax: string;
	desiredWorkdaysPerWeek: string;
	remotePreference: "full" | "hybrid" | "none";
	startDate: string;
	endDate: string;
	certificationIds: string[];
	specializationIds: string[];
	languageIds: string[];
	skills: Record<string, SkillLevel>;
	otherSkills: string;
}

const initialFormData: JobFormData = {
	title: "",
	nationalityId: "",
	workPermitId: "",
	nearestStation: "",
	desiredRegion: "",
	canWorkWeekends: false,
	canWorkOvertime: false,
	canTravel: false,
	jobUnitPriceMin: "",
	jobUnitPriceMax: "",
	desiredWorkdaysPerWeek: "5",
	remotePreference: "hybrid",
	startDate: "",
	endDate: "",
	certificationIds: [],
	specializationIds: [],
	languageIds: [],
	skills: {},
	otherSkills: "",
};

// 案件の表示ステータスを計算するヘルパー関数
// 募集期間の日付比較で判定: 募集前 / 募集中 / 終了
type DisplayStatus = "before_recruiting" | "recruiting" | "ended" | "draft" | "closed";

function getJobDisplayStatus(job: { status: string; startDate?: string; endDate?: string }): DisplayStatus {
	const status = job.status?.toLowerCase() || "";
	if (status === "closed") return "closed";
	if (status === "draft") return "draft";
	if (status === "open" || status === "published" || status === "expired") {
		const today = new Date();
		today.setHours(0, 0, 0, 0);
		if (job.startDate) {
			const startDate = new Date(job.startDate);
			startDate.setHours(0, 0, 0, 0);
			if (today < startDate) return "before_recruiting";
		}
		if (job.endDate) {
			const endDate = new Date(job.endDate);
			endDate.setHours(0, 0, 0, 0);
			if (endDate < today) return "ended";
		}
		return "recruiting";
	}
	return "closed";
}

export default function CorporateRecruiterJobsPage() {
	const { user, isLoaded } = useUser();
	const jobClient = useJobServiceClient();
	const agencyClient = useAgencyServiceClient();
	const masterDataClient = useMasterDataServiceClient();

	const [jobs, setJobs] = useState<Job[]>([]);
	const [recruiterProfile, setRecruiterProfile] = useState<Recruiter | null>(null);
	const [showCreateForm, setShowCreateForm] = useState(false);
	const [formData, setFormData] = useState<JobFormData>(initialFormData);
	const [saving, setSaving] = useState(false);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const [editingJob, setEditingJob] = useState<Job | null>(null);
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

	// Recruiterプロファイルとjobsを読み込み
	const fetchData = useCallback(async () => {
		if (!user?.id) return;

		setLoading(true);
		try {
			const recruiterRes = await agencyClient.getRecruiterByUserId(
				create(GetRecruiterByUserIdRequestSchema, { userId: user.id })
			);

			if (recruiterRes.recruiter) {
				setRecruiterProfile(recruiterRes.recruiter);

				const companyId = recruiterRes.recruiter.companyId || recruiterRes.recruiter.company?.id;
				if (companyId) {
					const jobsRes = await jobClient.listJobsByCompany(
						create(ListJobsByCompanyRequestSchema, {
							companyId: companyId,
							limit: 100,
							offset: 0,
						})
					);
					if (jobsRes.jobs) {
						setJobs(jobsRes.jobs);
					}
				}
			}
		} catch (err) {
			console.error("Failed to fetch data:", err);
			setError("データの取得に失敗しました");
		} finally {
			setLoading(false);
		}
	}, [user?.id, jobClient, agencyClient]);

	useEffect(() => {
		fetchMasterData();
	}, [fetchMasterData]);

	useEffect(() => {
		if (isLoaded && user?.id) {
			fetchData();
		}
	}, [isLoaded, user?.id, fetchData]);

	// 案件作成処理
	const handleCreateJob = async () => {
		const companyId = recruiterProfile?.companyId || recruiterProfile?.company?.id;

		if (!companyId) {
			setError("プロファイルが設定されていません。先にプロファイル設定で企業情報を登録してください。");
			return;
		}

		if (!formData.title.trim()) {
			setError("案件タイトルを入力してください");
			return;
		}

		setSaving(true);
		setError(null);

		try {
			const minPrice = formData.jobUnitPriceMin ? parseFloat(formData.jobUnitPriceMin) * 10000 : undefined;
			const maxPrice = formData.jobUnitPriceMax ? parseFloat(formData.jobUnitPriceMax) * 10000 : undefined;

			// skills + otherSkills を統合
			const skillsToSave: Record<string, string> = { ...formData.skills };
			if (formData.otherSkills) {
				skillsToSave["other"] = formData.otherSkills;
			}

			const requestData: any = {
				companyId: companyId,
				title: formData.title,
				description: formData.title,
				jobTypes: ["freelance"],
				jobLocation: formData.nearestStation || formData.desiredRegion || "",
				remoteAllowed: formData.remotePreference !== "none",
				nationalityId: formData.nationalityId || undefined,
				workPermitId: formData.workPermitId || undefined,
				nearestStation: formData.nearestStation || undefined,
				desiredRegion: formData.desiredRegion || undefined,
				canWorkWeekends: formData.canWorkWeekends,
				canWorkOvertime: formData.canWorkOvertime,
				canTravel: formData.canTravel,
				desiredWorkdaysPerWeek: parseInt(formData.desiredWorkdaysPerWeek) || 5,
				skills: skillsToSave,
				requiredCertificationIds: formData.certificationIds,
				requiredSpecializationIds: formData.specializationIds,
				requiredLanguageIds: formData.languageIds,
			};

			if (minPrice && minPrice > 0) requestData.jobUnitPriceMin = minPrice;
			if (maxPrice && maxPrice > 0) requestData.jobUnitPriceMax = maxPrice;
			if (formData.startDate) requestData.startDate = formData.startDate;
			if (formData.endDate) requestData.endDate = formData.endDate;

			const response = await jobClient.createJob(create(CreateJobRequestSchema, requestData));

			if (response.job) {
				setJobs(prev => [response.job!, ...prev]);
				setShowCreateForm(false);
				setFormData(initialFormData);
				setEditingJob(null);
			}
		} catch (err) {
			console.error("Failed to create job:", err);
			setError("案件の作成に失敗しました");
		} finally {
			setSaving(false);
		}
	};

	// 編集モードを開く
	const handleEditJob = (job: Job) => {
		setEditingJob(job);

		// skills から "other" キーを分離
		const jobSkills: Record<string, SkillLevel> = {};
		let otherSkillsText = "";
		if (job.skills) {
			for (const [key, value] of Object.entries(job.skills)) {
				if (key === "other") {
					otherSkillsText = value;
				} else {
					jobSkills[key] = value as SkillLevel;
				}
			}
		}

		setFormData({
			title: job.title,
			nationalityId: job.nationalityId || "",
			workPermitId: job.workPermitId || "",
			nearestStation: job.nearestStation || job.jobLocation || "",
			desiredRegion: job.desiredRegion || "",
			canWorkWeekends: job.canWorkWeekends || false,
			canWorkOvertime: job.canWorkOvertime || false,
			canTravel: job.canTravel || false,
			jobUnitPriceMin: job.jobUnitPriceMin ? (job.jobUnitPriceMin / 10000).toString() : "",
			jobUnitPriceMax: job.jobUnitPriceMax ? (job.jobUnitPriceMax / 10000).toString() : "",
			desiredWorkdaysPerWeek: job.desiredWorkdaysPerWeek?.toString() || "5",
			remotePreference: job.remoteAllowed ? "hybrid" : "none",
			startDate: job.startDate || "",
			endDate: job.endDate || "",
			certificationIds: job.requiredCertifications?.map((c) => c.id) || [],
			specializationIds: job.requiredSpecializations?.map((s) => s.id) || [],
			languageIds: job.requiredLanguages?.map((l) => l.id) || [],
			skills: jobSkills,
			otherSkills: otherSkillsText,
		});
		setShowCreateForm(true);
	};

	// 案件更新処理
	const handleUpdateJob = async () => {
		if (!editingJob?.id) return;

		if (!formData.title.trim()) {
			setError("案件タイトルを入力してください");
			return;
		}

		setSaving(true);
		setError(null);

		try {
			const minPrice = formData.jobUnitPriceMin ? parseFloat(formData.jobUnitPriceMin) * 10000 : undefined;
			const maxPrice = formData.jobUnitPriceMax ? parseFloat(formData.jobUnitPriceMax) * 10000 : undefined;

			// skills + otherSkills を統合
			const skillsToSave: Record<string, string> = { ...formData.skills };
			if (formData.otherSkills) {
				skillsToSave["other"] = formData.otherSkills;
			}

			const requestData: any = {
				id: editingJob.id,
				title: formData.title,
				description: formData.title,
				jobLocation: formData.nearestStation || formData.desiredRegion || "",
				remoteAllowed: formData.remotePreference !== "none",
				requiredCertificationIds: formData.certificationIds,
				requiredSpecializationIds: formData.specializationIds,
				requiredLanguageIds: formData.languageIds,
				nationalityId: formData.nationalityId || undefined,
				workPermitId: formData.workPermitId || undefined,
				nearestStation: formData.nearestStation || undefined,
				desiredRegion: formData.desiredRegion || undefined,
				canWorkWeekends: formData.canWorkWeekends,
				canWorkOvertime: formData.canWorkOvertime,
				canTravel: formData.canTravel,
				desiredWorkdaysPerWeek: parseInt(formData.desiredWorkdaysPerWeek) || 5,
				skills: skillsToSave,
			};

			if (minPrice && minPrice > 0) requestData.jobUnitPriceMin = minPrice;
			if (maxPrice && maxPrice > 0) requestData.jobUnitPriceMax = maxPrice;
			if (formData.startDate) requestData.startDate = formData.startDate;
			if (formData.endDate) requestData.endDate = formData.endDate;

			const response = await jobClient.updateJob(create(UpdateJobRequestSchema, requestData));

			if (response.job) {
				setJobs(prev => prev.map(j => j.id === response.job!.id ? response.job! : j));
				setShowCreateForm(false);
				setFormData(initialFormData);
				setEditingJob(null);
			}
		} catch (err) {
			console.error("Failed to update job:", err);
			setError("案件の更新に失敗しました");
		} finally {
			setSaving(false);
		}
	};

	// 案件削除処理（statusを"closed"に更新）
	const handleDeleteJob = async (jobId: string) => {
		if (!confirm("この案件を削除（終了）してもよろしいですか？")) return;

		try {
			const response = await jobClient.updateJob(
				create(UpdateJobRequestSchema, { id: jobId, status: "closed" })
			);
			if (response.job) {
				setJobs(prev => prev.filter(j => j.id !== jobId));
			}
		} catch (err) {
			console.error("Failed to delete job:", err);
			setError("案件の削除に失敗しました");
		}
	};

	// 案件公開処理
	const handlePublishJob = async (jobId: string) => {
		const job = jobs.find(j => j.id === jobId);
		if (!job) return;

		const today = new Date();
		today.setHours(0, 0, 0, 0);

		if (job.startDate) {
			const startDate = new Date(job.startDate);
			startDate.setHours(0, 0, 0, 0);
			if (today < startDate) {
				alert("募集期間前なので公開できません");
				return;
			}
		}

		if (job.endDate) {
			const endDate = new Date(job.endDate);
			endDate.setHours(0, 0, 0, 0);
			if (today > endDate) {
				alert("募集期間後なので公開できません");
				return;
			}
		}

		if (!confirm("この案件を公開してもよろしいですか？公開すると求職者から閲覧可能になります。")) return;

		try {
			const response = await jobClient.publishJob(create(PublishJobRequestSchema, { id: jobId }));
			if (response.job) {
				setJobs(prev => prev.map(j => j.id === response.job!.id ? response.job! : j));
			}
		} catch (err) {
			console.error("Failed to publish job:", err);
			setError("案件の公開に失敗しました");
		}
	};

	// 案件公開中止処理
	const handleUnpublishJob = async (jobId: string) => {
		if (!confirm("この案件の公開を中止してもよろしいですか？下書きに戻ります。")) return;

		try {
			const response = await jobClient.updateJob(
				create(UpdateJobRequestSchema, { id: jobId, status: "draft" })
			);
			if (response.job) {
				setJobs(prev => prev.map(j => j.id === response.job!.id ? response.job! : j));
			}
		} catch (err) {
			console.error("Failed to unpublish job:", err);
			setError("公開中止に失敗しました");
		}
	};

	// 保存処理（作成or更新を判定）
	const handleSaveJob = async () => {
		if (editingJob) {
			await handleUpdateJob();
		} else {
			await handleCreateJob();
		}
	};

	const closeModal = () => {
		setShowCreateForm(false);
		setFormData(initialFormData);
		setEditingJob(null);
		setError(null);
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
			<div className="mx-auto max-w-6xl">
				{/* ヘッダー */}
				<div className="mb-8 flex items-center justify-between">
					<div>
						<h1 className="text-3xl font-bold text-neutral-900 dark:text-neutral-100">
							案件管理
						</h1>
						<p className="mt-2 text-neutral-600 dark:text-neutral-400">
							求人案件の作成・編集・管理を行います
						</p>
					</div>
					<TouchOptimizedButton
						variant="primary"
						onClick={() => setShowCreateForm(true)}
					>
						新規案件を作成
					</TouchOptimizedButton>
				</div>

				{/* 案件一覧 */}
				{jobs.length === 0 ? (
					<div className="rounded-lg bg-white p-12 text-center shadow dark:bg-neutral-900">
						<div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-neutral-100 dark:bg-neutral-800">
							<svg className="h-8 w-8 text-neutral-400 dark:text-neutral-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
							</svg>
						</div>
						<h3 className="mb-2 text-lg font-semibold text-neutral-900 dark:text-neutral-100">案件がありません</h3>
						<p className="mb-4 text-neutral-600 dark:text-neutral-400">最初の求人案件を作成して、人材を募集しましょう</p>
						<TouchOptimizedButton variant="primary" onClick={() => setShowCreateForm(true)}>案件を作成する</TouchOptimizedButton>
					</div>
				) : (
					<div className="space-y-4">
						{jobs.map((job) => (
							<div key={job.id} className="rounded-lg bg-white p-6 shadow dark:bg-neutral-900">
								<div className="flex items-start justify-between">
									<div className="flex-1">
										<h3 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">{job.title}</h3>
										<div className="mt-3 flex flex-wrap gap-4 text-sm">
											{job.jobLocation && (
												<span className="text-neutral-600 dark:text-neutral-400">
													📍 {job.jobLocation}
												</span>
											)}
											{job.jobUnitPriceMin > 0 && job.jobUnitPriceMax > 0 && (
												<span className="text-neutral-600 dark:text-neutral-400">
													💰 {(job.jobUnitPriceMin / 10000).toLocaleString()}万円 〜 {(job.jobUnitPriceMax / 10000).toLocaleString()}万円
												</span>
											)}
											<span className="text-neutral-600 dark:text-neutral-400">
												{job.remoteAllowed ? "🏠 リモート可" : "🏢 出社"}
											</span>
											{(job.startDate || job.endDate) && (
												<span className="text-neutral-600 dark:text-neutral-400">
													📅 {job.startDate || "未定"} 〜 {job.endDate || "未定"}
												</span>
											)}
										</div>
									</div>
									<div className="ml-4 flex flex-col items-end gap-2">
										{(() => {
											const displayStatus = getJobDisplayStatus(job);
											return (
												<span className={`rounded-full px-3 py-1 text-xs font-medium ${
													displayStatus === "recruiting" ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
													: displayStatus === "before_recruiting" ? "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
													: displayStatus === "draft" ? "bg-neutral-100 text-neutral-800 dark:bg-neutral-700 dark:text-neutral-200"
													: displayStatus === "ended" ? "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200"
													: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
												}`}>
													{displayStatus === "recruiting" ? "募集中" : displayStatus === "before_recruiting" ? "募集前" : displayStatus === "draft" ? "下書き" : displayStatus === "ended" ? "募集終了" : "終了"}
												</span>
											);
										})()}
										<div className="flex gap-2">
											{job.status?.toLowerCase() === "draft" && (
												<TouchOptimizedButton variant="primary" size="sm" onClick={() => handlePublishJob(job.id)}>公開</TouchOptimizedButton>
											)}
											{(job.status?.toLowerCase() === "open" || job.status?.toLowerCase() === "published") && (getJobDisplayStatus(job) === "recruiting" || getJobDisplayStatus(job) === "before_recruiting") && (
												<TouchOptimizedButton variant="outline" size="sm" onClick={() => handleUnpublishJob(job.id)}>公開中止</TouchOptimizedButton>
											)}
											<TouchOptimizedButton variant="outline" size="sm" onClick={() => handleEditJob(job)}>編集</TouchOptimizedButton>
											<TouchOptimizedButton variant="outline" size="sm" onClick={() => handleDeleteJob(job.id)}>削除</TouchOptimizedButton>
										</div>
									</div>
								</div>
							</div>
						))}
					</div>
				)}

				{/* 案件作成/編集モーダル */}
				{showCreateForm && (
					<div className="fixed inset-0 z-50 overflow-y-auto bg-black/50">
						<div className="flex min-h-full items-start justify-center p-4 py-8">
						<div className="w-full max-w-4xl rounded-lg bg-white p-6 shadow-xl dark:bg-neutral-900">
							<div className="mb-6 flex items-center justify-between">
								<h2 className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100">
									{editingJob ? "案件編集" : "新規案件作成"}
								</h2>
								<button type="button" onClick={closeModal} className="text-neutral-500 hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-200" disabled={saving}>
									<svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
									</svg>
								</button>
							</div>

							{error && (
								<div className="mb-4 rounded-lg bg-red-50 p-4 text-red-800 dark:bg-red-900/20 dark:text-red-200">{error}</div>
							)}

							<div className="space-y-6">
								{/* 1. 案件タイトル */}
								<div>
									<label className="mb-2 block text-sm font-medium text-neutral-700 dark:text-neutral-300">
										案件タイトル <span className="text-red-500">*</span>
									</label>
									<input
										type="text"
										value={formData.title}
										onChange={(e) => setFormData({ ...formData, title: e.target.value })}
										className="w-full min-h-[44px] rounded-md border border-neutral-300 px-3 py-2 text-base dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100"
										placeholder="例: Reactエンジニア募集"
										disabled={saving}
									/>
								</div>

								{/* 2. 基本情報 */}
								<div className="rounded-lg border border-neutral-200 p-4 dark:border-neutral-700">
									<h3 className="mb-4 text-lg font-semibold text-neutral-900 dark:text-neutral-100">基本情報</h3>
									<div className="space-y-4">
										<div>
											<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">国籍</label>
											<select
												value={formData.nationalityId}
												onChange={(e) => setFormData({ ...formData, nationalityId: e.target.value })}
												className="mt-1 block w-full min-h-[44px] rounded-md border border-neutral-300 px-3 py-2 text-base dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100"
												disabled={saving}
											>
												<option value="">選択してください</option>
												{masterData.nationalities.map((nat) => (
													<option key={nat.id} value={nat.id}>{nat.nameJa}</option>
												))}
											</select>
										</div>
										<div>
											<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">在留資格</label>
											<select
												value={formData.workPermitId}
												onChange={(e) => setFormData({ ...formData, workPermitId: e.target.value })}
												className="mt-1 block w-full min-h-[44px] rounded-md border border-neutral-300 px-3 py-2 text-base dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100"
												disabled={saving}
											>
												<option value="">選択してください</option>
												{masterData.workPermits.map((permit) => (
													<option key={permit.id} value={permit.id}>{permit.nameJa}</option>
												))}
											</select>
										</div>
									</div>
								</div>

								{/* 3. 個人情報（勤務地・勤務条件） */}
								<div className="rounded-lg border border-neutral-200 p-4 dark:border-neutral-700">
									<h3 className="mb-4 text-lg font-semibold text-neutral-900 dark:text-neutral-100">勤務地・勤務条件</h3>
									<div className="space-y-4">
										<div>
											<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">最寄駅</label>
											<input
												type="text"
												value={formData.nearestStation}
												onChange={(e) => setFormData({ ...formData, nearestStation: e.target.value })}
												className="mt-1 block w-full min-h-[44px] rounded-md border border-neutral-300 px-3 py-2 text-base dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100"
												placeholder="例: 山手線渋谷駅"
												disabled={saving}
											/>
										</div>
										<div>
											<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">希望地域</label>
											<input
												type="text"
												value={formData.desiredRegion}
												onChange={(e) => setFormData({ ...formData, desiredRegion: e.target.value })}
												className="mt-1 block w-full min-h-[44px] rounded-md border border-neutral-300 px-3 py-2 text-base dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100"
												placeholder="例: 東京都23区内"
												disabled={saving}
											/>
										</div>
										<div className="space-y-3">
											<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">勤務条件</label>
											<div className="space-y-2">
												<label className="flex items-center space-x-2">
													<input
														type="checkbox"
														checked={formData.canWorkWeekends}
														onChange={(e) => setFormData({ ...formData, canWorkWeekends: e.target.checked })}
														className="h-5 w-5 rounded border-neutral-300 text-brand-600 focus:ring-brand-500 dark:border-neutral-600 dark:bg-neutral-800"
														disabled={saving}
													/>
													<span className="text-neutral-700 dark:text-neutral-300">休日作業可</span>
												</label>
												<label className="flex items-center space-x-2">
													<input
														type="checkbox"
														checked={formData.canWorkOvertime}
														onChange={(e) => setFormData({ ...formData, canWorkOvertime: e.target.checked })}
														className="h-5 w-5 rounded border-neutral-300 text-brand-600 focus:ring-brand-500 dark:border-neutral-600 dark:bg-neutral-800"
														disabled={saving}
													/>
													<span className="text-neutral-700 dark:text-neutral-300">残業可</span>
												</label>
												<label className="flex items-center space-x-2">
													<input
														type="checkbox"
														checked={formData.canTravel}
														onChange={(e) => setFormData({ ...formData, canTravel: e.target.checked })}
														className="h-5 w-5 rounded border-neutral-300 text-brand-600 focus:ring-brand-500 dark:border-neutral-600 dark:bg-neutral-800"
														disabled={saving}
													/>
													<span className="text-neutral-700 dark:text-neutral-300">出張可</span>
												</label>
											</div>
										</div>
									</div>
								</div>

								{/* 4. 希望条件 */}
								<div className="rounded-lg border border-neutral-200 p-4 dark:border-neutral-700">
									<h3 className="mb-4 text-lg font-semibold text-neutral-900 dark:text-neutral-100">希望条件</h3>
									<div className="space-y-4">
										<div className="grid grid-cols-2 gap-4">
											<div>
												<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">
													希望単価（最小）
												</label>
												<div className="relative mt-1">
													<input
														type="number"
														value={formData.jobUnitPriceMin}
														onChange={(e) => setFormData({ ...formData, jobUnitPriceMin: e.target.value })}
														className="block w-full min-h-[44px] rounded-md border border-neutral-300 px-3 py-2 pr-12 text-base dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100"
														min="0"
														step="0.1"
														placeholder="例: 30"
														disabled={saving}
													/>
													<span className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-500 dark:text-neutral-400 pointer-events-none">万円</span>
												</div>
												<p className="mt-1 text-xs text-neutral-500 dark:text-neutral-400">月額</p>
											</div>
											<div>
												<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">
													希望単価（最大）
												</label>
												<div className="relative mt-1">
													<input
														type="number"
														value={formData.jobUnitPriceMax}
														onChange={(e) => setFormData({ ...formData, jobUnitPriceMax: e.target.value })}
														className="block w-full min-h-[44px] rounded-md border border-neutral-300 px-3 py-2 pr-12 text-base dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100"
														min="0"
														step="0.1"
														placeholder="例: 50"
														disabled={saving}
													/>
													<span className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-500 dark:text-neutral-400 pointer-events-none">万円</span>
												</div>
												<p className="mt-1 text-xs text-neutral-500 dark:text-neutral-400">月額</p>
											</div>
										</div>
										<div>
											<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">週あたり稼働日数</label>
											<select
												value={formData.desiredWorkdaysPerWeek}
												onChange={(e) => setFormData({ ...formData, desiredWorkdaysPerWeek: e.target.value })}
												className="mt-1 block w-full min-h-[44px] rounded-md border border-neutral-300 px-3 py-2 text-base dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100"
												disabled={saving}
											>
												<option value="1">1日</option>
												<option value="2">2日</option>
												<option value="3">3日</option>
												<option value="4">4日</option>
												<option value="5">5日</option>
											</select>
										</div>
										<div>
											<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">リモート希望</label>
											<select
												value={formData.remotePreference}
												onChange={(e) => setFormData({ ...formData, remotePreference: e.target.value as "full" | "hybrid" | "none" })}
												className="mt-1 block w-full min-h-[44px] rounded-md border border-neutral-300 px-3 py-2 text-base dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100"
												disabled={saving}
											>
												<option value="full">フルリモート</option>
												<option value="hybrid">ハイブリッド</option>
												<option value="none">リモート不可</option>
											</select>
										</div>
									</div>
								</div>

								{/* 5. 募集期間 */}
								<div className="rounded-lg border border-neutral-200 p-4 dark:border-neutral-700">
									<h3 className="mb-4 text-lg font-semibold text-neutral-900 dark:text-neutral-100">募集期間</h3>
									<div className="grid grid-cols-2 gap-4">
										<div>
											<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">募集開始日</label>
											<div className="relative mt-1">
												<input
													id="jobStartDate"
													type="date"
													value={formData.startDate}
													onChange={(e) => setFormData({ ...formData, startDate: e.target.value })}
													className="block w-full min-h-[44px] rounded-md border border-neutral-300 px-3 py-2 text-base dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100"
													disabled={saving}
												/>
												<button
													type="button"
													onClick={() => { (document.getElementById("jobStartDate") as HTMLInputElement)?.showPicker?.(); }}
													className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-500 hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-200"
													aria-label="カレンダーを開く"
												>
													<svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
														<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
													</svg>
												</button>
											</div>
										</div>
										<div>
											<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">募集終了日</label>
											<div className="relative mt-1">
												<input
													id="jobEndDate"
													type="date"
													value={formData.endDate}
													onChange={(e) => setFormData({ ...formData, endDate: e.target.value })}
													min={formData.startDate || undefined}
													className="block w-full min-h-[44px] rounded-md border border-neutral-300 px-3 py-2 text-base dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100"
													disabled={saving}
												/>
												<button
													type="button"
													onClick={() => { (document.getElementById("jobEndDate") as HTMLInputElement)?.showPicker?.(); }}
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

								{/* 6. 資格・専門分野・言語 */}
								<div className="rounded-lg border border-neutral-200 p-4 dark:border-neutral-700">
									<h3 className="mb-4 text-lg font-semibold text-neutral-900 dark:text-neutral-100">資格・専門分野・言語</h3>
									<div className="space-y-4">
										<MultiSelect
											label="資格"
											options={masterData.certifications.map((c) => ({ id: c.id, name: c.nameJa }))}
											selectedIds={formData.certificationIds}
											onChange={(ids) => setFormData({ ...formData, certificationIds: ids })}
										/>
										<MultiSelect
											label="専門分野"
											options={masterData.specializations.map((s) => ({ id: s.id, name: s.nameJa }))}
											selectedIds={formData.specializationIds}
											onChange={(ids) => setFormData({ ...formData, specializationIds: ids })}
										/>
										<MultiSelect
											label="言語"
											options={masterData.languages.map((l) => ({ id: l.id, name: l.nameJa }))}
											selectedIds={formData.languageIds}
											onChange={(ids) => setFormData({ ...formData, languageIds: ids })}
										/>
									</div>
								</div>

								{/* 7. 業務スキル */}
								<div className="rounded-lg border border-neutral-200 p-4 dark:border-neutral-700">
									<h3 className="mb-4 text-lg font-semibold text-neutral-900 dark:text-neutral-100">業務スキル</h3>
									<div className="mb-4">
										<p className="mb-2 text-sm text-neutral-600 dark:text-neutral-400">各スキルのレベルを選択してください</p>
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
										<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">その他</label>
										<textarea
											value={formData.otherSkills}
											onChange={(e) => setFormData({ ...formData, otherSkills: e.target.value })}
											className="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2 text-base dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100"
											rows={4}
											placeholder="上記以外のスキルや補足事項があればご記入ください"
											disabled={saving}
										/>
									</div>
								</div>
							</div>

							<div className="mt-6 flex justify-end gap-3">
								<TouchOptimizedButton variant="outline" onClick={closeModal} disabled={saving}>
									キャンセル
								</TouchOptimizedButton>
								<TouchOptimizedButton
									variant="primary"
									onClick={handleSaveJob}
									disabled={saving || !formData.title}
								>
									{saving ? (editingJob ? "更新中..." : "作成中...") : (editingJob ? "案件を更新" : "案件を作成")}
								</TouchOptimizedButton>
							</div>
						</div>
						</div>
					</div>
				)}
			</div>
		</div>
	);
}
