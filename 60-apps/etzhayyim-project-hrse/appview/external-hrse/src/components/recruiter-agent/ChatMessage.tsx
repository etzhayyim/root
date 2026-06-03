"use client";

import type { ReactNode } from "react";

/**
 * @etzhayyim/etzhayyim-hrse#ChatMessage
 * Chat message component for recruiter agent
 */
interface ChatMessageProps {
	role: "user" | "assistant";
	content: string;
	timestamp?: Date;
}

export function ChatMessage({ role, content, timestamp }: ChatMessageProps) {
	const isUser = role === "user";

	return (
		<div
			className={`mb-4 flex ${isUser ? "justify-end" : "justify-start"}`}
		>
			<div
				className={`max-w-[80%] rounded-lg px-4 py-3 ${
					isUser
						? "bg-brand-600 text-white dark:bg-brand-500"
						: "bg-neutral-100 text-neutral-900 dark:bg-neutral-800 dark:text-neutral-100"
				}`}
			>
				<p className="text-sm leading-relaxed">{content}</p>
				{timestamp && (
					<p
						className={`mt-1 text-xs ${
							isUser
								? "text-brand-100"
								: "text-neutral-500 dark:text-neutral-400"
						}`}
					>
						{timestamp.toLocaleTimeString("ja-JP", {
							hour: "2-digit",
							minute: "2-digit",
						})}
					</p>
				)}
			</div>
		</div>
	);
}
