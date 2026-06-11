"use client";

import { useState, useEffect } from "react";
import { ThreadList } from "@/components/mailbox/ThreadList";
import { ChatView } from "@/components/mailbox/ChatView";
import { ComposeMessage } from "@/components/mailbox/ComposeMessage";
import { useMailboxServiceClient, useRecruiterServiceClient } from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import {
	CreateMailboxRequestSchema,
	GetThreadRequestSchema,
} from "@/gen/proto/hrse/v1/mailbox_pb";
import { GetRecruiterByUserIdRequestSchema } from "@/gen/proto/hrse/v1/agency_pb";
import { useUser } from "@clerk/nextjs";

/**
 * @etzhayyim/etzhayyim-hrse#RecruiterMailboxPage
 * Recruiter mailbox page
 */
export default function RecruiterMailboxPage() {
	const { user } = useUser();
	const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null);
	const [mailboxId, setMailboxId] = useState<string | null>(null);
	const [toEmail, setToEmail] = useState<string>("");
	const [loading, setLoading] = useState(true);
	const mailboxClient = useMailboxServiceClient();
	const recruiterClient = useRecruiterServiceClient();

	useEffect(() => {
		if (user?.id) {
			loadMailbox();
		}
	}, [user?.id]);

	const loadMailbox = async () => {
		if (!user?.id) return;

		try {
			setLoading(true);
			// Get recruiter by Clerk user ID
			const recruiterResponse = await recruiterClient.getRecruiterByUserId(
				create(GetRecruiterByUserIdRequestSchema, { userId: user.id }),
			);

			if (!recruiterResponse.recruiter) {
				console.error("Recruiter not found");
				return;
			}

			const recruiterId = recruiterResponse.recruiter.id;

			// Try to get existing mailbox or create new one
			try {
				const createResponse = await mailboxClient.createMailbox(
					create(CreateMailboxRequestSchema, {
						ownerType: "recruiter",
						ownerId: recruiterId,
					}),
				);
				if (createResponse.mailbox) {
					setMailboxId(createResponse.mailbox.id);
				}
			} catch (err: unknown) {
				// If mailbox already exists, try to find it
				console.error("Failed to create mailbox, may already exist:", err);
			}
		} catch (err) {
			console.error("Failed to load mailbox:", err);
		} finally {
			setLoading(false);
		}
	};

	const handleThreadSelect = (threadId: string) => {
		setSelectedThreadId(threadId);
		loadThreadForCompose(threadId);
	};

	const loadThreadForCompose = async (threadId: string) => {
		try {
			const response = await mailboxClient.getThread(
				create(GetThreadRequestSchema, { id: threadId }),
			);
			setToEmail("");
		} catch (err) {
			console.error("Failed to load thread:", err);
		}
	};

	const handleMessageSent = () => {
		if (selectedThreadId) {
			setSelectedThreadId(null);
			setTimeout(() => setSelectedThreadId(selectedThreadId), 100);
		}
	};

	if (loading || !mailboxId) {
		return (
			<div className="flex h-screen items-center justify-center">
				<p className="text-neutral-500 dark:text-neutral-400">読み込み中...</p>
			</div>
		);
	}

	return (
		<div className="flex h-screen">
			{/* Thread list sidebar */}
			<div className="w-80 flex-shrink-0">
				<ThreadList
					mailboxId={mailboxId}
					onThreadSelect={handleThreadSelect}
					selectedThreadId={selectedThreadId || undefined}
				/>
			</div>

			{/* Main content area */}
			<div className="flex flex-1 flex-col">
				{selectedThreadId ? (
					<>
						<div className="flex-1 overflow-hidden">
							<ChatView threadId={selectedThreadId} />
						</div>
						<div className="flex-shrink-0">
							<ComposeMessage
								threadId={selectedThreadId}
								toEmail={toEmail}
								onMessageSent={handleMessageSent}
							/>
						</div>
					</>
				) : (
					<div className="flex h-full items-center justify-center">
						<p className="text-neutral-500 dark:text-neutral-400">
							スレッドを選択してください
						</p>
					</div>
				)}
			</div>
		</div>
	);
}

