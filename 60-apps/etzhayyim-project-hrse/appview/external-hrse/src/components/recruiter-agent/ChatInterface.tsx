"use client";

import { useState, useRef, useEffect } from "react";
import { TouchOptimizedButton } from "@/components/TouchOptimizedButton";
import { ChatMessage } from "./ChatMessage";

/**
 * @etzhayyim/etzhayyim-hrse#ChatInterface
 * Chat interface component for recruiter agent
 */
interface ChatMessage {
	id: string;
	role: "user" | "assistant";
	content: string;
	timestamp: Date;
}

interface ChatInterfaceProps {
	onSendMessage?: (message: string) => Promise<void>;
	initialMessages?: ChatMessage[];
}

export function ChatInterface({
	onSendMessage,
	initialMessages = [],
}: ChatInterfaceProps) {
	const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
	const [input, setInput] = useState("");
	const [isLoading, setIsLoading] = useState(false);
	const messagesEndRef = useRef<HTMLDivElement>(null);

	// Update messages when initialMessages changes
	useEffect(() => {
		if (initialMessages.length > 0) {
			setMessages(initialMessages);
		}
	}, [initialMessages]);

	// Scroll to bottom when new messages arrive
	useEffect(() => {
		messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
	}, [messages]);

	const handleSend = async () => {
		if (!input.trim() || isLoading) return;

		const userMessage: ChatMessage = {
			id: `msg-${Date.now()}`,
			role: "user",
			content: input.trim(),
			timestamp: new Date(),
		};

		setMessages((prev) => [...prev, userMessage]);
		setInput("");
		setIsLoading(true);

		try {
			if (onSendMessage) {
				await onSendMessage(userMessage.content);
				// Note: The parent component will update initialMessages with the response
				// This component will update via useEffect when initialMessages changes
			} else {
				// Mock response if no handler provided
				setTimeout(() => {
					const assistantMessage: ChatMessage = {
						id: `msg-${Date.now() + 1}`,
						role: "assistant",
						content: "メッセージを受信しました。AIエージェントが応答を生成しています...",
						timestamp: new Date(),
					};
					setMessages((prev) => [...prev, assistantMessage]);
					setIsLoading(false);
				}, 1000);
			}
		} catch (error) {
			console.error("Failed to send message:", error);
			setIsLoading(false);
		} finally {
			setIsLoading(false);
		}
	};

	const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
		if (e.key === "Enter" && !e.shiftKey) {
			e.preventDefault();
			handleSend();
		}
	};

	return (
		<div className="flex h-full flex-col rounded-lg border border-neutral-200 bg-white dark:border-neutral-800 dark:bg-neutral-900">
			{/* Messages area */}
			<div className="flex-1 overflow-y-auto p-4">
				{messages.length === 0 ? (
					<div className="flex h-full items-center justify-center">
						<p className="text-neutral-500 dark:text-neutral-400">
							AIエージェントにメッセージを送信して会話を開始してください
						</p>
					</div>
				) : (
					<>
						{messages.map((message) => (
							<ChatMessage
								key={message.id}
								role={message.role}
								content={message.content}
								timestamp={message.timestamp}
							/>
						))}
						{isLoading && (
							<div className="mb-4 flex justify-start">
								<div className="rounded-lg bg-neutral-100 px-4 py-3 dark:bg-neutral-800">
									<p className="text-sm text-neutral-500 dark:text-neutral-400">
										入力中...
									</p>
								</div>
							</div>
						)}
						<div ref={messagesEndRef} />
					</>
				)}
			</div>

			{/* Input area */}
			<div className="border-t border-neutral-200 p-4 dark:border-neutral-800">
				<div className="flex gap-2">
					<textarea
						value={input}
						onChange={(e) => setInput(e.target.value)}
						onKeyPress={handleKeyPress}
						placeholder="メッセージを入力..."
						className="flex-1 resize-none rounded-lg border border-neutral-300 bg-white px-4 py-3 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100"
						rows={2}
						disabled={isLoading}
					/>
					<TouchOptimizedButton
						onClick={handleSend}
						disabled={!input.trim() || isLoading}
						className="self-end"
					>
						送信
					</TouchOptimizedButton>
				</div>
			</div>
		</div>
	);
}
