"use client";

interface BasicInfoStepProps {
	title: string;
	description: string;
	jobLocation: string;
	startDate: string;
	endDate: string;
	onChange: (field: string, value: string) => void;
}

/**
 * ステップ2: 基本情報入力
 */
export function BasicInfoStep({
	title,
	description,
	jobLocation,
	startDate,
	endDate,
	onChange,
}: BasicInfoStepProps) {
	return (
		<div className="space-y-6">
			<div>
				<h2 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">基本情報</h2>
				<p className="mt-2 text-sm text-neutral-600 dark:text-neutral-400">
					求人のタイトル、説明、勤務地、期間を入力してください。
				</p>
			</div>

			<div className="space-y-4">
				<div>
					<label
						htmlFor="title"
						className="block text-sm font-medium text-neutral-700 dark:text-neutral-300"
					>
						タイトル <span className="text-red-500 dark:text-red-400">*</span>
					</label>
					<input
						id="title"
						type="text"
						value={title}
						onChange={(e) => onChange("title", e.target.value)}
						className="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-brand-500 dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100"
						required
					/>
				</div>

				<div>
					<label
						htmlFor="description"
						className="block text-sm font-medium text-neutral-700 dark:text-neutral-300"
					>
						説明 <span className="text-red-500 dark:text-red-400">*</span>
					</label>
					<textarea
						id="description"
						value={description}
						onChange={(e) => onChange("description", e.target.value)}
						rows={8}
						className="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-brand-500 dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100"
						required
					/>
				</div>

				<div>
					<label
						htmlFor="jobLocation"
						className="block text-sm font-medium text-neutral-700 dark:text-neutral-300"
					>
						勤務地 <span className="text-red-500 dark:text-red-400">*</span>
					</label>
					<input
						id="jobLocation"
						type="text"
						value={jobLocation}
						onChange={(e) => onChange("jobLocation", e.target.value)}
						placeholder="例: 東京都、リモート可"
						className="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-brand-500 dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100"
						required
					/>
				</div>

				<div className="grid grid-cols-1 gap-4 md:grid-cols-2">
					<div>
						<label
							htmlFor="startDate"
							className="block text-sm font-medium text-neutral-700 dark:text-neutral-300"
						>
							開始日
						</label>
						<input
							id="startDate"
							type="date"
							value={startDate}
							onChange={(e) => onChange("startDate", e.target.value)}
							className="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-brand-500 dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100"
						/>
					</div>
					<div>
						<label
							htmlFor="endDate"
							className="block text-sm font-medium text-neutral-700 dark:text-neutral-300"
						>
							終了日
						</label>
						<input
							id="endDate"
							type="date"
							value={endDate}
							onChange={(e) => onChange("endDate", e.target.value)}
							className="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-brand-500 dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100"
						/>
					</div>
				</div>
			</div>
		</div>
	);
}
