"use client";

import { useParams } from "next/navigation";
import { ChatView } from "@/components/mailbox/ChatView";
import { ComposeMessage } from "@/components/mailbox/ComposeMessage";
import { useMailboxServiceClient } from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import { GetThreadRequestSchema } from "@/gen/proto/hrse/v1/mailbox_pb";
import { useEffect, useState } from "react";

/**
 * @etzhayyim/etzhayyim-hrse#MailboxThreadPage
 * Individual thread view page
 */
export default function MailboxThreadPage() {
	const params = useParams();
	const threadId = params.threadId as string;
	const [toEmail, setToEmail] = useState<string>("");
	const client = useMailboxServiceClient();

	useEffect(() => {
		if (threadId) {
			loadThread();
		}
	}, [threadId]);

	const loadThread = async () => {
		try {
			const response = await client.getThread(
				create(GetThreadRequestSchema, { id: threadId }),
			);
			// Set to_email from thread context
			// In production, get from last inbound message
			setToEmail("");
		} catch (err) {
			console.error("Failed to load thread:", err);
		}
	};

	const handleMessageSent = () => {
		// Reload chat view
		window.location.reload();
	};

	return (
		<div className="flex h-screen flex-col">
			<div className="flex-1 overflow-hidden">
				<ChatView threadId={threadId} />
			</div>
			<div className="flex-shrink-0">
				<ComposeMessage
					threadId={threadId}
					toEmail={toEmail}
					onMessageSent={handleMessageSent}
				/>
			</div>
		</div>
	);
}



