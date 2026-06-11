"use client";

/**
 * @etzhayyim/etzhayyim-hrse#EducationSectionConnect
 * 学歴管理セクション（Connect-Web版）
 */

import { useState, useCallback, useEffect } from "react";
import { useJobSeekerServiceClient, type Education } from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import {
	ListEducationsRequestSchema,
	CreateEducationRequestSchema,
	UpdateEducationRequestSchema,
	DeleteEducationRequestSchema,
} from "@/gen/proto/hrse/v1/job_seeker_pb";
import { TouchOptimizedButton } from "@/components/TouchOptimizedButton";

interface EducationSectionProps {
	jobSeekerId: string;
}

export function EducationSection({ jobSeekerId }: EducationSectionProps) {
	const [isEditing, setIsEditing] = useState(false);
	const [editingId, setEditingId] = useState<string | null>(null);
	const [formData, setFormData] = useState({
		schoolName: "",
		degree: "",
		fieldOfStudy: "",
		startDate: "",
		endDate: "",
		activities: "",
		description: "",
	});
	const [educations, setEducations] = useState<Education[]>([]);
	const [loading, setLoading] = useState(false);

	const jobSeekerClient = useJobSeekerServiceClient();

	const fetchEducations = useCallback(async () => {
		if (!jobSeekerId) return;

		setLoading(true);
		try {
			const res = await jobSeekerClient.listEducations(
				create(ListEducationsRequestSchema, { jobSeekerId })
			);
			setEducations(res.educations || []);
		} catch (error) {
			console.error("Failed to fetch educations:", error);
		} finally {
			setLoading(false);
		}
	}, [jobSeekerId, jobSeekerClient]);

	useEffect(() => {
		fetchEducations();
	}, [fetchEducations]);

	const handleEdit = (education: Education) => {
		setEditingId(education.id);
		setFormData({
			schoolName: education.schoolName,
			degree: education.degree || "",
			fieldOfStudy: education.fieldOfStudy || "",
			startDate: education.startDate || "",
			endDate: education.endDate || "",
			activities: education.activities || "",
			description: education.description || "",
		});
		setIsEditing(true);
	};

	const handleCancel = () => {
		setIsEditing(false);
		setEditingId(null);
		setFormData({
			schoolName: "",
			degree: "",
			fieldOfStudy: "",
			startDate: "",
			endDate: "",
			activities: "",
			description: "",
		});
	};

	const handleSubmit = async (e: React.FormEvent) => {
		e.preventDefault();
		setLoading(true);

		try {
			if (editingId) {
				await jobSeekerClient.updateEducation(
					create(UpdateEducationRequestSchema, {
						id: editingId,
						schoolName: formData.schoolName,
						degree: formData.degree || undefined,
						fieldOfStudy: formData.fieldOfStudy || undefined,
						startDate: formData.startDate || undefined,
						endDate: formData.endDate || undefined,
						activities: formData.activities || undefined,
						description: formData.description || undefined,
					})
				);
			} else {
				await jobSeekerClient.createEducation(
					create(CreateEducationRequestSchema, {
						jobSeekerId,
						schoolName: formData.schoolName,
						degree: formData.degree || undefined,
						fieldOfStudy: formData.fieldOfStudy || undefined,
						startDate: formData.startDate || undefined,
						endDate: formData.endDate || undefined,
						activities: formData.activities || undefined,
						description: formData.description || undefined,
					})
				);
			}

			await fetchEducations();
			handleCancel();
		} catch (error) {
			console.error("Failed to save education:", error);
			alert(error instanceof Error ? error.message : "学歴の保存に失敗しました");
		} finally {
			setLoading(false);
		}
	};

	const handleDelete = async (id: string) => {
		if (!confirm("この学歴を削除しますか？")) return;

		setLoading(true);
		try {
			await jobSeekerClient.deleteEducation(
				create(DeleteEducationRequestSchema, { id })
			);
			await fetchEducations();
		} catch (error) {
			console.error("Failed to delete education:", error);
			alert(error instanceof Error ? error.message : "学歴の削除に失敗しました");
		} finally {
			setLoading(false);
		}
	};

	return (
		<div className="rounded-lg bg-white p-6 shadow-sm border border-neutral-200 dark:bg-neutral-900 dark:border-neutral-800">
			<div className="mb-6 flex items-center justify-between">
				<h2 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">
					学歴
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
							学校名 <span className="text-red-500">*</span>
						</label>
						<input
							type="text"
							value={formData.schoolName}
							onChange={(e) => setFormData({ ...formData, schoolName: e.target.value })}
							className="block w-full min-h-[44px] rounded-lg border border-neutral-300 bg-white px-4 py-2.5 text-base text-neutral-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:bg-neutral-700 dark:border-neutral-600 dark:text-neutral-100"
							required
						/>
					</div>

					<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
						<div>
							<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
								学位
							</label>
							<input
								type="text"
								value={formData.degree}
								onChange={(e) => setFormData({ ...formData, degree: e.target.value })}
								className="block w-full min-h-[44px] rounded-lg border border-neutral-300 bg-white px-4 py-2.5 text-base text-neutral-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:bg-neutral-700 dark:border-neutral-600 dark:text-neutral-100"
							/>
						</div>

						<div>
							<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
								専攻分野
							</label>
							<input
								type="text"
								value={formData.fieldOfStudy}
								onChange={(e) => setFormData({ ...formData, fieldOfStudy: e.target.value })}
								className="block w-full min-h-[44px] rounded-lg border border-neutral-300 bg-white px-4 py-2.5 text-base text-neutral-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:bg-neutral-700 dark:border-neutral-600 dark:text-neutral-100"
							/>
						</div>
					</div>

					<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
						<div>
							<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
								開始日
							</label>
							<input
								type="date"
								value={formData.startDate}
								onChange={(e) => setFormData({ ...formData, startDate: e.target.value })}
								className="block w-full min-h-[44px] rounded-lg border border-neutral-300 bg-white px-4 py-2.5 text-base text-neutral-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:bg-neutral-700 dark:border-neutral-600 dark:text-neutral-100"
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
							活動・実績
						</label>
						<textarea
							value={formData.activities}
							onChange={(e) => setFormData({ ...formData, activities: e.target.value })}
							rows={3}
							className="block w-full rounded-lg border border-neutral-300 bg-white px-4 py-2.5 text-base text-neutral-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:bg-neutral-700 dark:border-neutral-600 dark:text-neutral-100"
						/>
					</div>

					<div>
						<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
							説明
						</label>
						<textarea
							value={formData.description}
							onChange={(e) => setFormData({ ...formData, description: e.target.value })}
							rows={3}
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

			{loading && educations.length === 0 ? (
				<div className="text-center py-8 text-neutral-600 dark:text-neutral-400">
					読み込み中...
				</div>
			) : educations.length === 0 ? (
				<div className="text-center py-8 text-neutral-600 dark:text-neutral-400">
					学歴が登録されていません
				</div>
			) : (
				<div className="space-y-4">
					{educations.map((education) => (
						<div
							key={education.id}
							className="rounded-lg border border-neutral-200 bg-neutral-50 p-4 dark:border-neutral-700 dark:bg-neutral-800"
						>
							<div className="flex items-start justify-between">
								<div className="flex-1">
									<h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
										{education.schoolName}
									</h3>
									{education.degree && (
										<p className="mt-1 text-sm text-neutral-700 dark:text-neutral-300">
											学位: {education.degree}
										</p>
									)}
									{education.fieldOfStudy && (
										<p className="mt-1 text-sm text-neutral-700 dark:text-neutral-300">
											専攻: {education.fieldOfStudy}
										</p>
									)}
									{(education.startDate || education.endDate) && (
										<p className="mt-1 text-sm text-neutral-700 dark:text-neutral-300">
											{education.startDate || "?"} 〜 {education.endDate || "現在"}
										</p>
									)}
									{education.activities && (
										<p className="mt-2 text-sm text-neutral-600 dark:text-neutral-400">
											{education.activities}
										</p>
									)}
									{education.description && (
										<p className="mt-2 text-sm text-neutral-600 dark:text-neutral-400">
											{education.description}
										</p>
									)}
								</div>
								<div className="ml-4 flex gap-2">
									<TouchOptimizedButton
										variant="secondary"
										size="sm"
										onClick={() => handleEdit(education)}
										disabled={loading}
									>
										編集
									</TouchOptimizedButton>
									<TouchOptimizedButton
										variant="secondary"
										size="sm"
										onClick={() => handleDelete(education.id)}
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



