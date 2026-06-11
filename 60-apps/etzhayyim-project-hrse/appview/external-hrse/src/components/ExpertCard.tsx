import Image from "next/image";

/**
 * @etzhayyim/cyber-freelance#ExpertCard
 * 検証済みエキスパートプロフィールカード
 * Toptalスタイルのエキスパートカード表示
 */
interface ExpertCardProps {
	name: string;
	title: string;
	specialization: string;
	previousCompany?: string;
	avatarUrl?: string;
	verified?: boolean;
}

export function ExpertCard({
	name,
	title,
	specialization,
	previousCompany,
	avatarUrl,
	verified = true,
}: ExpertCardProps) {
	return (
		<div className="card-interactive flex flex-col dark:bg-neutral-900 dark:border dark:border-neutral-800 dark:shadow-neutral-950/50">
			{/* アバター */}
			<div className="mb-4 flex items-center space-x-4">
				<div className="relative h-16 w-16 overflow-hidden rounded-full bg-background-surface dark:bg-neutral-800 dark:border dark:border-neutral-700">
					{avatarUrl ? (
						<Image
							src={avatarUrl}
							alt={name}
							fill
							className="object-cover"
						/>
					) : (
						<div className="flex h-full w-full items-center justify-center bg-brand-50 text-brand-500 dark:bg-brand-900/30 dark:text-brand-400">
							<span className="text-xl font-semibold">
								{name.charAt(0).toUpperCase()}
							</span>
						</div>
					)}
				</div>
				<div className="flex-1">
					<div className="flex items-center space-x-2">
						<h3 className="font-semibold text-content-primary dark:text-neutral-100">{name}</h3>
						{verified && (
							<span className="rounded-full bg-success-100 px-2 py-0.5 text-xs font-medium text-success-700 dark:bg-success-900/30 dark:text-success-400">
								検証済み
							</span>
						)}
					</div>
					<p className="text-sm text-content-secondary dark:text-neutral-300">{title}</p>
				</div>
			</div>

			{/* 専門分野 */}
			<div className="mb-2">
				<span className="inline-block rounded-md bg-brand-50 px-3 py-1 text-sm font-medium text-brand-500 dark:bg-brand-900/30 dark:text-brand-400">
					{specialization}
				</span>
			</div>

			{/* 以前の勤務先 */}
			{previousCompany && (
				<div className="mt-auto pt-4 text-sm text-content-secondary dark:text-neutral-400">
					以前: {previousCompany}
				</div>
			)}
		</div>
	);
}

