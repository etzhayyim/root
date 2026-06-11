"use client";

/**
 * @etzhayyim/etzhayyim-hrse#AdminCompaniesConnect
 * 企業管理ページ（Connect-Web版）
 */

import { useUser } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { TouchOptimizedButton } from "@/components/TouchOptimizedButton";
import { useJobServiceClient, type Company } from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import { ListCompaniesRequestSchema } from "@/gen/proto/hrse/v1/job_pb";
import Link from "next/link";

export default function CompaniesAdminPage() {
	const { user, isLoaded } = useUser();
	const router = useRouter();
	const jobClient = useJobServiceClient();

	const [companies, setCompanies] = useState<Company[]>([]);
	const [loading, setLoading] = useState(true);
	const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);

	const fetchCompanies = useCallback(async () => {
		setLoading(true);
		try {
			const res = await jobClient.listCompanies(create(ListCompaniesRequestSchema, { limit: 100 }));
			setCompanies(res.companies || []);
		} catch (error) {
			console.error("Failed to fetch companies:", error);
		} finally {
			setLoading(false);
		}
	}, [jobClient]);

	useEffect(() => {
		if (isLoaded && user) {
			fetchCompanies();
		}
	}, [isLoaded, user, fetchCompanies]);

	if (!isLoaded || loading) {
		return (
			<div className="flex min-h-screen items-center justify-center">
				<div className="text-lg">読み込み中...</div>
			</div>
		);
	}

	if (!user) {
		router.push("/auth/signin");
		return null;
	}

	return (
		<div className="min-h-screen bg-gray-50 p-4 md:p-8 dark:bg-neutral-950">
			<div className="mx-auto max-w-7xl">
				<div className="mb-6 flex items-center justify-between">
					<div className="flex items-center gap-3">
						<h1 className="text-3xl font-bold text-gray-900 dark:text-neutral-100">企業管理</h1>
						<span className="rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-800 dark:bg-green-900 dark:text-green-200">
							Connect-Web
						</span>
					</div>
					<Link href="/admin">
						<TouchOptimizedButton variant="secondary" size="sm">管理者トップへ</TouchOptimizedButton>
					</Link>
				</div>

				<div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
					{/* 左側: 企業一覧 */}
					<div className="rounded-lg bg-white shadow dark:bg-neutral-900">
						<div className="border-b border-gray-200 p-4 dark:border-neutral-800">
							<h2 className="text-xl font-semibold text-gray-900 dark:text-neutral-100">企業一覧</h2>
						</div>
						{companies.length === 0 ? (
							<div className="p-12 text-center">
								<p className="text-gray-600 dark:text-neutral-400">企業がありません</p>
							</div>
						) : (
							<div className="divide-y divide-gray-200 dark:divide-neutral-800">
								{companies.map((company) => (
									<button
										key={company.id}
										type="button"
										onClick={() => setSelectedCompany(company)}
										className={`w-full p-4 text-left transition-colors hover:bg-gray-50 dark:hover:bg-neutral-800 ${
											selectedCompany?.id === company.id ? "bg-blue-50 dark:bg-blue-900/20" : ""
										}`}
									>
									<div className="font-semibold text-gray-900 dark:text-neutral-100">{company.name}</div>
									<div className="mt-1 text-xs text-gray-500 dark:text-neutral-500">ID: {company.id}</div>
									</button>
								))}
							</div>
						)}
					</div>

					{/* 右側: 詳細 */}
					<div className="rounded-lg bg-white shadow dark:bg-neutral-900">
						<div className="border-b border-gray-200 p-4 dark:border-neutral-800">
							<h2 className="text-xl font-semibold text-gray-900 dark:text-neutral-100">詳細</h2>
						</div>
						{selectedCompany ? (
							<div className="p-6 space-y-4">
								<div>
									<label className="block text-sm font-medium text-gray-700 dark:text-neutral-300">ID</label>
									<div className="mt-1 text-sm text-gray-900 dark:text-neutral-100">{selectedCompany.id}</div>
								</div>
								<div>
									<label className="block text-sm font-medium text-gray-700 dark:text-neutral-300">企業名</label>
									<div className="mt-1 text-sm text-gray-900 dark:text-neutral-100">{selectedCompany.name}</div>
								</div>
								{selectedCompany.createdAt && (
									<div>
										<label className="block text-sm font-medium text-gray-700 dark:text-neutral-300">作成日時</label>
										<div className="mt-1 text-sm text-gray-900 dark:text-neutral-100">
											{selectedCompany.createdAt.seconds ? new Date(Number(selectedCompany.createdAt.seconds) * 1000).toLocaleString("ja-JP") : "-"}
										</div>
									</div>
								)}
								{selectedCompany.updatedAt && (
									<div>
										<label className="block text-sm font-medium text-gray-700 dark:text-neutral-300">更新日時</label>
										<div className="mt-1 text-sm text-gray-900 dark:text-neutral-100">
											{selectedCompany.updatedAt.seconds ? new Date(Number(selectedCompany.updatedAt.seconds) * 1000).toLocaleString("ja-JP") : "-"}
										</div>
									</div>
								)}
							</div>
						) : (
							<div className="flex items-center justify-center p-12">
								<p className="text-gray-600 dark:text-neutral-400">左側のリストから企業を選択してください</p>
							</div>
						)}
					</div>
				</div>
			</div>
		</div>
	);
}
