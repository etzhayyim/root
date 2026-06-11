"use client";

/**
 * @etzhayyim/etzhayyim-hrse#AgencyRecruiterProfile
 * エージェンシー所属リクルーター向けプロファイルページ
 */

import { useUser, useOrganization } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useState, useCallback, useEffect } from "react";
import { TouchOptimizedButton } from "@/components/TouchOptimizedButton";
import { useAgencyServiceClient, type Recruiter } from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import { GetRecruiterProfileRequestSchema } from "@/gen/proto/hrse/v1/agency_pb";

export default function AgencyRecruiterProfilePage() {
	const { user, isLoaded } = useUser();
	const { organization } = useOrganization();
	const router = useRouter();
	const agencyClient = useAgencyServiceClient();

	const [recruiter, setRecruiter] = useState<Recruiter | null>(null);
	const [loading, setLoading] = useState(true);

	// 組織に所属している場合は組織付きURLにリダイレクト
	useEffect(() => {
		if (organization?.id) {
			router.push(`/${organization.id}/agency-recruiter/profile`);
		}
	}, [organization?.id, router]);

	// リクルータープロファイル取得
	const fetchRecruiter = useCallback(async () => {
		if (!user?.id) return;

		try {
			const res = await agencyClient.getRecruiterProfile(
				create(GetRecruiterProfileRequestSchema, {})
			);
			if (res.recruiter) {
				setRecruiter(res.recruiter);
			}
		} catch (error) {
			console.error("Failed to fetch recruiter:", error);
		} finally {
			setLoading(false);
		}
	}, [user?.id, agencyClient]);

	useEffect(() => {
		if (user?.id) {
			fetchRecruiter();
		} else {
			setLoading(false);
		}
	}, [user?.id, fetchRecruiter]);

	if (!isLoaded || loading) {
		return (
			<div className="flex min-h-screen items-center justify-center">
				<div className="text-lg text-neutral-600 dark:text-neutral-400">
					読み込み中...
				</div>
			</div>
		);
	}

	if (!user) {
		router.push("/auth/signin");
		return null;
	}

	return (
		<div className="min-h-screen bg-neutral-50 p-4 md:p-8 dark:bg-neutral-950">
			<div className="mx-auto max-w-4xl">
				{/* ヘッダー */}
				<div className="mb-8">
					<h1 className="text-3xl font-bold text-neutral-900 dark:text-neutral-100">
						エージェンシー所属リクルーター プロファイル
					</h1>
					<p className="mt-2 text-neutral-600 dark:text-neutral-400">
						あなたのプロファイル情報を管理します
					</p>
				</div>

				{/* プロファイル情報 */}
				<div className="rounded-lg bg-white p-6 shadow dark:bg-neutral-900">
					{recruiter ? (
						<div className="space-y-4">
							<div>
								<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">
									名前
								</label>
								<p className="mt-1 text-neutral-900 dark:text-neutral-100">
									{recruiter.name || user.firstName || "未設定"}
								</p>
							</div>
							<div>
								<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">
									メールアドレス
								</label>
								<p className="mt-1 text-neutral-900 dark:text-neutral-100">
									{recruiter.email || user.primaryEmailAddress?.emailAddress || "未設定"}
								</p>
							</div>
							<div>
								<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">
									電話番号
								</label>
								<p className="mt-1 text-neutral-900 dark:text-neutral-100">
									{recruiter.phone || "未設定"}
								</p>
							</div>
						</div>
					) : (
						<div className="text-center">
							<p className="mb-4 text-neutral-600 dark:text-neutral-400">
								リクルータープロファイルが作成されていません
							</p>
							<p className="text-sm text-neutral-500 dark:text-neutral-400">
								エージェンシー管理者にお問い合わせください
							</p>
						</div>
					)}
				</div>

				{/* アクション */}
				<div className="mt-6 flex justify-end gap-4">
					<TouchOptimizedButton
						variant="outline"
						onClick={() => router.push("/agency-recruiter/matching")}
					>
						マッチング結果を確認
					</TouchOptimizedButton>
				</div>
			</div>
		</div>
	);
}
