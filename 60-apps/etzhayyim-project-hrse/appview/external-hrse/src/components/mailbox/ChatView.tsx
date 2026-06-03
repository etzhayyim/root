"use client";

import { useEffect, useState, useRef } from "react";
import { useMailboxServiceClient } from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import {
	ListMessagesRequestSchema,
	MailboxMessage,
	GetThreadRequestSchema,
	MessageThread,
} from "@/gen/proto/hrse/v1/mailbox_pb";

/**
 * @etzhayyim/etzhayyim-hrse#ChatView
 * Chat-style message view component
 */
interface ChatViewProps {
	threadId: string;
	onSendMessage?: () => void;
}

export function ChatView({ threadId, onSendMessage }: ChatViewProps) {
	const [thread, setThread] = useState<MessageThread | null>(null);
	const [messages, setMessages] = useState<MailboxMessage[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const messagesEndRef = useRef<HTMLDivElement>(null);
	const client = useMailboxServiceClient();

	useEffect(() => {
		if (threadId) {
			loadThread();
			loadMessages();
		}
	}, [threadId]);

	useEffect(() => {
		messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
	}, [messages]);

	const loadThread = async () => {
		try {
			const response = await client.getThread(
				create(GetThreadRequestSchema, { id: threadId }),
			);
			setThread(response.thread ?? null);
		} catch (err) {
			console.error("Failed to load thread:", err);
		}
	};

	const loadMessages = async () => {
		try {
			setLoading(true);
			const response = await client.listMessages(
				create(ListMessagesRequestSchema, {
					threadId,
					limit: 100,
					offset: 0,
				}),
			);
			setMessages(response.messages);
			setError(null);
		} catch (err) {
			console.error("Failed to load messages:", err);
			setError("メッセージの読み込みに失敗しました");
		} finally {
			setLoading(false);
		}
	};

	const formatDate = (timestamp: any) => {
		if (!timestamp) return "";
		const date = new Date(timestamp.seconds * 1000);
		return date.toLocaleString("ja-JP", {
			month: "short",
			day: "numeric",
			hour: "2-digit",
			minute: "2-digit",
		});
	};

	const isOutbound = (direction: string) => direction === "outbound";

	if (loading && messages.length === 0) {
		return (
			<div className="flex h-full items-center justify-center">
				<p className="text-neutral-500 dark:text-neutral-400">読み込み中...</p>
			</div>
		);
	}

	if (error) {
		return (
			<div className="flex h-full items-center justify-center">
				<p className="text-red-500">{error}</p>
			</div>
		);
	}

	return (
		<div className="flex h-full flex-col">
			{/* Thread header */}
			{thread && (
				<div className="border-b border-neutral-200 p-4 dark:border-neutral-800">
					<h2 className="text-lg font-semibold">{thread.subject}</h2>
					<div className="mt-2 flex items-center gap-2">
						{thread.classification && (
							<span
								className={`inline-block rounded-full px-2 py-1 text-xs font-medium ${
									thread.classification === "talent"
										? "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
										: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
								}`}
							>
								{thread.classification === "talent" ? "人材" : "案件"}
							</span>
						)}
						{thread.assignedTo && (
							<span className="text-sm text-neutral-500 dark:text-neutral-400">
								担当: {thread.assignedTo}
							</span>
						)}
					</div>
				</div>
			)}

			{/* Messages area */}
			<div className="flex-1 overflow-y-auto p-4">
				{messages.length === 0 ? (
					<div className="flex h-full items-center justify-center">
						<p className="text-neutral-500 dark:text-neutral-400">
							メッセージがありません
						</p>
					</div>
				) : (
					<div className="space-y-4">
						{messages.map((message) => {
							const outbound = isOutbound(message.direction);
							return (
								<div
									key={message.id}
									className={`flex ${outbound ? "justify-end" : "justify-start"}`}
								>
									<div
										className={`max-w-[80%] rounded-lg px-4 py-3 ${
											outbound
												? "bg-brand-600 text-white dark:bg-brand-500"
												: "bg-neutral-100 text-neutral-900 dark:bg-neutral-800 dark:text-neutral-100"
										}`}
									>
										{message.subject && (
											<p className="mb-2 font-semibold text-sm">
												{message.subject}
											</p>
										)}
										{message.bodyHtml ? (
											<div
												className="text-sm leading-relaxed"
												dangerouslySetInnerHTML={{
													__html: message.bodyHtml,
												}}
											/>
										) : (
											<p className="text-sm leading-relaxed whitespace-pre-wrap">
												{message.bodyText || "(メッセージなし)"}
											</p>
										)}
										<div
											className={`mt-2 flex items-center justify-between text-xs ${
												outbound
													? "text-brand-100"
													: "text-neutral-500 dark:text-neutral-400"
											}`}
										>
											<span>{formatDate(message.createdAt)}</span>
											{outbound && (
												<span className="ml-2">
													{message.fromEmail}
												</span>
											)}
											{!outbound && (
												<span className="ml-2">
													{message.fromEmail}
												</span>
											)}
										</div>
									</div>
								</div>
							);
						})}
						<div ref={messagesEndRef} />
					</div>
				)}
			</div>
		</div>
	);
}

