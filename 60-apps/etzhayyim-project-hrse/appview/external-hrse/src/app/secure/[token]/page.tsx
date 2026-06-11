"use client";

// @etzhayyim/etzhayyim-hrse#SecureLinkPage
// Secure Link Access Page

import { useParams, useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import { TouchOptimizedButton } from "@/components/TouchOptimizedButton";
import { useEmailAgentServiceClient } from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import {
	VerifySecureLinkAccessRequestSchema,
} from "@/gen/proto/hrse/v1/email_agent_pb";
import { AnalyticsTracker } from "@/lib/services/analytics-tracker";

export default function SecureLinkPage() {
	const params = useParams();
	const router = useRouter();
	const token = params.token as string;
	const emailAgentClient = useEmailAgentServiceClient();

	const [email, setEmail] = useState("");
	const [verified, setVerified] = useState(false);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const [entityType, setEntityType] = useState<"job" | "job_seeker" | null>(null);
	const [entityId, setEntityId] = useState<string | null>(null);
	const [secureLinkId, setSecureLinkId] = useState<string | null>(null);

	useEffect(() => {
		// Start analytics tracking when verified
		if (verified && secureLinkId && email) {
			const tracker = new AnalyticsTracker(secureLinkId, email);
			tracker.startTracking();
			return () => {
				tracker.stopTracking();
				// sendFinalData is now async, but we can't await in cleanup
				tracker.sendFinalData().catch(err => {
					console.error("Failed to send final analytics data:", err);
				});
			};
		}
	}, [verified, secureLinkId, email]);

	const handleVerify = async () => {
		if (!email || !email.includes("@")) {
			setError("有効なメールアドレスを入力してください");
			return;
		}

		setLoading(true);
		setError(null);

		try {
			const response = await emailAgentClient.verifySecureLinkAccess(
				create(VerifySecureLinkAccessRequestSchema, {
					token,
					email,
				})
			);

			if (response.valid) {
				setVerified(true);
				setEntityType(response.entityType as "job" | "job_seeker");
				setEntityId(response.entityId);
				setSecureLinkId(response.secureLinkId);
			} else {
				setError("このメールアドレスはアクセス権限がありません");
			}
		} catch (err) {
			setError(
				err instanceof Error ? err.message : "認証エラーが発生しました",
			);
		} finally {
			setLoading(false);
		}
	};

	if (verified && entityType && entityId) {
		// Redirect to entity detail page
		if (entityType === "job") {
			return (
				<div className="min-h-screen bg-neutral-50 p-4 md:p-8 dark:bg-neutral-950">
					<div className="mx-auto max-w-4xl">
						<div className="rounded-lg bg-white p-8 shadow dark:bg-neutral-900">
							<h1 className="mb-4 text-2xl font-bold">案件詳細</h1>
							<p className="text-neutral-600 dark:text-neutral-400">
								案件ID: {entityId}
							</p>
							{/* TODO: Fetch and display job details */}
						</div>
					</div>
				</div>
			);
		} else {
			return (
				<div className="min-h-screen bg-neutral-50 p-4 md:p-8 dark:bg-neutral-950">
					<div className="mx-auto max-w-4xl">
						<div className="rounded-lg bg-white p-8 shadow dark:bg-neutral-900">
							<h1 className="mb-4 text-2xl font-bold">人材詳細</h1>
							<p className="text-neutral-600 dark:text-neutral-400">
								人材ID: {entityId}
							</p>
							{/* TODO: Fetch and display job seeker details */}
						</div>
					</div>
				</div>
			);
		}
	}

	return (
		<div className="flex min-h-screen items-center justify-center bg-neutral-50 p-4 dark:bg-neutral-950">
			<div className="w-full max-w-md rounded-lg bg-white p-8 shadow dark:bg-neutral-900">
				<h1 className="mb-6 text-2xl font-bold">セキュアリンクアクセス</h1>
				<p className="mb-6 text-neutral-600 dark:text-neutral-400">
					詳細情報を確認するには、メールアドレスを入力してください。
				</p>

				{error && (
					<div className="mb-4 rounded bg-red-50 p-4 text-red-800 dark:bg-red-900/20 dark:text-red-400">
						{error}
					</div>
				)}

				<div className="mb-4">
					<label
						htmlFor="email"
						className="mb-2 block text-sm font-medium text-neutral-700 dark:text-neutral-300"
					>
						メールアドレス
					</label>
					<input
						id="email"
						type="email"
						value={email}
						onChange={(e) => setEmail(e.target.value)}
						onKeyDown={(e) => {
							if (e.key === "Enter") {
								handleVerify();
							}
						}}
						className="w-full rounded border border-neutral-300 bg-white px-4 py-2 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-neutral-600 dark:bg-neutral-800 dark:text-white"
						placeholder="your@email.com"
						disabled={loading}
					/>
				</div>

				<TouchOptimizedButton
					onClick={handleVerify}
					disabled={loading || !email}
					className="w-full"
				>
					{loading ? "確認中..." : "アクセス"}
				</TouchOptimizedButton>
			</div>
		</div>
	);
}
