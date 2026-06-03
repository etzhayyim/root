import Image from "next/image";

/**
 * @etzhayyim/cyber-freelance#TestimonialCard
 * テスティモニアルカード
 * Toptalスタイルのクライアントの声表示
 */
interface TestimonialCardProps {
	quote: string;
	authorName: string;
	authorTitle: string;
	companyName?: string;
	companyLogo?: string;
	avatarUrl?: string;
}

export function TestimonialCard({
	quote,
	authorName,
	authorTitle,
	companyName,
	companyLogo,
	avatarUrl,
}: TestimonialCardProps) {
	return (
		<div className="card-elevated flex h-full flex-col dark:bg-neutral-900 dark:border dark:border-neutral-800 dark:shadow-neutral-950/50">
			{/* 引用 */}
			<div className="mb-6 flex-1">
				<svg
					className="mb-4 h-8 w-8 text-brand-300 dark:text-brand-500"
					fill="currentColor"
					viewBox="0 0 32 32"
				>
					<path d="M10 8c-3.3 0-6 2.7-6 6v10h10V14H8c0-1.1.9-2 2-2V8zm16 0c-3.3 0-6 2.7-6 6v10h10V14h-6c0-1.1.9-2 2-2V8z" />
				</svg>
				<p className="text-lg leading-relaxed text-content-primary dark:text-neutral-200">{quote}</p>
			</div>

			{/* 著者情報 */}
			<div className="flex items-center space-x-4 border-t border-border pt-6 dark:border-neutral-800">
				{authorName && (
					<div className="relative h-12 w-12 overflow-hidden rounded-full bg-background-surface dark:bg-neutral-800 dark:border dark:border-neutral-700">
						{avatarUrl ? (
							<Image
								src={avatarUrl}
								alt={authorName}
								fill
								className="object-cover"
							/>
						) : (
							<div className="flex h-full w-full items-center justify-center bg-brand-50 text-brand-500 dark:bg-brand-900/30 dark:text-brand-400">
								<span className="text-lg font-semibold">
									{authorName.charAt(0).toUpperCase()}
								</span>
							</div>
						)}
					</div>
				)}
				<div className="flex-1">
					{authorName && (
						<div className="font-semibold text-content-primary dark:text-neutral-100">{authorName}</div>
					)}
					<div className="text-sm text-content-secondary dark:text-neutral-300">{authorTitle}</div>
					{companyName && (
						<div className="mt-1 flex items-center space-x-2">
							{companyLogo && (
								<div className="relative h-4 w-4">
									<Image
										src={companyLogo}
										alt={companyName}
										fill
										className="object-contain"
									/>
								</div>
							)}
							<span className="text-sm text-content-secondary dark:text-neutral-400">{companyName}</span>
						</div>
					)}
				</div>
			</div>
		</div>
	);
}

