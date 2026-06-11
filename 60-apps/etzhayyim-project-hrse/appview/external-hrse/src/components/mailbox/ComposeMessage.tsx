"use client";

import { useState } from "react";
import { useMailboxServiceClient } from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import {
	SendMessageRequestSchema,
	GetLLMSuggestionRequestSchema,
} from "@/gen/proto/hrse/v1/mailbox_pb";
import { TouchOptimizedButton } from "@/components/TouchOptimizedButton";

/**
 * @etzhayyim/etzhayyim-hrse#ComposeMessage
 * Message composer component for mailbox
 */
interface ComposeMessageProps {
	threadId: string;
	toEmail: string;
	onMessageSent?: () => void;
	onUseSuggestion?: (subject: string, bodyHtml: string, bodyText: string) => void;
}

export function ComposeMessage({
	threadId,
	toEmail,
	onMessageSent,
	onUseSuggestion,
}: ComposeMessageProps) {
	const [subject, setSubject] = useState("");
	const [bodyHtml, setBodyHtml] = useState("");
	const [bodyText, setBodyText] = useState("");
	const [suggestion, setSuggestion] = useState<{
		subject: string;
		bodyHtml: string;
		bodyText: string;
		reasoning: string;
	} | null>(null);
	const [loading, setLoading] = useState(false);
	const [suggestionLoading, setSuggestionLoading] = useState(false);

	const client = useMailboxServiceClient();

	const handleGetSuggestion = async () => {
		try {
			setSuggestionLoading(true);
			const response = await client.getLLMSuggestion(
				create(GetLLMSuggestionRequestSchema, { threadId }),
			);
			if (response.suggestion) {
				setSuggestion({
					subject: response.suggestion.suggestedSubject,
					bodyHtml: response.suggestion.suggestedBodyHtml,
					bodyText: response.suggestion.suggestedBodyText,
					reasoning: response.suggestion.reasoning,
				});
			}
		} catch (err) {
			console.error("Failed to get suggestion:", err);
		} finally {
			setSuggestionLoading(false);
		}
	};

	const handleUseSuggestion = () => {
		if (suggestion) {
			setSubject(suggestion.subject);
			setBodyHtml(suggestion.bodyHtml);
			setBodyText(suggestion.bodyText);
			onUseSuggestion?.(
				suggestion.subject,
				suggestion.bodyHtml,
				suggestion.bodyText,
			);
		}
	};

	const handleSend = async () => {
		if (!subject.trim() || (!bodyHtml.trim() && !bodyText.trim()) || loading) {
			return;
		}

		try {
			setLoading(true);
			await client.sendMessage(
				create(SendMessageRequestSchema, {
					threadId,
					toEmail,
					subject: subject.trim(),
					bodyHtml: bodyHtml.trim() || undefined,
					bodyText: bodyText.trim() || undefined,
				}),
			);

			// Reset form
			setSubject("");
			setBodyHtml("");
			setBodyText("");
			setSuggestion(null);

			onMessageSent?.();
		} catch (err) {
			console.error("Failed to send message:", err);
			alert("メッセージの送信に失敗しました");
		} finally {
			setLoading(false);
		}
	};

	const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
		if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
			e.preventDefault();
			handleSend();
		}
	};

	return (
		<div className="border-t border-neutral-200 p-4 dark:border-neutral-800">
			{/* LLM Suggestion */}
			{suggestion && (
				<div className="mb-4 rounded-lg border border-brand-200 bg-brand-50 p-3 dark:border-brand-800 dark:bg-brand-900/20">
					<div className="mb-2 flex items-center justify-between">
						<h4 className="text-sm font-semibold">AI提案</h4>
						<TouchOptimizedButton
							onClick={handleUseSuggestion}
							className="text-xs"
							size="sm"
						>
							使用
						</TouchOptimizedButton>
					</div>
					<p className="mb-2 text-xs text-neutral-600 dark:text-neutral-400">
						{suggestion.reasoning}
					</p>
					<div className="text-xs">
						<p className="font-medium">件名: {suggestion.subject}</p>
						<p className="mt-1 line-clamp-2">{suggestion.bodyText}</p>
					</div>
				</div>
			)}

			{/* Compose form */}
			<div className="space-y-3">
				<input
					type="text"
					value={subject}
					onChange={(e) => setSubject(e.target.value)}
					placeholder="件名"
					className="w-full rounded-lg border border-neutral-300 bg-white px-4 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100"
					disabled={loading}
				/>
				<textarea
					value={bodyText}
					onChange={(e) => {
						setBodyText(e.target.value);
						// Simple HTML conversion for display
						setBodyHtml(e.target.value.replace(/\n/g, "<br>"));
					}}
					onKeyPress={handleKeyPress}
					placeholder="メッセージを入力... (Cmd/Ctrl+Enter で送信)"
					className="w-full resize-none rounded-lg border border-neutral-300 bg-white px-4 py-3 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100"
					rows={4}
					disabled={loading}
				/>
				<div className="flex items-center justify-between">
					<TouchOptimizedButton
						onClick={handleGetSuggestion}
						disabled={suggestionLoading}
						variant="outline"
						size="sm"
					>
						{suggestionLoading ? "生成中..." : "AI提案を取得"}
					</TouchOptimizedButton>
					<TouchOptimizedButton
						onClick={handleSend}
						disabled={!subject.trim() || (!bodyHtml.trim() && !bodyText.trim()) || loading}
					>
						{loading ? "送信中..." : "送信"}
					</TouchOptimizedButton>
				</div>
			</div>
		</div>
	);
}

