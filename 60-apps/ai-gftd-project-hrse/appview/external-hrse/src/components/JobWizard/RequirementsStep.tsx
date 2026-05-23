"use client";

import { MultiSelect } from "@/components/MultiSelect";

interface Option {
	id: string;
	name: string;
}

interface RequirementsStepProps {
	specializations: Option[];
	certifications: Option[];
	languages: Option[];
	selectedSpecializationIds: string[];
	selectedCertificationIds: string[];
	selectedLanguageIds: string[];
	recommendedSpecializationIds: string[];
	recommendedCertificationIds: string[];
	onChange: (
		field: "specializations" | "certifications" | "languages",
		ids: string[],
	) => void;
	onApplyRecommendations: () => void;
}

/**
 * ステップ3: 要件設定
 */
export function RequirementsStep({
	specializations,
	certifications,
	languages,
	selectedSpecializationIds,
	selectedCertificationIds,
	selectedLanguageIds,
	recommendedSpecializationIds,
	recommendedCertificationIds,
	onChange,
	onApplyRecommendations,
}: RequirementsStepProps) {
	const hasRecommendations =
		recommendedSpecializationIds.length > 0 ||
		recommendedCertificationIds.length > 0;
	const recommendationsApplied =
		recommendedSpecializationIds.every((id) =>
			selectedSpecializationIds.includes(id),
		) &&
		recommendedCertificationIds.every((id) =>
			selectedCertificationIds.includes(id),
		);

	return (
		<div className="space-y-6">
			<div>
				<h2 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">要件設定</h2>
				<p className="mt-2 text-sm text-neutral-600 dark:text-neutral-400">
					必要な専門分野、資格、言語を選択してください。推奨設定が自動的に提案されます。
				</p>
			</div>

			{hasRecommendations && !recommendationsApplied && (
				<div className="rounded-lg border border-brand-200 bg-brand-50 p-4 dark:border-brand-800 dark:bg-brand-900/20">
					<div className="flex items-start justify-between">
						<div className="flex-1">
							<h3 className="text-sm font-semibold text-brand-900 dark:text-brand-100">
								推奨設定が利用可能です
							</h3>
							<p className="mt-1 text-sm text-brand-700 dark:text-brand-300">
								選択したニーズタイプに基づいて、推奨される専門分野と資格が提案されています。
							</p>
						</div>
						<button
							type="button"
							onClick={onApplyRecommendations}
							className="ml-4 rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600"
						>
							推奨設定を適用
						</button>
					</div>
				</div>
			)}

			<div className="space-y-4">
				<MultiSelect
					label="専門分野"
					options={specializations}
					selectedIds={selectedSpecializationIds}
					onChange={(ids) => onChange("specializations", ids)}
				/>

				<MultiSelect
					label="資格"
					options={certifications}
					selectedIds={selectedCertificationIds}
					onChange={(ids) => onChange("certifications", ids)}
				/>

				<MultiSelect
					label="言語"
					options={languages}
					selectedIds={selectedLanguageIds}
					onChange={(ids) => onChange("languages", ids)}
					required
				/>
			</div>
		</div>
	);
}
