"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useMailboxServiceClient } from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import {
	ListThreadsRequestSchema,
	MessageThread,
} from "@/gen/proto/hrse/v1/mailbox_pb";

/**
 * @etzhayyim/etzhayyim-hrse#ThreadList
 * Thread list component for mailbox
 */
interface ThreadListProps {
	mailboxId: string;
	onThreadSelect?: (threadId: string) => void;
	selectedThreadId?: string;
}

export function ThreadList({
	mailboxId,
	onThreadSelect,
	selectedThreadId,
}: ThreadListProps) {
	const [threads, setThreads] = useState<MessageThread[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		loadThreads();
	}, [mailboxId]);

	const client = useMailboxServiceClient();

	const loadThreads = async () => {
		try {
			setLoading(true);
			const response = await client.listThreads(
				create(ListThreadsRequestSchema, {
					mailboxId,
					limit: 50,
					offset: 0,
				}),
			);
			setThreads(response.threads);
			setError(null);
		} catch (err) {
			console.error("Failed to load threads:", err);
			setError("スレッドの読み込みに失敗しました");
		} finally {
			setLoading(false);
		}
	};

	const formatDate = (timestamp: any) => {
		if (!timestamp) return "";
		const date = new Date(timestamp.seconds * 1000);
		return date.toLocaleDateString("ja-JP", {
			month: "short",
			day: "numeric",
			hour: "2-digit",
			minute: "2-digit",
		});
	};

	const getClassificationBadge = (classification?: string) => {
		if (!classification) return null;
		return (
			<span
				className={`inline-block rounded-full px-2 py-1 text-xs font-medium ${
					classification === "talent"
						? "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
						: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
				}`}
			>
				{classification === "talent" ? "人材" : "案件"}
			</span>
		);
	};

	if (loading) {
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
		<div className="flex h-full flex-col overflow-y-auto border-r border-neutral-200 dark:border-neutral-800">
			<div className="border-b border-neutral-200 p-4 dark:border-neutral-800">
				<h2 className="text-lg font-semibold">メールボックス</h2>
			</div>
			<div className="flex-1 overflow-y-auto">
				{threads.length === 0 ? (
					<div className="flex h-full items-center justify-center p-4">
						<p className="text-center text-neutral-500 dark:text-neutral-400">
							スレッドがありません
						</p>
					</div>
				) : (
					<div className="divide-y divide-neutral-200 dark:divide-neutral-800">
						{threads.map((thread) => {
							const isSelected = thread.id === selectedThreadId;
							return (
								<button
									key={thread.id}
									onClick={() => onThreadSelect?.(thread.id)}
									className={`w-full text-left p-4 transition-colors hover:bg-neutral-50 dark:hover:bg-neutral-800 ${
										isSelected
											? "bg-brand-50 dark:bg-brand-900/20"
											: ""
									}`}
								>
									<div className="flex items-start justify-between gap-2">
										<div className="flex-1 min-w-0">
											<div className="flex items-center gap-2 mb-1">
												<h3 className="font-medium text-sm truncate">
													{thread.subject}
												</h3>
												{getClassificationBadge(thread.classification)}
											</div>
											{thread.lastMessageAt && (
												<p className="text-xs text-neutral-500 dark:text-neutral-400">
													{formatDate(thread.lastMessageAt)}
												</p>
											)}
										</div>
										{thread.unreadCount > 0 && (
											<span className="flex-shrink-0 rounded-full bg-brand-600 px-2 py-1 text-xs font-medium text-white">
												{thread.unreadCount}
											</span>
										)}
									</div>
									{thread.assignedTo && (
										<p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
											担当: {thread.assignedTo}
										</p>
									)}
								</button>
							);
						})}
					</div>
				)}
			</div>
		</div>
	);
}

