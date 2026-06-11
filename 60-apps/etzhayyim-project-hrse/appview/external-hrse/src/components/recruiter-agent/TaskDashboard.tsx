"use client";

import { TouchOptimizedButton } from "@/components/TouchOptimizedButton";
import type { Task } from "@/gen/proto/hrse/v1/recruiter_agent_pb";

/**
 * @etzhayyim/etzhayyim-hrse#TaskDashboard
 * Task dashboard component for recruiter agent
 */

interface TaskDashboardProps {
	tasks: Task[];
	onTaskClick?: (task: Task) => void;
	onTaskComplete?: (taskId: string, completed: boolean) => void;
	loading?: boolean;
}

export function TaskDashboard({
	tasks,
	onTaskClick,
	onTaskComplete,
	loading = false,
}: TaskDashboardProps) {
	const getPriorityColor = (priority: string) => {
		switch (priority) {
			case "high":
				return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";
			case "medium":
				return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200";
			case "low":
				return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
			default:
				return "bg-neutral-100 text-neutral-800 dark:bg-neutral-800 dark:text-neutral-200";
		}
	};

	const formatDate = (timestamp?: { seconds?: bigint | number; nanos?: number }) => {
		if (!timestamp?.seconds) return undefined;
		const seconds = typeof timestamp.seconds === "bigint" ? Number(timestamp.seconds) : timestamp.seconds;
		return new Date(seconds * 1000);
	};

	if (loading) {
		return (
			<div className="rounded-lg border border-neutral-200 bg-white p-6 dark:border-neutral-800 dark:bg-neutral-900">
				<h2 className="mb-4 text-xl font-bold text-neutral-900 dark:text-neutral-100">
					今日のタスク
				</h2>
				<div className="text-neutral-500 dark:text-neutral-400">
					読み込み中...
				</div>
			</div>
		);
	}

	const completedCount = tasks.filter((t) => t.completed).length;
	const pendingCount = tasks.length - completedCount;

	return (
		<div className="rounded-lg border border-neutral-200 bg-white p-6 dark:border-neutral-800 dark:bg-neutral-900">
			<div className="mb-4 flex items-center justify-between">
				<h2 className="text-xl font-bold text-neutral-900 dark:text-neutral-100">
					今日のタスク
				</h2>
				<div className="text-sm text-neutral-600 dark:text-neutral-400">
					{completedCount}/{tasks.length} 完了
				</div>
			</div>

			{tasks.length === 0 ? (
				<div className="py-8 text-center text-neutral-500 dark:text-neutral-400">
					タスクはありません
				</div>
			) : (
				<div className="space-y-3">
					{tasks.map((task) => (
						<div
							key={task.id}
							className={`rounded-lg border p-4 transition-all ${
								task.completed
									? "border-neutral-200 bg-neutral-50 dark:border-neutral-800 dark:bg-neutral-950"
									: "border-neutral-300 bg-white dark:border-neutral-700 dark:bg-neutral-800"
							}`}
						>
							<div className="flex items-start gap-3">
								<input
									type="checkbox"
									checked={task.completed}
									onChange={(e) => {
										if (onTaskComplete) {
											onTaskComplete(task.id, e.target.checked);
										}
									}}
									className="mt-1 h-5 w-5 cursor-pointer rounded border-neutral-300 text-brand-600 focus:ring-2 focus:ring-brand-500 dark:border-neutral-600"
								/>
								<div className="flex-1">
									<div className="mb-1 flex items-center gap-2">
										<h3
											className={`font-semibold ${
												task.completed
													? "text-neutral-500 line-through dark:text-neutral-400"
													: "text-neutral-900 dark:text-neutral-100"
											}`}
										>
											{task.title}
										</h3>
										<span
											className={`rounded-full px-2 py-0.5 text-xs font-medium ${getPriorityColor(
												task.priority
											)}`}
										>
											{task.priority === "high"
												? "高"
												: task.priority === "medium"
													? "中"
													: "低"}
										</span>
									</div>
									<p className="text-sm text-neutral-600 dark:text-neutral-400">
										{task.description}
									</p>
									{task.dueAt && formatDate(task.dueAt) && (
										<p className="mt-1 text-xs text-neutral-500 dark:text-neutral-400">
											期限: {formatDate(task.dueAt)!.toLocaleDateString("ja-JP")}
										</p>
									)}
								</div>
								{onTaskClick && (
									<TouchOptimizedButton
										variant="outline"
										size="sm"
										onClick={() => onTaskClick(task)}
									>
										詳細
									</TouchOptimizedButton>
								)}
							</div>
						</div>
					))}
				</div>
			)}
		</div>
	);
}
