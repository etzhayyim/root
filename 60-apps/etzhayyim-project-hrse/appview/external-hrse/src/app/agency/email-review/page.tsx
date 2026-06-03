"use client";

// @etzhayyim/etzhayyim-hrse#EmailReviewPage
// Email Review Queue Page

import { useUser } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { TouchOptimizedButton } from "@/components/TouchOptimizedButton";
import { useEmailAgentServiceClient, type EmailMessage } from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import {
	ListEmailMessagesPendingReviewRequestSchema,
	ApproveEmailMessageRequestSchema,
	RejectEmailMessageRequestSchema,
	UpdateAndApproveEmailMessageRequestSchema,
} from "@/gen/proto/hrse/v1/email_agent_pb";

export default function EmailReviewPage() {
	const { user, isLoaded } = useUser();
	const router = useRouter();
	const emailAgentClient = useEmailAgentServiceClient();
	const [loading, setLoading] = useState(true);
	const [messages, setMessages] = useState<EmailMessage[]>([]);
	const [selectedMessage, setSelectedMessage] = useState<EmailMessage | null>(null);
	const [editing, setEditing] = useState(false);
	const [editedSubject, setEditedSubject] = useState("");
	const [editedBodyHtml, setEditedBodyHtml] = useState("");
	const [editedBodyText, setEditedBodyText] = useState("");

	const fetchMessages = useCallback(async () => {
		setLoading(true);
		try {
			const response = await emailAgentClient.listEmailMessagesPendingReview(
				create(ListEmailMessagesPendingReviewRequestSchema, {
					limit: 20,
					offset: 0,
				})
			);
			setMessages(response.messages || []);
		} catch (error) {
			console.error("Failed to fetch email review queue:", error);
		} finally {
			setLoading(false);
		}
	}, [emailAgentClient]);

	useEffect(() => {
		if (user?.id) {
			fetchMessages();
		}
	}, [user?.id, fetchMessages]);

	const handleApprove = async (messageId: string) => {
		try {
			await emailAgentClient.approveEmailMessage(
				create(ApproveEmailMessageRequestSchema, {
					messageId,
				})
			);
			fetchMessages();
			setSelectedMessage(null);
		} catch (error) {
			console.error("Failed to approve email:", error);
		}
	};

	const handleReject = async (messageId: string, reason: string) => {
		try {
			await emailAgentClient.rejectEmailMessage(
				create(RejectEmailMessageRequestSchema, {
					messageId,
					reason,
				})
			);
			fetchMessages();
			setSelectedMessage(null);
		} catch (error) {
			console.error("Failed to reject email:", error);
		}
	};

	const handleEdit = async (messageId: string) => {
		try {
			await emailAgentClient.updateAndApproveEmailMessage(
				create(UpdateAndApproveEmailMessageRequestSchema, {
					messageId,
					subject: editedSubject,
					bodyHtml: editedBodyHtml,
					bodyText: editedBodyText,
				})
			);
			fetchMessages();
			setSelectedMessage(null);
			setEditing(false);
		} catch (error) {
			console.error("Failed to edit email:", error);
		}
	};

	if (!isLoaded) {
		return (
			<div className="flex min-h-screen items-center justify-center">
				<div className="text-lg">読み込み中...</div>
			</div>
		);
	}

	if (!user) {
		router.push("/auth/signin");
		return null;
	}

	return (
		<div className="min-h-screen bg-neutral-50 p-4 md:p-8 dark:bg-neutral-950">
			<div className="mx-auto max-w-6xl">
				<h1 className="mb-6 text-3xl font-bold">メール承認キュー</h1>

				{loading ? (
					<div className="text-center">読み込み中...</div>
				) : messages.length === 0 ? (
					<div className="rounded-lg bg-white p-8 shadow dark:bg-neutral-900">
						<p className="text-neutral-600 dark:text-neutral-400">
							承認待ちのメールはありません。
						</p>
					</div>
				) : (
					<div className="grid grid-cols-1 gap-4 md:grid-cols-2">
						<div className="space-y-4">
							{messages.map((message) => (
								<div
									key={message.id}
									className={`cursor-pointer rounded-lg border p-4 transition-colors ${
										selectedMessage?.id === message.id
											? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
											: "border-neutral-200 bg-white hover:border-neutral-300 dark:border-neutral-700 dark:bg-neutral-900 dark:hover:border-neutral-600"
									}`}
									onClick={() => {
										setSelectedMessage(message);
										setEditedSubject(message.subject);
										setEditedBodyHtml(message.bodyHtml);
										setEditedBodyText(message.bodyText);
										setEditing(false);
									}}
								>
									<h3 className="font-semibold">{message.subject}</h3>
									<p className="text-sm text-neutral-600 dark:text-neutral-400">
										宛先: {message.recipientEmail || "N/A"}
									</p>
									<p className="text-xs text-neutral-500 dark:text-neutral-500">
										{message.createdAt ? new Date(Number(message.createdAt.seconds || 0) * 1000).toLocaleString("ja-JP") : "N/A"}
									</p>
								</div>
							))}
						</div>

						{selectedMessage && (
							<div className="rounded-lg border border-neutral-200 bg-white p-6 shadow dark:border-neutral-700 dark:bg-neutral-900">
								<h2 className="mb-4 text-xl font-bold">プレビュー</h2>

								{editing ? (
									<div className="space-y-4">
										<div>
											<label className="mb-2 block text-sm font-medium">
												件名
											</label>
											<input
												type="text"
												value={editedSubject}
												onChange={(e) => setEditedSubject(e.target.value)}
												className="w-full rounded border border-neutral-300 px-3 py-2 dark:border-neutral-600 dark:bg-neutral-800"
											/>
										</div>
										<div>
											<label className="mb-2 block text-sm font-medium">
												本文 (HTML)
											</label>
											<textarea
												value={editedBodyHtml}
												onChange={(e) => setEditedBodyHtml(e.target.value)}
												rows={10}
												className="w-full rounded border border-neutral-300 px-3 py-2 font-mono text-sm dark:border-neutral-600 dark:bg-neutral-800"
											/>
										</div>
										<div>
											<label className="mb-2 block text-sm font-medium">
												本文 (テキスト)
											</label>
											<textarea
												value={editedBodyText}
												onChange={(e) => setEditedBodyText(e.target.value)}
												rows={10}
												className="w-full rounded border border-neutral-300 px-3 py-2 font-mono text-sm dark:border-neutral-600 dark:bg-neutral-800"
											/>
										</div>
										<div className="flex gap-2">
											<TouchOptimizedButton
												onClick={() =>
													handleEdit(selectedMessage.id)
												}
												className="flex-1"
											>
												保存して承認
											</TouchOptimizedButton>
											<TouchOptimizedButton
												onClick={() => setEditing(false)}
												className="flex-1"
											>
												キャンセル
											</TouchOptimizedButton>
										</div>
									</div>
								) : (
									<>
										<div
											className="mb-4 rounded border border-neutral-200 p-4 dark:border-neutral-700"
											dangerouslySetInnerHTML={{
												__html: selectedMessage.bodyHtml,
											}}
										/>
										<div className="flex gap-2">
											<TouchOptimizedButton
												onClick={() =>
													handleApprove(selectedMessage.id)
												}
												className="flex-1"
											>
												承認
											</TouchOptimizedButton>
											<TouchOptimizedButton
												onClick={() => setEditing(true)}
												className="flex-1"
											>
												編集
											</TouchOptimizedButton>
											<TouchOptimizedButton
												onClick={() =>
													handleReject(
														selectedMessage.id,
														"Rejected by user",
													)
												}
												className="flex-1 bg-red-600 hover:bg-red-700"
											>
												却下
											</TouchOptimizedButton>
										</div>
									</>
								)}
							</div>
						)}
					</div>
				)}
			</div>
		</div>
	);
}
