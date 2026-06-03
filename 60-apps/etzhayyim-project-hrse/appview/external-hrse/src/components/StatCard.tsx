/**
 * @etzhayyim/cyber-freelance#StatCard
 * 統計データ表示カード
 * Toptalスタイルの統計カード
 */
interface StatCardProps {
	value: string | number;
	label: string;
	description?: string;
}

export function StatCard({ value, label, description }: StatCardProps) {
	return (
		<div className="flex flex-col items-center text-center">
			<div className="mb-2 text-4xl font-bold text-brand-500 dark:text-brand-400 md:text-5xl">
				{value}
			</div>
			<div className="mb-1 text-lg font-semibold text-content-primary dark:text-neutral-100">{label}</div>
			{description && (
				<div className="text-sm text-content-secondary dark:text-neutral-300">{description}</div>
			)}
		</div>
	);
}

