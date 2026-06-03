"use client";

/**
 * @etzhayyim/etzhayyim-hrse#LicensesSectionConnect
 * ライセンス管理セクション（Connect-Web版）
 */

import { useState, useCallback, useEffect } from "react";
import { useJobSeekerServiceClient, type License } from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import {
	ListLicensesRequestSchema,
	CreateLicenseRequestSchema,
	UpdateLicenseRequestSchema,
	DeleteLicenseRequestSchema,
} from "@/gen/proto/hrse/v1/job_seeker_pb";
import { TouchOptimizedButton } from "@/components/TouchOptimizedButton";

interface LicensesSectionProps {
	jobSeekerId: string;
}

export function LicensesSection({ jobSeekerId }: LicensesSectionProps) {
	const [isEditing, setIsEditing] = useState(false);
	const [editingId, setEditingId] = useState<string | null>(null);
	const [formData, setFormData] = useState({
		name: "",
		issuingOrganization: "",
		licenseNumber: "",
		issueDate: "",
		expirationDate: "",
		credentialUrl: "",
	});
	const [licenses, setLicenses] = useState<License[]>([]);
	const [loading, setLoading] = useState(false);

	const jobSeekerClient = useJobSeekerServiceClient();

	const fetchLicenses = useCallback(async () => {
		if (!jobSeekerId) return;

		setLoading(true);
		try {
			const res = await jobSeekerClient.listLicenses(
				create(ListLicensesRequestSchema, { jobSeekerId })
			);
			setLicenses(res.licenses || []);
		} catch (error) {
			console.error("Failed to fetch licenses:", error);
		} finally {
			setLoading(false);
		}
	}, [jobSeekerId, jobSeekerClient]);

	useEffect(() => {
		fetchLicenses();
	}, [fetchLicenses]);

	const handleEdit = (license: License) => {
		setEditingId(license.id);
		setFormData({
			name: license.name,
			issuingOrganization: license.issuingOrganization,
			licenseNumber: license.licenseNumber || "",
			issueDate: license.issueDate || "",
			expirationDate: license.expirationDate || "",
			credentialUrl: license.credentialUrl || "",
		});
		setIsEditing(true);
	};

	const handleCancel = () => {
		setIsEditing(false);
		setEditingId(null);
		setFormData({
			name: "",
			issuingOrganization: "",
			licenseNumber: "",
			issueDate: "",
			expirationDate: "",
			credentialUrl: "",
		});
	};

	const handleSubmit = async (e: React.FormEvent) => {
		e.preventDefault();
		setLoading(true);

		try {
			if (editingId) {
				await jobSeekerClient.updateLicense(
					create(UpdateLicenseRequestSchema, {
						id: editingId,
						name: formData.name,
						issuingOrganization: formData.issuingOrganization,
						licenseNumber: formData.licenseNumber || undefined,
						issueDate: formData.issueDate || undefined,
						expirationDate: formData.expirationDate || undefined,
						credentialUrl: formData.credentialUrl || undefined,
					})
				);
			} else {
				await jobSeekerClient.createLicense(
					create(CreateLicenseRequestSchema, {
						jobSeekerId,
						name: formData.name,
						issuingOrganization: formData.issuingOrganization,
						licenseNumber: formData.licenseNumber || undefined,
						issueDate: formData.issueDate || undefined,
						expirationDate: formData.expirationDate || undefined,
						credentialUrl: formData.credentialUrl || undefined,
					})
				);
			}

			await fetchLicenses();
			handleCancel();
		} catch (error) {
			console.error("Failed to save license:", error);
			alert(error instanceof Error ? error.message : "ライセンスの保存に失敗しました");
		} finally {
			setLoading(false);
		}
	};

	const handleDelete = async (id: string) => {
		if (!confirm("このライセンスを削除しますか？")) return;

		setLoading(true);
		try {
			await jobSeekerClient.deleteLicense(
				create(DeleteLicenseRequestSchema, { id })
			);
			await fetchLicenses();
		} catch (error) {
			console.error("Failed to delete license:", error);
			alert(error instanceof Error ? error.message : "ライセンスの削除に失敗しました");
		} finally {
			setLoading(false);
		}
	};

	return (
		<div className="rounded-lg bg-white p-6 shadow-sm border border-neutral-200 dark:bg-neutral-900 dark:border-neutral-800">
			<div className="mb-6 flex items-center justify-between">
				<h2 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">
					ライセンス・資格
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
							ライセンス名 <span className="text-red-500">*</span>
						</label>
						<input
							type="text"
							value={formData.name}
							onChange={(e) => setFormData({ ...formData, name: e.target.value })}
							className="block w-full min-h-[44px] rounded-lg border border-neutral-300 bg-white px-4 py-2.5 text-base text-neutral-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:bg-neutral-700 dark:border-neutral-600 dark:text-neutral-100"
							required
						/>
					</div>

					<div>
						<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
							発行機関 <span className="text-red-500">*</span>
						</label>
						<input
							type="text"
							value={formData.issuingOrganization}
							onChange={(e) => setFormData({ ...formData, issuingOrganization: e.target.value })}
							className="block w-full min-h-[44px] rounded-lg border border-neutral-300 bg-white px-4 py-2.5 text-base text-neutral-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:bg-neutral-700 dark:border-neutral-600 dark:text-neutral-100"
							required
						/>
					</div>

					<div>
						<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
							ライセンス番号
						</label>
						<input
							type="text"
							value={formData.licenseNumber}
							onChange={(e) => setFormData({ ...formData, licenseNumber: e.target.value })}
							className="block w-full min-h-[44px] rounded-lg border border-neutral-300 bg-white px-4 py-2.5 text-base text-neutral-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:bg-neutral-700 dark:border-neutral-600 dark:text-neutral-100"
						/>
					</div>

					<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
						<div>
							<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
								発行日
							</label>
							<input
								type="date"
								value={formData.issueDate}
								onChange={(e) => setFormData({ ...formData, issueDate: e.target.value })}
								className="block w-full min-h-[44px] rounded-lg border border-neutral-300 bg-white px-4 py-2.5 text-base text-neutral-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:bg-neutral-700 dark:border-neutral-600 dark:text-neutral-100"
							/>
						</div>

						<div>
							<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
								有効期限
							</label>
							<input
								type="date"
								value={formData.expirationDate}
								onChange={(e) => setFormData({ ...formData, expirationDate: e.target.value })}
								className="block w-full min-h-[44px] rounded-lg border border-neutral-300 bg-white px-4 py-2.5 text-base text-neutral-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:bg-neutral-700 dark:border-neutral-600 dark:text-neutral-100"
							/>
						</div>
					</div>

					<div>
						<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
							資格証明URL
						</label>
						<input
							type="url"
							value={formData.credentialUrl}
							onChange={(e) => setFormData({ ...formData, credentialUrl: e.target.value })}
							className="block w-full min-h-[44px] rounded-lg border border-neutral-300 bg-white px-4 py-2.5 text-base text-neutral-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:bg-neutral-700 dark:border-neutral-600 dark:text-neutral-100"
							placeholder="https://..."
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

			{loading && licenses.length === 0 ? (
				<div className="text-center py-8 text-neutral-600 dark:text-neutral-400">
					読み込み中...
				</div>
			) : licenses.length === 0 ? (
				<div className="text-center py-8 text-neutral-600 dark:text-neutral-400">
					ライセンスが登録されていません
				</div>
			) : (
				<div className="space-y-4">
					{licenses.map((license) => (
						<div
							key={license.id}
							className="rounded-lg border border-neutral-200 bg-neutral-50 p-4 dark:border-neutral-700 dark:bg-neutral-800"
						>
							<div className="flex items-start justify-between">
								<div className="flex-1">
									<h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
										{license.name}
									</h3>
									<p className="mt-1 text-sm text-neutral-700 dark:text-neutral-300">
										発行機関: {license.issuingOrganization}
									</p>
									{license.licenseNumber && (
										<p className="mt-1 text-sm text-neutral-700 dark:text-neutral-300">
											ライセンス番号: {license.licenseNumber}
										</p>
									)}
									{(license.issueDate || license.expirationDate) && (
										<p className="mt-1 text-sm text-neutral-700 dark:text-neutral-300">
											{license.issueDate && `発行日: ${license.issueDate}`}
											{license.issueDate && license.expirationDate && " / "}
											{license.expirationDate && `有効期限: ${license.expirationDate}`}
										</p>
									)}
									{license.credentialUrl && (
										<a
											href={license.credentialUrl}
											target="_blank"
											rel="noopener noreferrer"
											className="mt-2 inline-block text-sm text-brand-600 hover:text-brand-700 dark:text-brand-400 dark:hover:text-brand-300"
										>
											資格証明を確認
										</a>
									)}
								</div>
								<div className="ml-4 flex gap-2">
									<TouchOptimizedButton
										variant="secondary"
										size="sm"
										onClick={() => handleEdit(license)}
										disabled={loading}
									>
										編集
									</TouchOptimizedButton>
									<TouchOptimizedButton
										variant="secondary"
										size="sm"
										onClick={() => handleDelete(license.id)}
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



