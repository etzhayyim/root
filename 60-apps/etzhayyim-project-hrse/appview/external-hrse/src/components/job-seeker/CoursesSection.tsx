"use client";

/**
 * @etzhayyim/etzhayyim-hrse#CoursesSectionConnect
 * コース修了管理セクション（Connect-Web版）
 */

import { useState, useCallback, useEffect } from "react";
import { useJobSeekerServiceClient, useMasterDataServiceClient, type CourseCompletion } from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import {
	ListCourseCompletionsRequestSchema,
	CreateCourseCompletionRequestSchema,
	UpdateCourseCompletionRequestSchema,
	DeleteCourseCompletionRequestSchema,
} from "@/gen/proto/hrse/v1/job_seeker_pb";
import {
	ListCoursesRequestSchema,
} from "@/gen/proto/hrse/v1/job_seeker_pb";
import { TouchOptimizedButton } from "@/components/TouchOptimizedButton";

interface CoursesSectionProps {
	jobSeekerId: string;
}

export function CoursesSection({ jobSeekerId }: CoursesSectionProps) {
	const [isEditing, setIsEditing] = useState(false);
	const [editingId, setEditingId] = useState<string | null>(null);
	const [formData, setFormData] = useState({
		courseId: "",
		completionDate: "",
		certificateUrl: "",
		credentialId: "",
	});
	const [courseCompletions, setCourseCompletions] = useState<CourseCompletion[]>([]);
	const [courses, setCourses] = useState<Array<{ id: string; name: string; provider: string }>>([]);
	const [loading, setLoading] = useState(false);

	const jobSeekerClient = useJobSeekerServiceClient();
	const masterDataClient = useMasterDataServiceClient();

	const fetchCourses = useCallback(async () => {
		try {
			const res = await masterDataClient.listCourses(
				create(ListCoursesRequestSchema, {})
			);
			setCourses((res.courses || []).map((c) => ({ id: c.id, name: c.name, provider: c.provider })));
		} catch (error) {
			console.error("Failed to fetch courses:", error);
		}
	}, [masterDataClient]);

	const fetchCourseCompletions = useCallback(async () => {
		if (!jobSeekerId) return;

		setLoading(true);
		try {
			const res = await jobSeekerClient.listCourseCompletions(
				create(ListCourseCompletionsRequestSchema, { jobSeekerId })
			);
			setCourseCompletions(res.courseCompletions || []);
		} catch (error) {
			console.error("Failed to fetch course completions:", error);
		} finally {
			setLoading(false);
		}
	}, [jobSeekerId, jobSeekerClient]);

	useEffect(() => {
		fetchCourses();
	}, [fetchCourses]);

	useEffect(() => {
		fetchCourseCompletions();
	}, [fetchCourseCompletions]);

	const handleEdit = (completion: CourseCompletion) => {
		setEditingId(completion.id);
		setFormData({
			courseId: completion.courseId,
			completionDate: completion.completionDate,
			certificateUrl: completion.certificateUrl || "",
			credentialId: completion.credentialId || "",
		});
		setIsEditing(true);
	};

	const handleCancel = () => {
		setIsEditing(false);
		setEditingId(null);
		setFormData({
			courseId: "",
			completionDate: "",
			certificateUrl: "",
			credentialId: "",
		});
	};

	const handleSubmit = async (e: React.FormEvent) => {
		e.preventDefault();
		setLoading(true);

		try {
			if (editingId) {
				await jobSeekerClient.updateCourseCompletion(
					create(UpdateCourseCompletionRequestSchema, {
						id: editingId,
						completionDate: formData.completionDate,
						certificateUrl: formData.certificateUrl || undefined,
						credentialId: formData.credentialId || undefined,
					})
				);
			} else {
				await jobSeekerClient.createCourseCompletion(
					create(CreateCourseCompletionRequestSchema, {
						jobSeekerId,
						courseId: formData.courseId,
						completionDate: formData.completionDate,
						certificateUrl: formData.certificateUrl || undefined,
						credentialId: formData.credentialId || undefined,
					})
				);
			}

			await fetchCourseCompletions();
			handleCancel();
		} catch (error) {
			console.error("Failed to save course completion:", error);
			alert(error instanceof Error ? error.message : "コース修了の保存に失敗しました");
		} finally {
			setLoading(false);
		}
	};

	const handleDelete = async (id: string) => {
		if (!confirm("このコース修了を削除しますか？")) return;

		setLoading(true);
		try {
			await jobSeekerClient.deleteCourseCompletion(
				create(DeleteCourseCompletionRequestSchema, { id })
			);
			await fetchCourseCompletions();
		} catch (error) {
			console.error("Failed to delete course completion:", error);
			alert(error instanceof Error ? error.message : "コース修了の削除に失敗しました");
		} finally {
			setLoading(false);
		}
	};

	return (
		<div className="rounded-lg bg-white p-6 shadow-sm border border-neutral-200 dark:bg-neutral-900 dark:border-neutral-800">
			<div className="mb-6 flex items-center justify-between">
				<h2 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">
					コース修了
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
					{!editingId && (
						<div>
							<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
								コース <span className="text-red-500">*</span>
							</label>
							<select
								value={formData.courseId}
								onChange={(e) => setFormData({ ...formData, courseId: e.target.value })}
								className="block w-full min-h-[44px] rounded-lg border border-neutral-300 bg-white px-4 py-2.5 text-base text-neutral-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:bg-neutral-700 dark:border-neutral-600 dark:text-neutral-100"
								required={!editingId}
								disabled={!!editingId}
							>
								<option value="">選択してください</option>
								{courses.map((course) => (
									<option key={course.id} value={course.id}>
										{course.name} ({course.provider})
									</option>
								))}
							</select>
						</div>
					)}

					<div>
						<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
							修了日 <span className="text-red-500">*</span>
						</label>
						<input
							type="date"
							value={formData.completionDate}
							onChange={(e) => setFormData({ ...formData, completionDate: e.target.value })}
							className="block w-full min-h-[44px] rounded-lg border border-neutral-300 bg-white px-4 py-2.5 text-base text-neutral-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:bg-neutral-700 dark:border-neutral-600 dark:text-neutral-100"
							required
						/>
					</div>

					<div>
						<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
							修了証明書URL
						</label>
						<input
							type="url"
							value={formData.certificateUrl}
							onChange={(e) => setFormData({ ...formData, certificateUrl: e.target.value })}
							className="block w-full min-h-[44px] rounded-lg border border-neutral-300 bg-white px-4 py-2.5 text-base text-neutral-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:bg-neutral-700 dark:border-neutral-600 dark:text-neutral-100"
							placeholder="https://..."
						/>
					</div>

					<div>
						<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
							資格ID
						</label>
						<input
							type="text"
							value={formData.credentialId}
							onChange={(e) => setFormData({ ...formData, credentialId: e.target.value })}
							className="block w-full min-h-[44px] rounded-lg border border-neutral-300 bg-white px-4 py-2.5 text-base text-neutral-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:bg-neutral-700 dark:border-neutral-600 dark:text-neutral-100"
							placeholder="例: ABC123456"
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

			{loading && courseCompletions.length === 0 ? (
				<div className="text-center py-8 text-neutral-600 dark:text-neutral-400">
					読み込み中...
				</div>
			) : courseCompletions.length === 0 ? (
				<div className="text-center py-8 text-neutral-600 dark:text-neutral-400">
					コース修了が登録されていません
				</div>
			) : (
				<div className="space-y-4">
					{courseCompletions.map((completion) => (
						<div
							key={completion.id}
							className="rounded-lg border border-neutral-200 bg-neutral-50 p-4 dark:border-neutral-700 dark:bg-neutral-800"
						>
							<div className="flex items-start justify-between">
								<div className="flex-1">
									<h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
										{completion.course?.name || "コース名不明"}
									</h3>
									{completion.course?.provider && (
										<p className="mt-1 text-sm text-neutral-700 dark:text-neutral-300">
											提供元: {completion.course.provider}
										</p>
									)}
									<p className="mt-1 text-sm text-neutral-700 dark:text-neutral-300">
										修了日: {completion.completionDate}
									</p>
									{completion.credentialId && (
										<p className="mt-1 text-sm text-neutral-700 dark:text-neutral-300">
											資格ID: {completion.credentialId}
										</p>
									)}
									{completion.certificateUrl && (
										<a
											href={completion.certificateUrl}
											target="_blank"
											rel="noopener noreferrer"
											className="mt-2 inline-block text-sm text-brand-600 hover:text-brand-700 dark:text-brand-400 dark:hover:text-brand-300"
										>
											修了証明書を確認
										</a>
									)}
								</div>
								<div className="ml-4 flex gap-2">
									<TouchOptimizedButton
										variant="secondary"
										size="sm"
										onClick={() => handleEdit(completion)}
										disabled={loading}
									>
										編集
									</TouchOptimizedButton>
									<TouchOptimizedButton
										variant="secondary"
										size="sm"
										onClick={() => handleDelete(completion.id)}
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



