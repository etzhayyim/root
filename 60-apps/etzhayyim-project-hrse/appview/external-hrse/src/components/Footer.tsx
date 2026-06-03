import Link from "next/link";

/**
 * @etzhayyim/cyber-freelance#Footer
 * Toptalスタイルのフッターコンポーネント
 */
export function Footer() {
	return (
		<footer className="bg-white text-neutral-700 dark:bg-neutral-950 dark:text-neutral-300 border-t border-neutral-200 dark:border-t dark:border-neutral-900 safe-area-bottom">
			<div className="mx-auto max-w-7xl px-4 py-12 md:px-6 lg:px-8">
				<div className="grid grid-cols-1 gap-8 md:grid-cols-4">
					{/* ブランドセクション */}
					<div className="space-y-4">
						<div className="flex items-center space-x-2">
							<div className="flex h-10 w-10 items-center justify-center rounded-md bg-brand-500 text-white">
								<span className="text-xl font-bold">CF</span>
							</div>
							<span className="text-xl font-bold text-neutral-900 dark:text-white">
								etzhayyim HRSE
							</span>
						</div>
						<p className="text-sm text-neutral-600 dark:text-neutral-400">
							サイバーセキュリティ特化型
							<br />
							フリーランスマッチングプラットフォーム
						</p>
					</div>

					{/* リンクセクション */}
					<div>
						<h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-neutral-900 dark:text-white">
							求職者
						</h3>
						<ul className="space-y-2">
							<li>
								<Link
									href="/job-seeker/jobs"
									className="text-sm text-neutral-600 transition-colors hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white"
								>
									案件を探す
								</Link>
							</li>
							<li>
								<Link
									href="/job-seeker/profile"
									className="text-sm text-neutral-600 transition-colors hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white"
								>
									プロファイル作成
								</Link>
							</li>
							<li>
								<Link
									href="/job-seeker/proposals"
									className="text-sm text-neutral-600 transition-colors hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white"
								>
									応募管理
								</Link>
							</li>
						</ul>
					</div>

					<div>
						<h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-neutral-900 dark:text-white">
							エージェンシー
						</h3>
						<ul className="space-y-2">
							<li>
								<Link
									href="/agency/profile"
									className="text-sm text-neutral-600 transition-colors hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white"
								>
									エージェンシー登録
								</Link>
							</li>
							<li>
								<Link
									href="/agency/matching"
									className="text-sm text-neutral-600 transition-colors hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white"
								>
									マッチング
								</Link>
							</li>
						</ul>
					</div>

					<div>
						<h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-neutral-900 dark:text-white">
							サポート
						</h3>
						<ul className="space-y-2">
							<li>
								<Link
									href="https://etzhayyim.com/about"
									className="text-sm text-neutral-600 transition-colors hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white"
								>
									会社概要
								</Link>
							</li>
							<li>
								<Link
									href="https://etzhayyim.com/contact"
									className="text-sm text-neutral-600 transition-colors hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white"
								>
									お問い合わせ
								</Link>
							</li>
							<li>
								<Link
									href="https://etzhayyim.com/g1nSERUt/privacypolicy"
									className="text-sm text-neutral-600 transition-colors hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white"
								>
									プライバシーポリシー
								</Link>
							</li>
							<li>
								<Link
									href="https://etzhayyim.com/g1nSERUt/csfm_termsofservice"
									className="text-sm text-neutral-600 transition-colors hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white"
								>
									利用規約
								</Link>
							</li>
						</ul>
					</div>
				</div>

				{/* ソーシャルメディア */}
				<div className="mt-8 border-t border-neutral-200 dark:border-neutral-900 pt-8">
					<div className="flex flex-col items-center justify-between space-y-4 md:flex-row">
						<p className="text-sm text-neutral-600 dark:text-neutral-400">
							© {new Date().getFullYear()} etzhayyim HRSE. All
							rights reserved.
						</p>
						<div className="flex space-x-6">
						<a
							href="https://x.com/etzhayyimjapan"
							className="text-neutral-600 transition-colors hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white"
							aria-label="X"
						>
							<svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
								<path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
							</svg>
						</a>
							<a
								href="https://www.linkedin.com/company/etzhayyimjapan"
								className="text-neutral-600 transition-colors hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white"
								aria-label="LinkedIn"
							>
								<svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
									<path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
								</svg>
							</a>
						</div>
					</div>
				</div>
			</div>
		</footer>
	);
}
