import Link from "next/link";
import { redirect } from "next/navigation";
import { ExpertCard } from "@/components/ExpertCard";
import { StatCard } from "@/components/StatCard";
import { TestimonialCard } from "@/components/TestimonialCard";
import { CompanyLogos } from "@/components/CompanyLogos";
import { TouchOptimizedButton } from "@/components/TouchOptimizedButton";
import { createServerTransport } from "@/lib/connect/client";
import { JobSeekerService } from "@/gen/proto/hrse/v1/job_seeker_pb";
import { createClient } from "@connectrpc/connect";
import { create } from "@bufbuild/protobuf";
import { SearchJobSeekersRequestSchema } from "@/gen/proto/hrse/v1/job_seeker_pb";
import { auth, clerkClient } from "@clerk/nextjs/server";
import { getUserAuthInfo, determineEffectiveUserType } from "@/lib/auth-helpers";

/**
 * システム管理者かどうかを判定
 * @etzhayyim.com ドメインのメールアドレスを持つユーザーを管理者とみなす
 */
async function isSystemAdmin(): Promise<boolean> {
	const { userId } = await auth();
	if (!userId) {
		return false;
	}

	try {
		const client = await clerkClient();
		const user = await client.users.getUser(userId);

		if (!user.emailAddresses || user.emailAddresses.length === 0) {
			return false;
		}

		return user.emailAddresses.some(
			(email) => email.emailAddress?.includes("@etzhayyim.com")
		);
	} catch (error) {
		console.error("Failed to check admin status:", error);
		return false;
	}
}

/**
 * @etzhayyim/cyber-freelance#LandingPage
 * Toptalスタイルのランディングページ
 * Apple HIG準拠：タッチターゲット44px、認知負荷最小化、Fittsの法則
 */
