"use client";

interface ConditionsStepProps {
	unitPriceMin: string;
	unitPriceMax: string;
	remoteAllowed: boolean;
	recommendedUnitPriceMin: string | null;
	recommendedUnitPriceMax: string | null;
	onChange: (field: string, value: string | boolean) => void;
	onApplyRecommendedPrice: () => void;
}

/**
 * ステップ4: 条件設定
 */
export function ConditionsStep({
	unitPriceMin,
	unitPriceMax,
	remoteAllowed,
	recommendedUnitPriceMin,
	recommendedUnitPriceMax,
	onChange,
	onApplyRecommendedPrice,
}: ConditionsStepProps) {
	const hasRecommendedPrice =
		recommendedUnitPriceMin !== null &&
		recommendedUnitPriceMax !== null;
	const recommendedPriceApplied =
		hasRecommendedPrice &&
		unitPriceMin === recommendedUnitPriceMin &&
		unitPriceMax === recommendedUnitPriceMax;

	return (
		<div className="space-y-6">
			<div>
				<h2 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">条件設定</h2>
				<p className="mt-2 text-sm text-neutral-600 dark:text-neutral-400">
					単価範囲とリモート可否を設定してください。
				</p>
			</div>

			<div className="space-y-4">
				<div>
					<label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">
						単価範囲（円/月） <span className="text-red-500 dark:text-red-400">*</span>
					</label>
					{hasRecommendedPrice && !recommendedPriceApplied && (
						<div className="mt-2 rounded-lg border border-brand-200 bg-brand-50 p-3 dark:border-brand-800 dark:bg-brand-900/20">
							<div className="flex items-center justify-between">
								<div>
									<p className="text-sm font-medium text-brand-900 dark:text-brand-100">
										推奨単価範囲
									</p>
									<p className="text-sm text-brand-700 dark:text-brand-300">
										{Number.parseInt(recommendedUnitPriceMin!).toLocaleString()}円
										〜 {Number.parseInt(recommendedUnitPriceMax!).toLocaleString()}
										円/月
									</p>
								</div>
								<button
									type="button"
									onClick={onApplyRecommendedPrice}
									className="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600"
								>
									適用
								</button>
							</div>
						</div>
					)}
					<div className="mt-2 grid grid-cols-2 gap-4">
						<div>
							<label
								htmlFor="unitPriceMin"
								className="block text-xs text-neutral-600 dark:text-neutral-400"
							>
								最小
							</label>
							<input
								id="unitPriceMin"
								type="number"
								value={unitPriceMin}
								onChange={(e) => onChange("unitPriceMin", e.target.value)}
								min="0"
								step="10000"
								className="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-brand-500 dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100"
								required
							/>
						</div>
						<div>
							<label
								htmlFor="unitPriceMax"
								className="block text-xs text-neutral-600 dark:text-neutral-400"
							>
								最大
							</label>
							<input
								id="unitPriceMax"
								type="number"
								value={unitPriceMax}
								onChange={(e) => onChange("unitPriceMax", e.target.value)}
								min="0"
								step="10000"
								className="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-brand-500 dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100"
								required
							/>
						</div>
					</div>
				</div>

				<div>
					<label
						htmlFor="remoteAllowed"
						className="block text-sm font-medium text-neutral-700 dark:text-neutral-300"
					>
						リモート許可 <span className="text-red-500 dark:text-red-400">*</span>
					</label>
					<select
						id="remoteAllowed"
						value={remoteAllowed.toString()}
						onChange={(e) =>
							onChange("remoteAllowed", e.target.value === "true")
						}
						className="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-brand-500 dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100"
						required
					>
						<option value="true">可</option>
						<option value="false">不可</option>
					</select>
				</div>
			</div>
		</div>
	);
}
