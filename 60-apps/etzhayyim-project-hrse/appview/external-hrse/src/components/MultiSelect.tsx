"use client";

/**
 * マルチセレクトコンポーネント（タグ+Checkbox形式）
 * iPad最適化（タッチ操作対応）
 */
interface MultiSelectProps {
	label: string;
	options: Array<{ id: string; name: string }>;
	selectedIds: string[];
	onChange: (selectedIds: string[]) => void;
	required?: boolean;
}

export function MultiSelect({
	label,
	options,
	selectedIds,
	onChange,
	required = false,
}: MultiSelectProps) {
	const toggleOption = (id: string) => {
		if (selectedIds.includes(id)) {
			onChange(selectedIds.filter((selectedId) => selectedId !== id));
		} else {
			onChange([...selectedIds, id]);
		}
	};

	const id = `multiselect-${label.replace(/\s+/g, "-").toLowerCase()}`;

	return (
		<div>
			<label
				htmlFor={id}
				className="block text-sm font-medium text-content-primary mb-3 dark:text-neutral-300"
			>
				{label}
				{required && <span className="text-error-500 dark:text-error-400">*</span>}
			</label>
			<div
				id={id}
				className="flex flex-wrap gap-2"
				role="group"
				aria-label={label}
			>
				{options.map((option) => {
					const isSelected = selectedIds.includes(option.id);
					const optionId = `${id}-${option.id}`;

					return (
						<label
							key={option.id}
							htmlFor={optionId}
							className={`inline-flex min-h-[44px] cursor-pointer items-center gap-2 rounded-md border px-4 py-2.5 text-sm font-medium transition-all ${
								isSelected
									? "border-brand-500 bg-brand-50 text-brand-500 shadow-sm dark:bg-brand-900 dark:text-brand-400 dark:border-brand-500"
									: "border-border bg-background text-content-primary hover:border-brand-500 hover:bg-background-surface dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-100 dark:hover:border-brand-500 dark:hover:bg-neutral-700"
							}`}
						>
							<input
								id={optionId}
								type="checkbox"
								checked={isSelected}
								onChange={() => toggleOption(option.id)}
								className="h-4 w-4 rounded border-border text-brand-500 focus:ring-2 focus:ring-brand-500 focus:ring-offset-0 checked:bg-brand-500 checked:border-brand-500 dark:border-neutral-600 dark:bg-neutral-700 dark:checked:bg-brand-500 dark:checked:border-brand-500"
								aria-label={option.name}
							/>
							<span className="select-none">{option.name}</span>
						</label>
					);
				})}
			</div>
			{selectedIds.length > 0 && (
				<p className="mt-2 text-xs text-content-secondary dark:text-neutral-400">
					{selectedIds.length}個選択中
				</p>
			)}
		</div>
	);
}
