"use client";

import { useCallback } from "react";

interface NeedType {
	id: string;
	nameJa: string;
	descriptionJa: string | null;
	icon: string | null;
}

interface NeedTypeStepProps {
	needTypes: NeedType[];
	selectedNeedTypeId: string | null;
	onSelect: (needTypeId: string) => void;
}

/**
 * ステップ1: ニーズタイプ選択
 */
export function NeedTypeStep({
	needTypes,
	selectedNeedTypeId,
	onSelect,
}: NeedTypeStepProps) {
	const handleSelect = useCallback(
		(needTypeId: string) => {
			onSelect(needTypeId);
		},
		[onSelect],
	);

	if (needTypes.length === 0) {
		return (
			<div className="space-y-6">
				<div>
					<h2 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
						ニーズタイプを選択
					</h2>
					<p className="mt-2 text-sm text-neutral-600 dark:text-neutral-400">
						現在選択可能なニーズタイプがありません。直接入力に進んでください。
					</p>
				</div>
			</div>
		);
	}

	return (
		<div className="space-y-6">
			<div>
				<h2 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
					どのようなニーズがありますか？
				</h2>
				<p className="mt-2 text-sm text-neutral-600 dark:text-neutral-400">
					サイバーセキュリティの専門領域から、ご希望のニーズタイプを選択してください。
				</p>
			</div>

			<div className="grid grid-cols-1 gap-4 md:grid-cols-2">
				{needTypes.map((needType) => {
					const isSelected = selectedNeedTypeId === needType.id;
					return (
						<button
							key={needType.id}
							type="button"
							onClick={() => handleSelect(needType.id)}
							className={`rounded-lg border-2 p-6 text-left transition-all ${
								isSelected
									? "border-brand-600 bg-brand-50 shadow-md dark:border-brand-500 dark:bg-brand-900/20"
									: "border-neutral-200 bg-white hover:border-neutral-300 hover:shadow-sm dark:border-neutral-700 dark:bg-neutral-800 dark:hover:border-neutral-600"
							}`}
						>
							<div className="flex items-start justify-between">
								<div className="flex-1">
									<h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
										{needType.nameJa}
									</h3>
									{needType.descriptionJa && (
										<p className="mt-2 text-sm text-neutral-600 dark:text-neutral-400">
											{needType.descriptionJa}
										</p>
									)}
								</div>
								<div
									className={`ml-4 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-2 ${
										isSelected
											? "border-brand-600 bg-brand-600 dark:border-brand-500 dark:bg-brand-500"
											: "border-neutral-300 dark:border-neutral-600"
									}`}
								>
									{isSelected && (
										<svg
											className="h-4 w-4 text-white"
											fill="none"
											viewBox="0 0 24 24"
											stroke="currentColor"
										>
											<path
												strokeLinecap="round"
												strokeLinejoin="round"
												strokeWidth={2}
												d="M5 13l4 4L19 7"
											/>
										</svg>
									)}
								</div>
							</div>
						</button>
					);
				})}
			</div>
		</div>
	);
}