export default async function Home() {
	// 認証状態を確認
	const { userId, orgId } = await auth();

	if (userId) {
		const authInfo = await getUserAuthInfo();
		const effectiveUserType = determineEffectiveUserType(authInfo);

		// authInfo.clerkOrgId を優先使用（組織メンバーシップから取得済み）
		const effectiveOrgId = authInfo.clerkOrgId || orgId;

		// ユーザータイプに応じて適切なページにリダイレクト
		if (effectiveUserType === "agency") {
			// エージェンシーの場合はダッシュボードにリダイレクト
			if (effectiveOrgId) {
				redirect(`/${effectiveOrgId}/agency`);
			} else {
				// 組織IDがない場合は /agency にリダイレクト（middlewareが処理）
				redirect("/agency");
			}
		} else if (effectiveUserType === "job_seeker") {
			// 求職者の場合はプロファイルページにリダイレクト
			redirect("/job-seeker/profile");
		} else if (effectiveUserType === "corporate_recruiter") {
			// 企業担当リクルーターの場合はダッシュボードにリダイレクト
			redirect("/corporate-recruiter");
		} else if (effectiveUserType === "agency_recruiter") {
			// エージェンシー所属リクルーターの場合
			if (effectiveOrgId) {
				redirect(`/${effectiveOrgId}/agency-recruiter/profile`);
			} else {
				redirect("/agency-recruiter/profile");
			}
		}
	}

	// 管理者判定
	const adminOnly = await isSystemAdmin();

	// DBからエキスパート情報を取得（Connect-Web）- 管理者の場合のみ
	let experts: Array<{
		name: string;
		title: string;
		specialization: string;
		previousCompany?: string;
	}> = [];

	// 管理者の場合のみエキスパート情報を取得
	if (adminOnly) {
		try {
			const transport = createServerTransport();
			const client = createClient(JobSeekerService, transport);
			const res = await client.searchJobSeekers(
				create(SearchJobSeekersRequestSchema, {
					limit: 4,
					offset: 0,
				})
			);

			if (res.jobSeekers && res.jobSeekers.length > 0) {
				experts = res.jobSeekers.slice(0, 4).map((jobSeeker, index) => {
					const specialization = jobSeeker.specializations?.[0];
					const certification = jobSeeker.certifications?.[0];
					const specializationName = specialization?.nameJa || "サイバーセキュリティ";
					const certificationName = certification?.nameJa || "セキュリティエンジニア";

					// 専門分野に基づいてタイトルを決定
					let title = certificationName;
					if (specializationName.includes("ペネトレーション") || specializationName.includes("侵入")) {
						title = "ペネトレーションテスター";
					} else if (specializationName.includes("クラウド")) {
						title = "クラウドセキュリティアーキテクト";
					} else if (specializationName.includes("インシデント") || specializationName.includes("対応")) {
						title = "インシデントレスポンダー";
					} else if (specializationName.includes("コンプライアンス") || specializationName.includes("規制")) {
						title = "セキュリティコンサルタント";
					}

					return {
						name: `エキスパート ${index + 1}`,
						title: title,
						specialization: specializationName,
						previousCompany: undefined,
					};
				});
			}
		} catch (error) {
			console.error("Failed to fetch experts:", error);
		}
	}

	const testimonials = [
		{
			quote:
				"etzhayyim HRSEを利用して、優秀なセキュリティエンジニアを見つけることができました。迅速な対応と専門性の高さに感動しています。",
			authorName: "",
			authorTitle: "CTO",
			companyName: "テクノロジー企業E",
		},
		{
			quote:
				"プラットフォームのマッチング機能が非常に優れており、我々の要件に完全に合致する専門家を48時間以内に見つけることができました。",
			authorName: "",
			authorTitle: "セキュリティマネージャー",
			companyName: "金融機関F",
		},
		{
			quote:
				"サイバーセキュリティ特化型のプラットフォームとして、業界最高水準のタレントが集まっています。今後も継続的に利用する予定です。",
			authorName: "",
			authorTitle: "プロダクトマネージャー",
			companyName: "スタートアップG",
		},
	];

	return (
		<div className="flex flex-col">
			{/* ヒーローセクション */}
			<section className="gradient-hero relative overflow-hidden px-4 py-20 text-white md:px-6 lg:px-8 lg:py-32 transition-colors duration-300">
				<div className="mx-auto max-w-7xl">
					<div className="mx-auto max-w-3xl text-center">
						<h1 className="mb-6 text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl lg:text-display-lg">
							サイバーセキュリティの
							<br />
							<span className="text-white">トップ3%のタレントを採用</span>
						</h1>
						<p className="mb-8 text-xl leading-relaxed text-white/90 sm:text-2xl">
							etzhayyim HRSEは、サイバーセキュリティ特化型のフリーランスマッチングプラットフォームです。
                            <br />
							厳格な審査を通過した専門家が、あなたの重要なプロジェクトをサポートします。
						</p>
						<div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
							<Link href="/job-seeker/jobs">
								<TouchOptimizedButton
									variant="secondary"
									size="lg"
									className="bg-white text-brand-700 hover:bg-neutral-50 dark:bg-neutral-800 dark:text-brand-400 dark:hover:bg-neutral-700"
								>
									タレントを探す
								</TouchOptimizedButton>
							</Link>
							<Link href="/auth/signup">
								<TouchOptimizedButton
									variant="outline"
									size="lg"
									className="border-2 border-white text-white hover:bg-white/10 dark:border-neutral-300 dark:text-neutral-100 dark:hover:bg-neutral-800/50"
								>
									エキスパートになる
								</TouchOptimizedButton>
							</Link>
						</div>
					</div>
				</div>
			</section>

			{/* 検証済みエキスパートセクション - 管理者のみ表示 */}
			{adminOnly && (
				<section className="bg-background px-4 py-16 dark:bg-neutral-950 md:px-6 lg:px-8" id="experts">
					<div className="mx-auto max-w-7xl">
						<div className="mb-12 text-center">
							<h2 className="mb-4 text-3xl font-bold text-content-primary dark:text-neutral-100 md:text-4xl">
								検証済みエキスパート
							</h2>
							<p className="mx-auto max-w-2xl text-lg text-content-secondary dark:text-neutral-300">
								厳格な審査プロセスを通過した、業界トップレベルのセキュリティ専門家が
								プラットフォームに登録しています。
							</p>
						</div>
						<div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
							{experts.map((expert, index) => (
								<ExpertCard key={index} {...expert} />
							))}
						</div>
						<div className="mt-12 text-center">
							<Link href="/job-seeker/jobs">
								<TouchOptimizedButton variant="primary" size="lg">
									すべてのエキスパートを見る
								</TouchOptimizedButton>
							</Link>
						</div>
					</div>
				</section>
			)}

			{/* 信頼性セクション - 企業ロゴ */}
			<CompanyLogos />

			{/* 統計・実績セクション */}
			<section className="bg-background-surface px-4 py-16 dark:bg-neutral-900 md:px-6 lg:px-8">
				<div className="mx-auto max-w-7xl">
					<div className="grid grid-cols-1 gap-8 md:grid-cols-3">
						<StatCard value="140+" label="カ国対応" />
						<StatCard value="30,000+" label="クライアント" />
						<StatCard value="98%" label="マッチング成功率" />
					</div>
				</div>
			</section>

			{/* サービス紹介セクション */}
			<section
				className="bg-background px-4 py-16 dark:bg-neutral-950 md:px-6 lg:px-8"
				id="services"
			>
				<div className="mx-auto max-w-7xl">
					<div className="mb-12 text-center">
						<h2 className="mb-4 text-3xl font-bold text-content-primary dark:text-neutral-100 md:text-4xl">
							高品質なソリューションを提供
						</h2>
						<p className="mx-auto max-w-2xl text-lg text-content-secondary dark:text-neutral-300">
							世界クラスのタレントとアジャイルチームが、複雑なビジネス課題を解決します。
						</p>
					</div>
					<div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-4">
						<div className="card-elevated text-center">
							<div className="mb-4 text-4xl">🔒</div>
							<h3 className="mb-2 text-xl font-semibold text-content-primary dark:text-neutral-100">
								セキュアなマッチング
							</h3>
							<p className="text-content-secondary dark:text-neutral-300">
								高度なセキュリティ機能により、安全に取引できます。
							</p>
						</div>
						<div className="card-elevated text-center">
							<div className="mb-4 text-4xl">🎯</div>
							<h3 className="mb-2 text-xl font-semibold text-content-primary dark:text-neutral-100">
								専門家との出会い
							</h3>
							<p className="text-content-secondary dark:text-neutral-300">
								サイバーセキュリティのプロフェッショナルが集結しています。
							</p>
						</div>
						<div className="card-elevated text-center">
							<div className="mb-4 text-4xl">⚡</div>
							<h3 className="mb-2 text-xl font-semibold text-content-primary dark:text-neutral-100">
								迅速な対応
							</h3>
							<p className="text-content-secondary dark:text-neutral-300">
								48時間以内に最適なタレントとマッチングできます。
							</p>
						</div>
						<div className="card-elevated text-center">
							<div className="mb-4 text-4xl">✅</div>
							<h3 className="mb-2 text-xl font-semibold text-content-primary dark:text-neutral-100">
								厳格な審査
							</h3>
							<p className="text-content-secondary dark:text-neutral-300">
								すべてのエキスパートが厳格な審査プロセスを通過しています。
							</p>
						</div>
					</div>
				</div>
			</section>

			{/* テスティモニアルセクション */}
			<section className="bg-background-surface px-4 py-16 dark:bg-neutral-900 md:px-6 lg:px-8">
				<div className="mx-auto max-w-7xl">
					<div className="mb-12 text-center">
						<h2 className="mb-4 text-3xl font-bold text-content-primary dark:text-neutral-100 md:text-4xl">
							お客様の満足度が最優先
						</h2>
						<p className="mx-auto max-w-2xl text-lg text-content-secondary dark:text-neutral-300">
							世界中のお客様が、重要なプロジェクトで成功を収めています。
						</p>
					</div>
					<div className="grid grid-cols-1 gap-8 md:grid-cols-3">
						{testimonials.map((testimonial, index) => (
							<TestimonialCard key={index} {...testimonial} />
						))}
					</div>
					<div className="mt-12 text-center">
						<div className="mb-4 text-2xl font-bold text-content-primary dark:text-neutral-100">
							平均評価 4.9 / 5.0
						</div>
						<p className="text-content-secondary dark:text-neutral-300">
							39,107件のレビューに基づく評価
						</p>
					</div>
				</div>
			</section>

			{/* 最終CTAセクション */}
			<section className="gradient-hero px-4 py-20 text-white dark:text-neutral-50 md:px-6 lg:px-8">
				<div className="mx-auto max-w-4xl text-center">
					<h2 className="mb-6 text-3xl font-bold md:text-4xl">
						準備はできましたか？
					</h2>
					<p className="mb-8 text-xl text-white/90">
						今すぐトップレベルのサイバーセキュリティタレントを見つけましょう。
					</p>
					<div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
						<Link href="/job-seeker/jobs">
							<TouchOptimizedButton
								variant="secondary"
								size="lg"
								className="bg-white text-brand-500 hover:bg-background-surface dark:bg-neutral-800 dark:text-brand-400 dark:hover:bg-neutral-700"
							>
								タレントを探す
							</TouchOptimizedButton>
						</Link>
						<Link href="/auth/signup">
							<TouchOptimizedButton
								variant="outline"
								size="lg"
								className="border-2 border-white text-white hover:bg-white/10 dark:border-neutral-300 dark:text-neutral-100 dark:hover:bg-neutral-800/50"
							>
								今すぐ始める
							</TouchOptimizedButton>
						</Link>
					</div>
				</div>
			</section>
		</div>
	);
}
