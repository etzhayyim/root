"use client";

/**
 * @etzhayyim/etzhayyim-hrse#ExperienceSectionConnect
 * 職歴管理セクション（Connect-Web版）
 */

import { useState, useCallback, useEffect } from "react";
import { useJobSeekerServiceClient, type Experience } from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import {
	ListExperiencesRequestSchema,
	CreateExperienceRequestSchema,
	UpdateExperienceRequestSchema,
	DeleteExperienceRequestSchema,
} from "@/gen/proto/hrse/v1/job_seeker_pb";
import { TouchOptimizedButton } from "@/components/TouchOptimizedButton";

interface ExperienceSectionProps {
	jobSeekerId: string;
}

export function ExperienceSection({ jobSeekerId }: ExperienceSectionProps) {
	const [isEditing, setIsEditing] = useState(false);
	const [editingId, setEditingId] = useState<string | null>(null);
	const [formData, setFormData] = useState({
		companyName: "",
		title: "",
		location: "",
		employmentType: "",
		startDate: "",
		endDate: "",
		description: "",
	});
	const [experiences, setExperiences] = useState<Experience[]>([]);
	const [loading, setLoading] = useState(false);

	const jobSeekerClient = useJobSeekerServiceClient();

	const fetchExperiences = useCallback(async () => {
		if (!jobSeekerId) return;

		setLoading(true);
		try {
			const res = await jobSeekerClient.listExperiences(
				create(ListExperiencesRequestSchema, { jobSeekerId })
			);
			setExperiences(res.experiences || []);
		} catch (error) {
			console.error("Failed to fetch experiences:", error);
		} finally {
			setLoading(false);
		}
	}, [jobSeekerId, jobSeekerClient]);

	useEffect(() => {
		fetchExperiences();
	}, [fetchExperiences]);

	const handleEdit = (experience: Experience) => {
		setEditingId(experience.id);
		setFormData({
			companyName: experience.companyName,
			title: experience.title,
			location: experience.location || "",
			employmentType: experience.employmentType || "",
			startDate: experience.startDate,
			endDate: experience.endDate || "",
			description: experience.description || "",
		});
		setIsEditing(true);
	};

	const handleCancel = () => {
		setIsEditing(false);
		setEditingId(null);
		setFormData({
			companyName: "",
			title: "",
			location: "",
			employmentType: "",
			startDate: "",
			endDate: "",
			description: "",
		});
	};

	const handleSubmit = async (e: React.FormEvent) => {
		e.preventDefault();
		setLoading(true);

		try {
			if (editingId) {
				await jobSeekerClient.updateExperience(
					create(UpdateExperienceRequestSchema, {
						id: editingId,
						companyName: formData.companyName,
						title: formData.title,
						location: formData.location || undefined,
						employmentType: formData.employmentType || undefined,
						startDate: formData.startDate,
						endDate: formData.endDate || undefined,
						description: formData.description || undefined,
					})
				);
			} else {
				await jobSeekerClient.createExperience(
					create(CreateExperienceRequestSchema, {
						jobSeekerId,
						companyName: formData.companyName,
						title: formData.title,
						location: formData.location || undefined,
						employmentType: formData.employmentType || undefined,
						startDate: formData.startDate,
						endDate: formData.endDate || undefined,
						description: formData.description || undefined,
					})
				);
			}

			await fetchExperiences();
			handleCancel();
		} catch (error) {
			console.error("Failed to save experience:", error);
			alert(error instanceof Error ? error.message : "職歴の保存に失敗しました");
		} finally {
			setLoading(false);
		}
	};

	const handleDelete = async (id: string) => {
		if (!confirm("この職歴を削除しますか？")) return;

		setLoading(true);
		try {
			await jobSeekerClient.deleteExperience(
				create(DeleteExperienceRequestSchema, { id })
			);
			await fetchExperiences();
		} catch (error) {
			console.error("Failed to delete experience:", error);
			alert(error instanceof Error ? error.message : "職歴の削除に失敗しました");
		} finally {
			setLoading(false);
		}
	};

	return (
		<div className="rounded-lg bg-white p-6 shadow-sm border border-neutral-200 dark:bg-neutral-900 dark:border-neutral-800">
			<div className="mb-6 flex items-center justify-between">
				<h2 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">
					職歴
				</h2>
				{!isEditing && (
					<TouchOptimizedButton
						variant="primary"
						size="sm"
						onClick={() => setIsEditing(true)}
					>
						追加
					</TouchOptimizedButton>
				)}
			</div>

			{isEditing && (
				<form onSubmit={handleSubmit} className="mb-6 space-y-4 rounded-lg border border-neutral-200 bg-neutral-50 p-4 dark:border-neutral-700 dark:bg-neutral-800">
					<div>
						<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
							会社名 <span className="text-red-500">*</span>
						</label>
						<input
							type="text"
							value={formData.companyName}
							onChange={(e) => setFormData({ ...formData, companyName: e.target.value })}
							className="block w-full min-h-[44px] rounded-lg border border-neutral-300 bg-white px-4 py-2.5 text-base text-neutral-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:bg-neutral-700 dark:border-neutral-600 dark:text-neutral-100"
							required
						/>
					</div>

					<div>
						<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
							役職 <span className="text-red-500">*</span>
						</label>
						<input
							type="text"
							value={formData.title}
							onChange={(e) => setFormData({ ...formData, title: e.target.value })}
							className="block w-full min-h-[44px] rounded-lg border border-neutral-300 bg-white px-4 py-2.5 text-base text-neutral-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:bg-neutral-700 dark:border-neutral-600 dark:text-neutral-100"
							required
						/>
					</div>

					<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
						<div>
							<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
								勤務地
							</label>
							<input
								type="text"
								value={formData.location}
								onChange={(e) => setFormData({ ...formData, location: e.target.value })}
								className="block w-full min-h-[44px] rounded-lg border border-neutral-300 bg-white px-4 py-2.5 text-base text-neutral-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:bg-neutral-700 dark:border-neutral-600 dark:text-neutral-100"
							/>
						</div>

						<div>
							<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
								雇用形態
							</label>
							<select
								value={formData.employmentType}
								onChange={(e) => setFormData({ ...formData, employmentType: e.target.value })}
								className="block w-full min-h-[44px] rounded-lg border border-neutral-300 bg-white px-4 py-2.5 text-base text-neutral-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:bg-neutral-700 dark:border-neutral-600 dark:text-neutral-100"
							>
								<option value="">選択してください</option>
								<option value="full_time">正社員</option>
								<option value="contract">契約社員</option>
								<option value="part_time">パートタイム</option>
								<option value="freelance">フリーランス</option>
							</select>
						</div>
					</div>

					<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
						<div>
							<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
								開始日 <span className="text-red-500">*</span>
							</label>
							<input
								type="date"
								value={formData.startDate}
								onChange={(e) => setFormData({ ...formData, startDate: e.target.value })}
								className="block w-full min-h-[44px] rounded-lg border border-neutral-300 bg-white px-4 py-2.5 text-base text-neutral-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:bg-neutral-700 dark:border-neutral-600 dark:text-neutral-100"
								required
							/>
						</div>

						<div>
							<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
								終了日
							</label>
							<input
								type="date"
								value={formData.endDate}
								onChange={(e) => setFormData({ ...formData, endDate: e.target.value })}
								className="block w-full min-h-[44px] rounded-lg border border-neutral-300 bg-white px-4 py-2.5 text-base text-neutral-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:bg-neutral-700 dark:border-neutral-600 dark:text-neutral-100"
							/>
						</div>
					</div>

					<div>
						<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
							説明
						</label>
						<textarea
							value={formData.description}
							onChange={(e) => setFormData({ ...formData, description: e.target.value })}
							rows={4}
							className="block w-full rounded-lg border border-neutral-300 bg-white px-4 py-2.5 text-base text-neutral-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:bg-neutral-700 dark:border-neutral-600 dark:text-neutral-100"
						/>
					</div>

					<div className="flex justify-end gap-2">
						<TouchOptimizedButton
							type="button"
							variant="secondary"
							size="sm"
							onClick={handleCancel}
							disabled={loading}
						>
							キャンセル
						</TouchOptimizedButton>
						<TouchOptimizedButton
							type="submit"
							variant="primary"
							size="sm"
							disabled={loading}
						>
							{loading ? "保存中..." : editingId ? "更新" : "作成"}
						</TouchOptimizedButton>
					</div>
				</form>
			)}

			{loading && experiences.length === 0 ? (
				<div className="text-center py-8 text-neutral-600 dark:text-neutral-400">
					読み込み中...
				</div>
			) : experiences.length === 0 ? (
				<div className="text-center py-8 text-neutral-600 dark:text-neutral-400">
					職歴が登録されていません
				</div>
			) : (
				<div className="space-y-4">
					{experiences.map((experience) => (
						<div
							key={experience.id}
							className="rounded-lg border border-neutral-200 bg-neutral-50 p-4 dark:border-neutral-700 dark:bg-neutral-800"
						>
							<div className="flex items-start justify-between">
								<div className="flex-1">
									<h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
										{experience.title}
									</h3>
									<p className="mt-1 text-sm text-neutral-700 dark:text-neutral-300">
										{experience.companyName}
									</p>
									{experience.location && (
										<p className="mt-1 text-sm text-neutral-700 dark:text-neutral-300">
											勤務地: {experience.location}
										</p>
									)}
									{experience.employmentType && (
										<p className="mt-1 text-sm text-neutral-700 dark:text-neutral-300">
											雇用形態: {experience.employmentType}
										</p>
									)}
									<p className="mt-1 text-sm text-neutral-700 dark:text-neutral-300">
										{experience.startDate} 〜 {experience.endDate || "現在"}
									</p>
									{experience.description && (
										<p className="mt-2 text-sm text-neutral-600 dark:text-neutral-400">
											{experience.description}
										</p>
									)}
								</div>
								<div className="ml-4 flex gap-2">
									<TouchOptimizedButton
										variant="secondary"
										size="sm"
										onClick={() => handleEdit(experience)}
										disabled={loading}
									>
										編集
									</TouchOptimizedButton>
									<TouchOptimizedButton
										variant="secondary"
										size="sm"
										onClick={() => handleDelete(experience.id)}
										disabled={loading}
										className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
									>
										削除
									</TouchOptimizedButton>
								</div>
							</div>
						</div>
					))}
				</div>
			)}
		</div>
	);
}



