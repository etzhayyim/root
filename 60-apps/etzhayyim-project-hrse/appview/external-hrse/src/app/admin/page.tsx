"use client";

import { useUser } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { TouchOptimizedButton } from "@/components/TouchOptimizedButton";

/**
 * 管理者ページインデックス
 */
export default function AdminPage() {
	const { user, isLoaded } = useUser();
	const router = useRouter();

	if (!isLoaded) {
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

	const adminPages = [
		{
			title: "ユーザー管理",
			description: "Clerkユーザーの一覧、メタデータ編集",
			href: "/admin/users",
			icon: "👥",
		},
		{
			title: "組織管理",
			description: "Clerk組織の一覧、メタデータ編集",
			href: "/admin/organizations",
			icon: "🏢",
		},
		{
			title: "企業管理",
			description: "企業の一覧、詳細、編集",
			href: "/admin/companies",
			icon: "🏢",
		},
		{
			title: "エージェンシー管理",
			description: "エージェンシーの一覧、詳細、編集",
			href: "/admin/agencies",
			icon: "🏛️",
		},
		{
			title: "求職者管理",
			description: "求職者の一覧、詳細、編集",
			href: "/admin/job-seekers",
			icon: "👤",
		},
		{
			title: "リクルーター管理",
			description: "リクルーターの一覧、詳細、編集",
			href: "/admin/recruiters",
			icon: "🎯",
		},
		{
			title: "マスターデータ管理",
			description: "資格、専門分野、言語などのマスターデータ管理",
			href: "/admin/master-data",
			icon: "📊",
		},
		{
			title: "メール分析管理",
			description: "メール分析結果の確認と管理",
			href: "/admin/email-analysis",
			icon: "📧",
		},
		{
			title: "案件管理",
			description: "案件の一覧、詳細、編集",
			href: "/admin/jobs",
			icon: "📋",
		},
	];

	return (
		<div className="min-h-screen bg-background-surface p-4 md:p-8 dark:bg-neutral-950">
			<div className="mx-auto max-w-7xl">
				<h1 className="mb-8 text-3xl font-bold text-content-primary dark:text-neutral-100">
					管理者ページ
				</h1>

				<div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
					{adminPages.map((page) => (
						<Link
							key={page.href}
							href={page.href}
							className="group rounded-md bg-background p-6 shadow transition-shadow hover:shadow-lg dark:bg-neutral-900"
						>
							<div className="mb-4 text-4xl">{page.icon}</div>
							<h2 className="mb-2 text-xl font-semibold text-content-primary group-hover:text-brand-500 dark:text-neutral-100 dark:group-hover:text-brand-400">
								{page.title}
							</h2>
							<p className="text-sm text-content-secondary dark:text-neutral-400">
								{page.description}
							</p>
						</Link>
					))}
				</div>
			</div>
		</div>
	);
}

