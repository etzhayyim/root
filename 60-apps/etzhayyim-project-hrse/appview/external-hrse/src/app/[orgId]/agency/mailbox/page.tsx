"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { ThreadList } from "@/components/mailbox/ThreadList";
import { ChatView } from "@/components/mailbox/ChatView";
import { ComposeMessage } from "@/components/mailbox/ComposeMessage";
import { useMailboxServiceClient, useAgencyServiceClient } from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import {
	CreateMailboxRequestSchema,
	GetThreadRequestSchema,
} from "@/gen/proto/hrse/v1/mailbox_pb";
import { GetAgencyByClerkOrgIdRequestSchema } from "@/gen/proto/hrse/v1/agency_pb";

/**
 * @etzhayyim/etzhayyim-hrse#MailboxPage
 * Organization mailbox page
 */
export default function MailboxPage() {
	const params = useParams();
	const orgSlug = params.orgSlug as string;
	const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null);
	const [mailboxId, setMailboxId] = useState<string | null>(null);
	const [toEmail, setToEmail] = useState<string>("");
	const [loading, setLoading] = useState(true);
	const mailboxClient = useMailboxServiceClient();
	const agencyClient = useAgencyServiceClient();

	useEffect(() => {
		loadMailbox();
	}, [orgSlug]);

	const loadMailbox = async () => {
		try {
			setLoading(true);
			// Get agency by Clerk org ID
			const agencyResponse = await agencyClient.getAgencyByClerkOrgId(
				create(GetAgencyByClerkOrgIdRequestSchema, { clerkOrgId: orgSlug }),
			);

			if (!agencyResponse.agency) {
				console.error("Agency not found");
				return;
			}

			const agencyId = agencyResponse.agency.id;

			// Try to get existing mailbox or create new one
			try {
				// For now, we'll create a mailbox - in production, check if exists first
				const createResponse = await mailboxClient.createMailbox(
					create(CreateMailboxRequestSchema, {
						ownerType: "organization",
						ownerId: agencyId,
					}),
				);
				if (createResponse.mailbox) {
					setMailboxId(createResponse.mailbox.id);
				}
			} catch (err: unknown) {
				// If mailbox already exists, try to find it
				console.error("Failed to create mailbox, may already exist:", err);
				// In production, implement GetMailboxByOwner or similar
			}
		} catch (err) {
			console.error("Failed to load mailbox:", err);
		} finally {
			setLoading(false);
		}
	};

	const handleThreadSelect = (threadId: string) => {
		setSelectedThreadId(threadId);
		// Load thread to get to_email
		loadThreadForCompose(threadId);
	};

	const loadThreadForCompose = async (threadId: string) => {
		try {
			const response = await mailboxClient.getThread(
				create(GetThreadRequestSchema, { id: threadId }),
			);
			// Get the last inbound message's from_email
			// For now, we'll set a placeholder - in production, get from messages
			setToEmail(""); // Will be set from thread messages
		} catch (err) {
			console.error("Failed to load thread:", err);
		}
	};

	const handleMessageSent = () => {
		// Reload thread view
		if (selectedThreadId) {
			// Force refresh
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

