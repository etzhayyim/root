"use client";

import type { ReactNode } from "react";
import Link from "next/link";

/**
 * @etzhayyim/etzhayyim-hrse#DashboardCard
 * ダッシュボード用カードコンポーネント
 * Apple HIGに基づくタッチ最適化デザイン
 */

interface DashboardCardProps {
	title: string;
	value: string | number;
	subtitle?: string;
	icon?: ReactNode;
	trend?: {
		direction: "up" | "down" | "neutral";
		value: string;
	};
	href?: string;
	variant?: "default" | "primary" | "success" | "warning" | "info";
}

export function DashboardCard({
	title,
	value,
	subtitle,
	icon,
	trend,
	href,
	variant = "default",
}: DashboardCardProps) {
	const variantStyles = {
		default: {
			container: "bg-background dark:bg-neutral-900 border border-border dark:border-neutral-800",
			icon: "bg-background-surface text-content-secondary dark:bg-neutral-800 dark:text-neutral-400",
			value: "text-content-primary dark:text-neutral-100",
		},
		primary: {
			container: "bg-gradient-to-br from-brand-500 to-brand-700 dark:from-brand-600 dark:to-brand-800 border-0",
			icon: "bg-white/20 text-white",
			value: "text-white",
		},
		success: {
			container: "bg-gradient-to-br from-success-500 to-success-600 dark:from-success-600 dark:to-success-700 border-0",
			icon: "bg-white/20 text-white",
			value: "text-white",
		},
		warning: {
			container: "bg-gradient-to-br from-warning-500 to-warning-600 dark:from-warning-600 dark:to-warning-700 border-0",
			icon: "bg-white/20 text-white",
			value: "text-white",
		},
		info: {
			container: "bg-gradient-to-br from-brand-500 to-brand-600 dark:from-brand-600 dark:to-brand-700 border-0",
			icon: "bg-white/20 text-white",
			value: "text-white",
		},
	};

	const isColoredVariant = variant !== "default";
	const styles = variantStyles[variant];

	const trendColors = {
		up: isColoredVariant ? "text-white/80" : "text-success-500 dark:text-success-400",
		down: isColoredVariant ? "text-white/80" : "text-error-500 dark:text-error-400",
		neutral: isColoredVariant ? "text-white/60" : "text-content-secondary dark:text-neutral-400",
	};

	const trendIcons = {
		up: (
			<svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 11l5-5m0 0l5 5m-5-5v12" />
			</svg>
		),
		down: (
			<svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 13l-5 5m0 0l-5-5m5 5V6" />
			</svg>
		),
		neutral: (
			<svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14" />
			</svg>
		),
	};

	const content = (
		<div
			className={`group relative overflow-hidden rounded-2xl p-6 shadow-lg transition-all duration-300 ${styles.container} ${
				href ? "cursor-pointer hover:shadow-xl hover:-translate-y-1 active:scale-[0.98]" : ""
			}`}
		>
			{/* Background decoration */}
			{isColoredVariant && (
				<div className="absolute right-0 top-0 -mr-8 -mt-8 h-32 w-32 rounded-full bg-white/10 blur-2xl" />
			)}

			<div className="relative flex items-start justify-between">
				<div className="flex-1">
					<p className={`text-sm font-medium ${isColoredVariant ? "text-white/80" : "text-content-secondary dark:text-neutral-400"}`}>
						{title}
					</p>
					<p className={`mt-2 text-4xl font-bold tracking-tight ${styles.value}`}>
						{value}
					</p>
					{subtitle && (
						<p className={`mt-1 text-sm ${isColoredVariant ? "text-white/60" : "text-content-secondary dark:text-neutral-400"}`}>
							{subtitle}
						</p>
					)}
					{trend && (
						<div className={`mt-3 flex items-center gap-1 ${trendColors[trend.direction]}`}>
							{trendIcons[trend.direction]}
							<span className="text-sm font-medium">{trend.value}</span>
						</div>
					)}
				</div>
				{icon && (
					<div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl ${styles.icon}`}>
						{icon}
					</div>
				)}
			</div>

			{/* Hover indicator for links */}
			{href && (
				<div className={`absolute bottom-4 right-4 opacity-0 transition-opacity group-hover:opacity-100 ${isColoredVariant ? "text-white/60" : "text-content-tertiary"}`}>
					<svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
					</svg>
				</div>
			)}
		</div>
	);

	if (href) {
		return <Link href={href}>{content}</Link>;
	}

	return content;
}

/**
 * Quick Action Button for Dashboard
 */
interface QuickActionProps {
	title: string;
	description: string;
	icon: ReactNode;
	href: string;
}

export function QuickAction({ title, description, icon, href }: QuickActionProps) {
	return (
		<Link href={href}>
			<div className="group flex items-center gap-4 rounded-md border border-border bg-background p-4 shadow-sm transition-all duration-300 hover:border-brand-500 hover:shadow-md dark:border-neutral-800 dark:bg-neutral-900 dark:hover:border-brand-500">
				<div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-md bg-brand-50 text-brand-500 transition-colors group-hover:bg-brand-100 dark:bg-brand-900/30 dark:text-brand-400 dark:group-hover:bg-brand-900/50">
					{icon}
				</div>
				<div className="flex-1 min-w-0">
					<h4 className="font-semibold text-content-primary dark:text-neutral-100">{title}</h4>
					<p className="mt-0.5 text-sm text-content-secondary dark:text-neutral-400 truncate">{description}</p>
				</div>
				<svg
					className="h-5 w-5 shrink-0 text-content-tertiary transition-transform group-hover:translate-x-1 dark:text-neutral-500"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
				</svg>
			</div>
		</Link>
	);
}

/**
 * Recent Activity Item
 */
interface ActivityItemProps {
	title: string;
	description: string;
	time: string;
	type: "matching" | "email" | "member" | "system";
}

export function ActivityItem({ title, description, time, type }: ActivityItemProps) {
	const typeStyles = {
		matching: "bg-success-100 text-success-700 dark:bg-success-900/30 dark:text-success-400",
		email: "bg-brand-100 text-brand-700 dark:bg-brand-900/30 dark:text-brand-400",
		member: "bg-brand-100 text-brand-700 dark:bg-brand-900/30 dark:text-brand-400",
		system: "bg-background-surface text-content-secondary dark:bg-neutral-800 dark:text-neutral-400",
	};

	const typeIcons = {
		matching: (
			<svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
			</svg>
		),
		email: (
			<svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
			</svg>
		),
		member: (
			<svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
			</svg>
		),
		system: (
			<svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
			</svg>
		),
	};

	return (
		<div className="flex items-start gap-3 py-3 border-b border-border-light last:border-0 dark:border-neutral-800">
			<div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-md ${typeStyles[type]}`}>
				{typeIcons[type]}
			</div>
			<div className="flex-1 min-w-0">
				<p className="font-medium text-content-primary dark:text-neutral-100 truncate">{title}</p>
				<p className="text-sm text-content-secondary dark:text-neutral-400 truncate">{description}</p>
			</div>
			<span className="shrink-0 text-xs text-content-secondary dark:text-neutral-500">{time}</span>
		</div>
	);
}

