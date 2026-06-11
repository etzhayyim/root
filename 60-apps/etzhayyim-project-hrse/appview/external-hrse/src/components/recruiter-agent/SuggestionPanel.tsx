"use client";

import { TouchOptimizedButton } from "@/components/TouchOptimizedButton";
import type { Suggestion } from "@/gen/proto/hrse/v1/recruiter_agent_pb";

/**
 * @etzhayyim/etzhayyim-hrse#SuggestionPanel
 * Suggestion panel component for recruiter agent
 */

interface SuggestionPanelProps {
	suggestions: Suggestion[];
	onSuggestionClick?: (suggestion: Suggestion) => void;
	loading?: boolean;
}

export function SuggestionPanel({
	suggestions,
	onSuggestionClick,
	loading = false,
}: SuggestionPanelProps) {
	const getPriorityIcon = (priority: string) => {
		switch (priority) {
			case "high":
				return "🔥";
			case "medium":
				return "📧";
			case "low":
				return "💡";
			default:
				return "✨";
		}
	};

	const getPriorityColor = (priority: string) => {
		switch (priority) {
			case "high":
				return "border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-900/20";
			case "medium":
				return "border-yellow-200 bg-yellow-50 dark:border-yellow-900 dark:bg-yellow-900/20";
			case "low":
				return "border-green-200 bg-green-50 dark:border-green-900 dark:bg-green-900/20";
			default:
				return "border-neutral-200 bg-neutral-50 dark:border-neutral-800 dark:bg-neutral-900";
		}
	};

	if (loading) {
		return (
			<div className="rounded-lg border border-neutral-200 bg-white p-6 dark:border-neutral-800 dark:bg-neutral-900">
				<h2 className="mb-4 text-xl font-bold text-neutral-900 dark:text-neutral-100">
					おすすめアクション
				</h2>
				<div className="text-neutral-500 dark:text-neutral-400">
					読み込み中...
				</div>
			</div>
		);
	}

	return (
		<div className="rounded-lg border border-neutral-200 bg-white p-6 dark:border-neutral-800 dark:bg-neutral-900">
			<h2 className="mb-4 text-xl font-bold text-neutral-900 dark:text-neutral-100">
				おすすめアクション
			</h2>

			{suggestions.length === 0 ? (
				<div className="py-8 text-center text-neutral-500 dark:text-neutral-400">
					推奨アクションはありません
				</div>
			) : (
				<div className="space-y-3">
					{suggestions.map((suggestion) => (
						<div
							key={suggestion.id}
							className={`rounded-lg border p-4 transition-all hover:shadow-md ${getPriorityColor(
								suggestion.priority
							)}`}
						>
							<div className="mb-2 flex items-start gap-2">
								<span className="text-2xl">
									{getPriorityIcon(suggestion.priority)}
								</span>
								<div className="flex-1">
									<h3 className="mb-1 font-semibold text-neutral-900 dark:text-neutral-100">
										{suggestion.title}
									</h3>
									<p className="mb-2 text-sm text-neutral-600 dark:text-neutral-400">
										{suggestion.description}
									</p>
									<p className="text-xs text-neutral-500 dark:text-neutral-400">
										理由: {suggestion.reason}
									</p>
								</div>
							</div>
							{suggestion.actionUrl && (
								<TouchOptimizedButton
									variant="primary"
									size="sm"
									onClick={() => {
										if (onSuggestionClick) {
											onSuggestionClick(suggestion);
										} else if (suggestion.actionUrl) {
											window.location.href = suggestion.actionUrl;
										}
									}}
									className="w-full"
								>
									アクションを実行
								</TouchOptimizedButton>
							)}
						</div>
					))}
				</div>
			)}
		</div>
	);
}
