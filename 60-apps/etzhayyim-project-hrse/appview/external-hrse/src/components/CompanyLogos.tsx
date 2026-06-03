"use client";

import Image from "next/image";

/**
 * @etzhayyim/cyber-freelance#CompanyLogos
 * 企業ロゴセクション
 * Toptalスタイルの信頼性セクション
 *
 * API連携可能な求人プラットフォーム一覧:
 * - Indeed: API連携可能（Indeed API）
 * - LinkedIn: Talent Solutions API（パートナーシップ必要）
 * - ZipRecruiter: Campaign Management API
 * - CareerBuilder: ATS統合可能
 * - Greenhouse: Harvest API
 * - Lever: REST API
 * - Workday: SOAP/REST API
 * - SmartRecruiters: Public API
 * - Jobvite: API Access
 * - Wellfound: ATS統合可能（旧AngelList Talent）
 */
interface CompanyLogosProps {
	logos?: Array<{ name: string; logoUrl?: string; apiAvailable?: boolean; visible?: boolean }>;
}

/**
 * API連携が可能な求人プラットフォーム
 * ローカルのロゴファイルを使用（public/logos/）
 *
 * ロゴCDNサービス（参考）:
 * - SimpleIcons: https://simpleicons.org/ (無料、オープンソース)
 * - Logo.dev: https://logo.dev/ (Clearbitの後継、APIキー必要)
 * - Brandfetch: https://brandfetch.com/ (APIキー必要、高品質)
 * - FreeLogoAPI: https://freelogoapi.com/ (無料、Google CDN使用)
 */
const defaultCompanies = [
	{
		name: "Indeed",
		logoUrl: "/logos/indeed.svg",
		apiAvailable: true,
		visible: true
	},
	{
		name: "LinkedIn",
		logoUrl: "/logos/linkedin.svg",
		apiAvailable: true,
		visible: true
	},
	{
		name: "ZipRecruiter",
		logoUrl: "/logos/ziprecruiter.svg",
		apiAvailable: true,
		visible: false
	},
	{
		name: "CareerBuilder",
		logoUrl: "/logos/careerbuilder.svg",
		apiAvailable: true,
		visible: false
	},
	{
		name: "Greenhouse",
		logoUrl: "/logos/greenhouse.svg",
		apiAvailable: true,
		visible: true
	},
	{
		name: "Lever",
		logoUrl: "/logos/lever.svg",
		apiAvailable: true,
		visible: false
	},
	{
		name: "Workday",
		logoUrl: "/logos/workday.svg",
		apiAvailable: true,
		visible: false
	},
	{
		name: "SmartRecruiters",
		logoUrl: "/logos/smartrecruiters.svg",
		apiAvailable: true,
		visible: false
	},
	{
		name: "Jobvite",
		logoUrl: "/logos/jobvite.svg",
		apiAvailable: true,
		visible: false
	},
	{
		name: "Wellfound",
		logoUrl: "/logos/wellfound.svg",
		apiAvailable: true,
		visible: false
	},
];

export function CompanyLogos({ logos = defaultCompanies }: CompanyLogosProps) {
	// visible: trueのもののみ表示
	const visibleLogos = logos.filter((company) => company.visible !== false);

	return (
		<div className="py-12 bg-white dark:bg-neutral-950">
			<div className="mx-auto max-w-7xl px-4 md:px-6 lg:px-8">
				<p className="mb-8 text-center text-sm font-semibold uppercase tracking-wider text-neutral-600 dark:text-neutral-400">
					連携企業・求人プラットフォーム
				</p>
				<div className="grid grid-cols-2 gap-8 md:grid-cols-3 lg:grid-cols-5">
					{visibleLogos.map((company, index) => (
						<div
							key={index}
							className="flex items-center justify-center transition-all hover:scale-105"
							title={company.apiAvailable ? `${company.name} - API連携可能` : company.name}
						>
							{company.logoUrl ? (
								<div className="group relative h-12 w-full">
									<Image
										src={company.logoUrl}
										alt={company.name}
										fill
										className="object-contain transition-all duration-300 grayscale opacity-60 hover:grayscale-0 hover:opacity-100 dark:opacity-60 dark:hover:opacity-100"
										unoptimized
									/>
								</div>
							) : (
								<div className="flex h-12 items-center justify-center text-sm font-semibold text-neutral-600 dark:text-neutral-400">
									{company.name}
									{company.apiAvailable && (
										<span className="ml-1 text-xs text-green-600 dark:text-green-400" title="API連携可能">
											✓
										</span>
									)}
								</div>
							)}
						</div>
					))}
				</div>
				{/* API連携情報の注釈 */}
				<div className="mt-8 text-center">
					<p className="text-xs text-neutral-600 dark:text-neutral-400">
						すべてのプラットフォームでAPI連携が可能です
					</p>
				</div>
			</div>
		</div>
	);
}

