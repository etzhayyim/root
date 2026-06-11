"use client";

/**
 * @etzhayyim/etzhayyim-hrse#RecruiterSupporterPage
 * Agency Recruiter Supporter AI Agent Page
 */

import { useUser } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useEffect, useState, useCallback } from "react";
import { ChatInterface } from "@/components/recruiter-agent/ChatInterface";
import { TaskDashboard } from "@/components/recruiter-agent/TaskDashboard";
import { SuggestionPanel } from "@/components/recruiter-agent/SuggestionPanel";
import {
	useRecruiterAgentServiceClient,
	type Task,
	type Suggestion,
	type ChatMessage,
} from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import {
	GetDailyTasksRequestSchema,
	GetSuggestionsRequestSchema,
	SendChatMessageRequestSchema,
	MarkTaskCompleteRequestSchema,
	GetChatHistoryRequestSchema,
} from "@/gen/proto/hrse/v1/recruiter_agent_pb";

export default function RecruiterSupporterPage() {
	const { user, isLoaded } = useUser();
	const router = useRouter();
	const recruiterAgentClient = useRecruiterAgentServiceClient();
	const [tasks, setTasks] = useState<Task[]>([]);
	const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
	const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
	const [conversationId, setConversationId] = useState<string | undefined>();
	const [loading, setLoading] = useState(true);

	// Load initial data
	useEffect(() => {
		if (!isLoaded) return;

		if (!user) {
			router.push("/auth/signin");
			return;
		}

		loadData();
	}, [isLoaded, user, router]);

	const loadData = useCallback(async () => {
		setLoading(true);
		try {
			// Load daily tasks
			try {
				const tasksRes = await recruiterAgentClient.getDailyTasks(
					create(GetDailyTasksRequestSchema, {})
				);
				if (tasksRes.tasks) {
					setTasks(tasksRes.tasks as Task[]);
				}
			} catch (error) {
				console.error("Failed to fetch tasks:", error);
				// Fallback to empty array
				setTasks([]);
			}

			// Load suggestions
			try {
				const suggestionsRes = await recruiterAgentClient.getSuggestions(
					create(GetSuggestionsRequestSchema, { limit: 10 })
				);
				if (suggestionsRes.suggestions) {
					setSuggestions(suggestionsRes.suggestions as Suggestion[]);
				}
			} catch (error) {
				console.error("Failed to fetch suggestions:", error);
				// Fallback to empty array
				setSuggestions([]);
			}

			// Load chat history
			try {
				const chatRes = await recruiterAgentClient.getChatHistory(
					create(GetChatHistoryRequestSchema, {
						conversationId: conversationId,
						limit: 50,
						offset: 0,
					})
				);
				if (chatRes.messages) {
					setChatMessages(chatRes.messages as ChatMessage[]);
					if (chatRes.conversationId) {
						setConversationId(chatRes.conversationId);
					}
				}
			} catch (error) {
				console.error("Failed to fetch chat history:", error);
				// Fallback to empty array
				setChatMessages([]);
			}
		} catch (error) {
			console.error("Failed to load data:", error);
		} finally {
			setLoading(false);
		}
	}, [recruiterAgentClient, conversationId]);

	const handleSendMessage = useCallback(
		async (message: string) => {
			try {
				const res = await recruiterAgentClient.sendChatMessage(
					create(SendChatMessageRequestSchema, {
						content: message,
						conversationId: conversationId,
					})
				);

				// Update chat messages
				if (res.userMessage && res.assistantMessage) {
					setChatMessages((prev) => [
						...(prev as ChatMessage[]),
						res.userMessage as ChatMessage,
						res.assistantMessage as ChatMessage,
					]);
				}

				// Update conversation ID if provided
				if (res.conversationId) {
					setConversationId(res.conversationId);
				}

				// Update suggestions if provided
				if (res.suggestedActions && res.suggestedActions.length > 0) {
					setSuggestions((prev) => [
						...(prev as Suggestion[]),
						...(res.suggestedActions as Suggestion[]),
					]);
				}
			} catch (error) {
				console.error("Failed to send message:", error);
				// Re-throw error so ChatInterface can handle it
				throw error;
			}
		},
		[recruiterAgentClient, conversationId]
	);

	const handleTaskComplete = useCallback(
		async (taskId: string, completed: boolean) => {
			try {
				const res = await recruiterAgentClient.markTaskComplete(
					create(MarkTaskCompleteRequestSchema, {
						taskId: taskId,
						completed: completed,
					})
				);

				// Update task in local state
				if (res.task) {
					setTasks((prev) =>
						prev.map((task) =>
							task.id === taskId ? (res.task as Task) : task
						)
					);
				}
			} catch (error) {
				console.error("Failed to mark task complete:", error);
				// Revert optimistic update
				setTasks((prev) =>
					prev.map((task) =>
						task.id === taskId ? { ...task, completed: !completed } : task
					)
				);
			}
		},
		[recruiterAgentClient]
	);

	const handleSuggestionClick = useCallback((suggestion: Suggestion) => {
		if (suggestion.actionUrl) {
			router.push(suggestion.actionUrl);
		}
	}, [router]);

	if (!isLoaded) {
		return (
			<div className="flex min-h-screen items-center justify-center">
				<div className="text-lg text-neutral-600 dark:text-neutral-400">
					読み込み中...
				</div>
			</div>
		);
	}

	if (!user) {
		return null;
	}

	return (
		<div className="min-h-screen bg-neutral-50 p-4 md:p-8 dark:bg-neutral-950">
			<div className="mx-auto max-w-7xl">
				{/* Header */}
				<div className="mb-8">
					<h1 className="text-3xl font-bold text-neutral-900 dark:text-neutral-100">
						AI リクルーターサポート
					</h1>
					<p className="mt-2 text-neutral-600 dark:text-neutral-400">
						今日のタスクと推奨アクションを確認し、AIエージェントと対話して業務を効率化しましょう
					</p>
				</div>

				{/* Main Layout - iPad optimized split view */}
				<div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
					{/* Left Column - Tasks and Suggestions */}
					<div className="space-y-6">
						<TaskDashboard
							tasks={tasks}
							onTaskComplete={handleTaskComplete}
							loading={loading}
						/>
						<SuggestionPanel
							suggestions={suggestions}
							onSuggestionClick={handleSuggestionClick}
							loading={loading}
						/>
					</div>

					{/* Right Column - Chat Interface */}
					<div className="lg:sticky lg:top-4">
						<div className="mb-4">
							<h2 className="text-xl font-bold text-neutral-900 dark:text-neutral-100">
								AI チャット
							</h2>
							<p className="text-sm text-neutral-600 dark:text-neutral-400">
								AIエージェントに質問したり、アドバイスを求めたりできます
							</p>
						</div>
						<div className="h-[600px]">
							<ChatInterface
								onSendMessage={handleSendMessage}
								initialMessages={chatMessages.map((msg) => ({
									id: msg.id,
									role: msg.role as "user" | "assistant",
									content: msg.content,
									timestamp: msg.createdAt
										? new Date(
												// Handle Timestamp conversion
												typeof msg.createdAt === "object" && "seconds" in msg.createdAt
													? Number((msg.createdAt as any).seconds) * 1000 +
														Number((msg.createdAt as any).nanos || 0) / 1000000
													: Date.now()
											)
										: new Date(),
								}))}
							/>
						</div>
					</div>
				</div>
			</div>
		</div>
	);
}
