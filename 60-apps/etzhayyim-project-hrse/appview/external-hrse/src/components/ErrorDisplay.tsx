"use client";

interface ErrorDisplayProps {
	error: Error | string | null;
	onDismiss?: () => void;
}

export function ErrorDisplay({ error, onDismiss }: ErrorDisplayProps) {
	if (!error) return null;

	const message = typeof error === "string" ? error : error.message;

	return (
		<div className="mb-4 rounded-md bg-red-50 p-4 border border-red-200">
			<div className="flex items-start">
				<svg
					className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
				>
					<path
						strokeLinecap="round"
						strokeLinejoin="round"
						strokeWidth={2}
						d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
					/>
				</svg>
				<div className="ml-3 flex-1">
					<p className="text-sm font-medium text-red-800">{message}</p>
				</div>
				{onDismiss && (
					<button
						type="button"
						onClick={onDismiss}
						className="ml-4 text-red-600 hover:text-red-800 min-h-[44px] min-w-[44px] flex items-center justify-center"
						aria-label="エラーを閉じる"
					>
						<svg
							className="h-5 w-5"
							fill="none"
							stroke="currentColor"
							viewBox="0 0 24 24"
						>
							<path
								strokeLinecap="round"
								strokeLinejoin="round"
								strokeWidth={2}
								d="M6 18L18 6M6 6l12 12"
							/>
						</svg>
					</button>
				)}
			</div>
		</div>
	);
}






