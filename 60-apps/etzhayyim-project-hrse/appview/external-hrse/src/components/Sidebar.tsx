"use client";

import {  useAuth, useUser, useOrganization, OrganizationSwitcher, UserButton } from "@clerk/nextjs";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useMemo } from "react";
import { ThemeToggle } from "@/components/ThemeToggle";
import { getUserMetadata } from "@/lib/clerk-metadata-client";

/**
 * @etzhayyim/cyber-freelance#Sidebar
 * 左サイドバーナビゲーション
 * Apple HIG準拠：タッチターゲット44px、Safe Area対応
 */
export function Sidebar() {
	const pathname = usePathname();
	const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
	const { isSignedIn, isLoaded } = useAuth();
	const { user } = useUser();
	const { organization, membership } = useOrganization();

	// ユーザーメタデータを取得
	const userMetadata = useMemo(() => {
		return getUserMetadata(user?.publicMetadata as Record<string, unknown> | undefined);
	}, [user?.publicMetadata]);

	const userType = userMetadata.userType;
	const recruiterRole = userMetadata.recruiterRole;

	// 組織ロールを取得（Clerkのmembershipから取得）
	const orgRole = useMemo<string | null>(() => {
		return membership?.role || null;
	}, [membership?.role]);

	// Clerk組織IDを取得（組織に所属している場合）
	const clerkOrgId = useMemo<string | null>(() => {
		// 組織に所属していれば組織IDを返す
		if (organization?.id) {
			return organization.id;
		}
		return null;
	}, [organization?.id]);

	// システム管理者の判定: @etzhayyim.com が含まれているメールアドレスを持つユーザー
	const isSystemAdmin = useMemo(() => {
		if (!user?.emailAddresses || user.emailAddresses.length === 0) {
			return false;
		}
		return user.emailAddresses.some(
			(email) => email.emailAddress?.includes("@etzhayyim.com")
		);
	}, [user?.emailAddresses]);

	// 組織に所属しているかどうか
	const hasOrganization = !!organization?.id;
	// 組織の管理者かどうか（org:admin）
	const isOrgAdmin = orgRole === "org:admin";

	// ユーザータイプの判定（シンプルな優先順位）
	// 1. userTypeが明示的に設定されていればそれを使用
	// 2. 組織に所属している場合:
	//    - org:admin → エージェンシー
	//    - それ以外 → エージェンシー所属リクルーター
	// 3. 組織に所属していない場合 → 求職者

	// 明示的なuserType設定を最優先
	const explicitUserType = userType; // "job_seeker" | "corporate_recruiter" | "agency_recruiter" | "agency" | undefined

	// 判定結果
	let isAgencyRecruiter = false;
	let isAgency = false;
	let isJobSeeker = false;
	let isCorporateRecruiter = false;

	if (explicitUserType === "agency_recruiter") {
		isAgencyRecruiter = true;
	} else if (explicitUserType === "agency") {
		isAgency = true;
	} else if (explicitUserType === "job_seeker") {
		isJobSeeker = true;
	} else if (explicitUserType === "corporate_recruiter") {
		isCorporateRecruiter = true;
	} else if (hasOrganization) {
		// userTypeが未設定で組織に所属している場合
		if (isOrgAdmin) {
			isAgency = true;
		} else {
			isAgencyRecruiter = true;
		}
	} else {
		// userTypeが未設定で組織に所属していない場合 → 求職者
		isJobSeeker = true;
	}

	// メニュー表示制御のヘルパー関数
	// システム管理者の場合はすべてのメニューを表示
	// 各ユーザータイプは自分のメニューのみ表示（排他的）
	const canShowJobSeekerMenu = isSystemAdmin || isJobSeeker;
	const canShowAgencyMenu = isSystemAdmin || isAgency;
	const canShowAgencyRecruiterMenu = isSystemAdmin || isAgencyRecruiter;
	const canShowCorporateRecruiterMenu = isSystemAdmin || isCorporateRecruiter;
	const canShowAgencyMembersMenu = isSystemAdmin || (canShowAgencyMenu && (isOrgAdmin || recruiterRole === "admin"));

	const isActive = (path: string) => {
		if (path === "/") {
			return pathname === "/";
		}
		// 動的ルートに対応: /[orgId]/agency/profile と /agency/profile の両方をチェック
		if (path.startsWith("/agency")) {
			return pathname.startsWith(path) || (clerkOrgId && pathname.startsWith(`/${clerkOrgId}${path}`));
		}
		return pathname.startsWith(path);
	};

	// エージェンシーリンクのURLを生成
	const getAgencyLink = (path: string) => {
		if (clerkOrgId) {
			return `/${clerkOrgId}${path}`;
		}
		return path;
	};

	// 認証状態が読み込まれるまで何も表示しない
	if (!isLoaded) {
		return null;
	}

	return (
		<>
			{/* モバイルメニューボタン */}
			<button
				type="button"
				className="fixed left-4 top-4 z-50 touch-target rounded-md bg-white p-2 shadow-md dark:bg-neutral-900 dark:text-neutral-100 dark:border dark:border-neutral-800 md:hidden"
				onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
				aria-label="メニューを開く"
			>
				<svg
					className="h-6 w-6"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
				>
					{mobileMenuOpen ? (
						<path
							strokeLinecap="round"
							strokeLinejoin="round"
							strokeWidth={2}
							d="M6 18L18 6M6 6l12 12"
						/>
					) : (
						<path
							strokeLinecap="round"
							strokeLinejoin="round"
							strokeWidth={2}
							d="M4 6h16M4 12h16M4 18h16"
						/>
					)}
				</svg>
			</button>

			{/* モバイルオーバーレイ */}
			{mobileMenuOpen && (
				<div
					className="fixed inset-0 z-40 bg-black/50 md:hidden"
					onClick={() => setMobileMenuOpen(false)}
				/>
			)}

			{/* サイドバー - デジタル庁デザインシステム v2.9.0 */}
			<aside
				className={`fixed left-0 top-0 z-40 h-full w-64 transform border-r border-border bg-background shadow-lg transition-transform duration-300 ease-in-out safe-area-left dark:border-neutral-800 dark:bg-neutral-950 dark:shadow-neutral-950/50 ${
					mobileMenuOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
				}`}
			>
				<div className="flex h-full flex-col overflow-y-auto overscroll-contain">
					{/* ロゴ - デジタル庁デザインシステム v2.9.0 */}
					<div className="border-b border-border p-6 dark:border-neutral-800">
						<Link
							href="/"
							className="flex items-center space-x-2"
							onClick={() => setMobileMenuOpen(false)}
						>
							<div className="flex h-10 w-10 items-center justify-center rounded-md bg-brand-500 text-white dark:bg-brand-500">
								<span className="text-xl font-bold">CF</span>
							</div>
							<span className="text-xl font-bold text-content-primary dark:text-neutral-100">
								etzhayyim HRSE
							</span>
						</Link>
					</div>

					{/* ナビゲーションメニュー */}
					<nav className="flex-1 space-y-1 p-4">
						{/* ログインしていないユーザー向けメニュー */}
						{!isSignedIn && (
							<div className="mb-6">
								<h2 className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-neutral-600 dark:text-neutral-400">
									一般
								</h2>
								<Link
									href="/"
									className={`touch-target flex items-center rounded-md px-3 py-3 text-sm font-medium transition-colors ${
										isActive("/") && pathname === "/"
											? "bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-400"
											: "text-neutral-800 hover:bg-neutral-100 dark:text-neutral-300 dark:hover:bg-neutral-800"
									}`}
									onClick={() => setMobileMenuOpen(false)}
								>
									ホーム
								</Link>
							</div>
						)}

						{/* ログイン済みユーザー向けメニュー */}
						{isSignedIn && (
							<>
							{/* 一般 - システム管理者のみ表示 */}
							{isSystemAdmin && (
								<div className="mb-6">
									<h2 className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-neutral-600 dark:text-neutral-400">
										一般
									</h2>
									<Link
										href="/"
										className={`touch-target flex items-center rounded-md px-3 py-3 text-sm font-medium transition-colors ${
											isActive("/") && pathname === "/"
												? "bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-400"
												: "text-neutral-800 hover:bg-neutral-100 dark:text-neutral-300 dark:hover:bg-neutral-800"
										}`}
										onClick={() => setMobileMenuOpen(false)}
									>
										ホーム
									</Link>
								</div>
							)}

						{/* 求職者 - job_seeker タイプまたは全ユーザー向け */}
						{canShowJobSeekerMenu && (
							<div className="mb-6">
								<h2 className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-content-secondary dark:text-neutral-400">
									求職者
								</h2>
								<Link
									href="/job-seeker/profile"
									className={`touch-target flex items-center rounded-md px-3 py-3 text-sm font-medium transition-colors ${
										isActive("/job-seeker/profile")
											? "bg-brand-50 text-brand-500 dark:bg-brand-900/30 dark:text-brand-400"
											: "text-content-primary hover:bg-background-surface dark:text-neutral-300 dark:hover:bg-neutral-800"
									}`}
									onClick={() => setMobileMenuOpen(false)}
								>
									プロファイル
								</Link>
								<Link
									href="/job-seeker/jobs"
									className={`touch-target flex items-center rounded-md px-3 py-3 text-sm font-medium transition-colors ${
										isActive("/job-seeker/jobs")
											? "bg-brand-50 text-brand-500 dark:bg-brand-900/30 dark:text-brand-400"
											: "text-content-primary hover:bg-background-surface dark:text-neutral-300 dark:hover:bg-neutral-800"
									}`}
									onClick={() => setMobileMenuOpen(false)}
								>
									案件を探す
								</Link>
								<Link
									href="/job-seeker/proposals"
									className={`touch-target flex items-center rounded-md px-3 py-3 text-sm font-medium transition-colors ${
										isActive("/job-seeker/proposals")
											? "bg-brand-50 text-brand-500 dark:bg-brand-900/30 dark:text-brand-400"
											: "text-content-primary hover:bg-background-surface dark:text-neutral-300 dark:hover:bg-neutral-800"
									}`}
									onClick={() => setMobileMenuOpen(false)}
								>
									応募管理
								</Link>
							</div>
						)}

						{/* エージェンシー - agencyタイプまたはエージェンシープロファイルが存在する場合のみ表示 */}
						{canShowAgencyMenu && (
							<div className="mb-6">
								<h2 className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-content-secondary dark:text-neutral-400">
									エージェンシー
								</h2>
								<Link
									href={getAgencyLink("/agency")}
									className={`touch-target flex items-center rounded-md px-3 py-3 text-sm font-medium transition-colors ${
										isActive("/agency") && !isActive("/agency/profile") && !isActive("/agency/matching") && !isActive("/agency/members") && !isActive("/agency/recruiter-supporter") && !isActive("/agency/mailbox")
											? "bg-brand-50 text-brand-500 dark:bg-brand-900/30 dark:text-brand-400"
											: "text-content-primary hover:bg-background-surface dark:text-neutral-300 dark:hover:bg-neutral-800"
									}`}
									onClick={() => setMobileMenuOpen(false)}
								>
									ダッシュボード
								</Link>
								<Link
									href={getAgencyLink("/agency/profile")}
									className={`touch-target flex items-center rounded-md px-3 py-3 text-sm font-medium transition-colors ${
										isActive("/agency/profile")
											? "bg-brand-50 text-brand-500 dark:bg-brand-900/30 dark:text-brand-400"
											: "text-content-primary hover:bg-background-surface dark:text-neutral-300 dark:hover:bg-neutral-800"
									}`}
									onClick={() => setMobileMenuOpen(false)}
								>
									プロファイル
								</Link>
								<Link
									href={getAgencyLink("/agency/mailbox")}
									className={`touch-target flex items-center rounded-md px-3 py-3 text-sm font-medium transition-colors ${
										isActive("/agency/mailbox")
											? "bg-brand-50 text-brand-500 dark:bg-brand-900/30 dark:text-brand-400"
											: "text-content-primary hover:bg-background-surface dark:text-neutral-300 dark:hover:bg-neutral-800"
									}`}
									onClick={() => setMobileMenuOpen(false)}
								>
									メールボックス
								</Link>
								<Link
									href={getAgencyLink("/agency/matching")}
									className={`touch-target flex items-center rounded-md px-3 py-3 text-sm font-medium transition-colors ${
										isActive("/agency/matching")
											? "bg-brand-50 text-brand-500 dark:bg-brand-900/30 dark:text-brand-400"
											: "text-content-primary hover:bg-background-surface dark:text-neutral-300 dark:hover:bg-neutral-800"
									}`}
									onClick={() => setMobileMenuOpen(false)}
								>
									マッチング結果
								</Link>
								<Link
									href={getAgencyLink("/agency/recruiter-supporter")}
									className={`touch-target flex items-center rounded-md px-3 py-3 text-sm font-medium transition-colors ${
										isActive("/agency/recruiter-supporter")
											? "bg-brand-50 text-brand-500 dark:bg-brand-900/30 dark:text-brand-400"
											: "text-content-primary hover:bg-background-surface dark:text-neutral-300 dark:hover:bg-neutral-800"
									}`}
									onClick={() => setMobileMenuOpen(false)}
								>
									AI サポート
								</Link>
								{/* メンバー管理 - 組織管理者またはリクルーターのadminロールのみ表示 */}
								{canShowAgencyMembersMenu && (
									<Link
										href={getAgencyLink("/agency/members")}
										className={`touch-target flex items-center rounded-md px-3 py-3 text-sm font-medium transition-colors ${
											isActive("/agency/members")
												? "bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-400"
												: "text-neutral-800 hover:bg-neutral-100 dark:text-neutral-300 dark:hover:bg-neutral-800"
										}`}
										onClick={() => setMobileMenuOpen(false)}
									>
										メンバー管理
									</Link>
								)}
								{/* SES業務管理 - agencyタイプまたはシステム管理者に表示 */}
								{canShowAgencyMenu && (
									<div className="mt-4 pt-4 border-t border-neutral-200 dark:border-neutral-800">
										<h3 className="mb-2 px-3 text-[10px] font-bold uppercase tracking-widest text-neutral-400 dark:text-neutral-500">
											SES業務管理
										</h3>
										<Link
											href="/agency/ses"
											className={`touch-target flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors ${
												pathname === "/agency/ses"
													? "bg-brand-50 text-brand-500 dark:bg-brand-900/30 dark:text-brand-400"
													: "text-content-primary hover:bg-background-surface dark:text-neutral-300 dark:hover:bg-neutral-800"
											}`}
											onClick={() => setMobileMenuOpen(false)}
										>
											SESダッシュボード
										</Link>
										<Link
											href="/agency/ses/bp"
											className={`touch-target flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors ${
												pathname === "/agency/ses/bp"
													? "bg-brand-50 text-brand-500 dark:bg-brand-900/30 dark:text-brand-400"
													: "text-content-primary hover:bg-background-surface dark:text-neutral-300 dark:hover:bg-neutral-800"
											}`}
											onClick={() => setMobileMenuOpen(false)}
										>
											BPパートナー管理
										</Link>
										<Link
											href="/agency/ses/inventory"
											className={`touch-target flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors ${
												pathname === "/agency/ses/inventory"
													? "bg-brand-50 text-brand-500 dark:bg-brand-900/30 dark:text-brand-400"
													: "text-content-primary hover:bg-background-surface dark:text-neutral-300 dark:hover:bg-neutral-800"
											}`}
											onClick={() => setMobileMenuOpen(false)}
										>
											エンジニア在庫
										</Link>
									</div>
								)}
							</div>
						)}

						{/* エージェンシー所属リクルーター - agency_recruiterタイプの場合のみ表示 */}
						{canShowAgencyRecruiterMenu && (
							<div className="mb-6">
								<h2 className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-content-secondary dark:text-neutral-400">
									エージェンシー所属リクルーター
								</h2>
								<Link
									href={organization?.id ? `/${organization.id}/agency-recruiter/profile` : "/agency-recruiter/profile"}
									className={`touch-target flex items-center rounded-md px-3 py-3 text-sm font-medium transition-colors ${
										isActive("/agency-recruiter/profile") || (organization?.id && isActive(`/${organization.id}/agency-recruiter/profile`))
											? "bg-brand-50 text-brand-500 dark:bg-brand-900/30 dark:text-brand-400"
											: "text-content-primary hover:bg-background-surface dark:text-neutral-300 dark:hover:bg-neutral-800"
									}`}
									onClick={() => setMobileMenuOpen(false)}
								>
									プロファイル
								</Link>
								<Link
									href={organization?.id ? `/${organization.id}/agency-recruiter/mailbox` : "/agency-recruiter/mailbox"}
									className={`touch-target flex items-center rounded-md px-3 py-3 text-sm font-medium transition-colors ${
										isActive("/agency-recruiter/mailbox") || (organization?.id && isActive(`/${organization.id}/agency-recruiter/mailbox`))
											? "bg-brand-50 text-brand-500 dark:bg-brand-900/30 dark:text-brand-400"
											: "text-content-primary hover:bg-background-surface dark:text-neutral-300 dark:hover:bg-neutral-800"
									}`}
									onClick={() => setMobileMenuOpen(false)}
								>
									メールボックス
								</Link>
								<Link
									href={organization?.id ? `/${organization.id}/agency-recruiter/matching` : "/agency-recruiter/matching"}
									className={`touch-target flex items-center rounded-md px-3 py-3 text-sm font-medium transition-colors ${
										isActive("/agency-recruiter/matching") || (organization?.id && isActive(`/${organization.id}/agency-recruiter/matching`))
											? "bg-brand-50 text-brand-500 dark:bg-brand-900/30 dark:text-brand-400"
											: "text-content-primary hover:bg-background-surface dark:text-neutral-300 dark:hover:bg-neutral-800"
									}`}
									onClick={() => setMobileMenuOpen(false)}
								>
									マッチング結果
								</Link>
								<Link
									href={getAgencyLink("/agency/recruiter-supporter")}
									className={`touch-target flex items-center rounded-md px-3 py-3 text-sm font-medium transition-colors ${
										isActive("/agency/recruiter-supporter")
											? "bg-brand-50 text-brand-500 dark:bg-brand-900/30 dark:text-brand-400"
											: "text-content-primary hover:bg-background-surface dark:text-neutral-300 dark:hover:bg-neutral-800"
									}`}
									onClick={() => setMobileMenuOpen(false)}
								>
									AI サポート
								</Link>
							</div>
						)}

						{/* リクルーター - corporate_recruiterタイプの場合のみ表示 */}
						{canShowCorporateRecruiterMenu && (
							<div className="mb-6">
								<h2 className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-content-secondary dark:text-neutral-400">
									リクルーター
								</h2>
								<Link
									href="/corporate-recruiter"
									className={`touch-target flex items-center rounded-md px-3 py-3 text-sm font-medium transition-colors ${
										isActive("/corporate-recruiter") && pathname === "/corporate-recruiter"
											? "bg-brand-50 text-brand-500 dark:bg-brand-900/30 dark:text-brand-400"
											: "text-content-primary hover:bg-background-surface dark:text-neutral-300 dark:hover:bg-neutral-800"
									}`}
									onClick={() => setMobileMenuOpen(false)}
								>
									ダッシュボード
								</Link>
								<Link
									href="/corporate-recruiter/profile"
									className={`touch-target flex items-center rounded-md px-3 py-3 text-sm font-medium transition-colors ${
										isActive("/corporate-recruiter/profile")
											? "bg-brand-50 text-brand-500 dark:bg-brand-900/30 dark:text-brand-400"
											: "text-content-primary hover:bg-background-surface dark:text-neutral-300 dark:hover:bg-neutral-800"
									}`}
									onClick={() => setMobileMenuOpen(false)}
								>
									プロファイル
								</Link>
								<Link
									href="/corporate-recruiter/jobs"
									className={`touch-target flex items-center rounded-md px-3 py-3 text-sm font-medium transition-colors ${
										isActive("/corporate-recruiter/jobs")
											? "bg-brand-50 text-brand-500 dark:bg-brand-900/30 dark:text-brand-400"
											: "text-content-primary hover:bg-background-surface dark:text-neutral-300 dark:hover:bg-neutral-800"
									}`}
									onClick={() => setMobileMenuOpen(false)}
								>
									案件管理
								</Link>
								<Link
									href="/corporate-recruiter/matching"
									className={`touch-target flex items-center rounded-md px-3 py-3 text-sm font-medium transition-colors ${
										isActive("/corporate-recruiter/matching")
											? "bg-brand-50 text-brand-500 dark:bg-brand-900/30 dark:text-brand-400"
											: "text-content-primary hover:bg-background-surface dark:text-neutral-300 dark:hover:bg-neutral-800"
									}`}
									onClick={() => setMobileMenuOpen(false)}
								>
									マッチング結果
								</Link>
							</div>
						)}

							{/* 管理者 - システム管理者（@etzhayyim.com メールアドレス）のみ表示 */}
							{isSystemAdmin && (
								<div className="mb-6">
									<h2 className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-content-secondary dark:text-neutral-400">
										管理者
									</h2>
									<Link
										href="/admin"
										className={`touch-target flex items-center rounded-md px-3 py-3 text-sm font-medium transition-colors ${
											isActive("/admin") && pathname === "/admin"
												? "bg-brand-50 text-brand-500 dark:bg-brand-900/30 dark:text-brand-400"
												: "text-content-secondary hover:bg-background-surface dark:text-neutral-300 dark:hover:bg-neutral-800"
										}`}
										onClick={() => setMobileMenuOpen(false)}
									>
										ダッシュボード
									</Link>
									<Link
										href="/admin/job-seekers"
										className={`touch-target flex items-center rounded-md px-3 py-3 text-sm font-medium transition-colors ${
											isActive("/admin/job-seekers")
												? "bg-brand-50 text-brand-500 dark:bg-brand-900/30 dark:text-brand-400"
												: "text-content-secondary hover:bg-background-surface dark:text-neutral-300 dark:hover:bg-neutral-800"
										}`}
										onClick={() => setMobileMenuOpen(false)}
									>
										求職者管理
									</Link>
									<Link
										href="/admin/agencies"
										className={`touch-target flex items-center rounded-md px-3 py-3 text-sm font-medium transition-colors ${
											isActive("/admin/agencies")
												? "bg-brand-50 text-brand-500 dark:bg-brand-900/30 dark:text-brand-400"
												: "text-content-secondary hover:bg-background-surface dark:text-neutral-300 dark:hover:bg-neutral-800"
										}`}
										onClick={() => setMobileMenuOpen(false)}
									>
										エージェンシー管理
									</Link>
									<Link
										href="/admin/recruiters"
										className={`touch-target flex items-center rounded-md px-3 py-3 text-sm font-medium transition-colors ${
											isActive("/admin/recruiters")
												? "bg-brand-50 text-brand-500 dark:bg-brand-900/30 dark:text-brand-400"
												: "text-content-secondary hover:bg-background-surface dark:text-neutral-300 dark:hover:bg-neutral-800"
										}`}
										onClick={() => setMobileMenuOpen(false)}
									>
										リクルーター管理
									</Link>
									<Link
										href="/admin/jobs"
										className={`touch-target flex items-center rounded-md px-3 py-3 text-sm font-medium transition-colors ${
											isActive("/admin/jobs")
												? "bg-brand-50 text-brand-500 dark:bg-brand-900/30 dark:text-brand-400"
												: "text-content-secondary hover:bg-background-surface dark:text-neutral-300 dark:hover:bg-neutral-800"
										}`}
										onClick={() => setMobileMenuOpen(false)}
									>
										案件管理
									</Link>
									<Link
										href="/admin/master-data"
										className={`touch-target flex items-center rounded-md px-3 py-3 text-sm font-medium transition-colors ${
											isActive("/admin/master-data")
												? "bg-brand-50 text-brand-500 dark:bg-brand-900/30 dark:text-brand-400"
												: "text-content-secondary hover:bg-background-surface dark:text-neutral-300 dark:hover:bg-neutral-800"
										}`}
										onClick={() => setMobileMenuOpen(false)}
									>
										マスターデータ
									</Link>
									<Link
										href="/admin/email-analysis"
										className={`touch-target flex items-center rounded-md px-3 py-3 text-sm font-medium transition-colors ${
											isActive("/admin/email-analysis")
												? "bg-brand-50 text-brand-500 dark:bg-brand-900/30 dark:text-brand-400"
												: "text-content-secondary hover:bg-background-surface dark:text-neutral-300 dark:hover:bg-neutral-800"
										}`}
										onClick={() => setMobileMenuOpen(false)}
									>
										メール分析
									</Link>
								</div>
							)}
							</>
						)}
					</nav>

					{/* テーマ切り替え */}
					<div className="border-t border-border p-4 dark:border-neutral-800">
						<div className="flex items-center justify-between px-3">
							<span className="text-xs font-semibold uppercase tracking-wider text-content-secondary dark:text-neutral-400">
								テーマ
							</span>
							<ThemeToggle />
						</div>
					</div>

					{/* アカウントセクション */}
					<div className="border-t border-border p-4 dark:border-neutral-800">
						{!isSignedIn && (
							<>
								<h2 className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-content-secondary dark:text-neutral-400">
									アカウント
								</h2>
								<Link
									href="/auth/signin"
									className="touch-target mb-2 flex items-center justify-center rounded-md bg-background-surface px-3 py-3 text-sm font-medium text-content-primary transition-colors hover:bg-neutral-200 dark:bg-neutral-800 dark:text-neutral-100 dark:hover:bg-neutral-700"
									onClick={() => setMobileMenuOpen(false)}
								>
									サインイン
								</Link>
								<Link
									href="/auth/signup"
									className="touch-target flex items-center justify-center rounded-md bg-brand-500 px-3 py-3 text-sm font-medium text-white transition-colors hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600"
									onClick={() => setMobileMenuOpen(false)}
								>
									登録
								</Link>
							</>
						)}
						{isSignedIn && (
							<div className="space-y-3">
								{/* Organization Switcher */}
								<div className="clerk-sidebar-component">
									<OrganizationSwitcher
										hidePersonal
										afterCreateOrganizationUrl="/agency/profile"
										afterSelectOrganizationUrl="/"
										appearance={{
											elements: {
												rootBox: "w-full",
												organizationSwitcherTrigger:
													"w-full justify-between px-3 py-2.5 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800/50 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors",
												organizationSwitcherTriggerIcon: "text-neutral-500 dark:text-neutral-400",
												organizationPreviewMainIdentifier:
													"text-sm font-medium text-neutral-900 dark:text-neutral-100",
												organizationPreviewSecondaryIdentifier:
													"text-xs text-neutral-500 dark:text-neutral-400",
											},
										}}
									/>
								</div>
								{/* User Button with full width */}
								<div className="clerk-sidebar-component flex items-center gap-3 px-3 py-2.5 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800/50 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors">
									<UserButton
										appearance={{
											elements: {
												avatarBox: "w-8 h-8",
												userButtonTrigger: "focus:shadow-none",
											},
										}}
									/>
									<div className="flex-1 min-w-0">
										<div className="text-sm font-medium text-neutral-900 dark:text-neutral-100 truncate">
											{user?.firstName || user?.username || "ユーザー"}
										</div>
										<div className="text-xs text-neutral-500 dark:text-neutral-400 truncate">
											{user?.primaryEmailAddress?.emailAddress || ""}
										</div>
									</div>
								</div>
							</div>
						)}
					</div>
				</div>
			</aside>
		</>
	);
}
