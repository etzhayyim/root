import { getClerkClient } from "./clerk";

/**
 * Clerk Subscription管理ヘルパー
 * 注意: Clerk v6には直接的なサブスクリプションAPIはありません。
 * この実装は、Clerkのメタデータ機能を使用してサブスクリプション情報を管理し、
 * 実際の決済は外部サービス（Stripe等）と連携する前提のインターフェースです。
 */

export interface Subscription {
	id: string;
	status: "active" | "cancelled" | "paused";
	amount: number;
	currency: string;
	contractId?: string;
	userId?: string;
}

/**
 * Clerkメタデータ内のサブスクリプション情報の型定義
 */
type SubscriptionMetadata = {
	contractId: string;
	amount: number;
	currency: string;
	status: string;
	createdAt: string;
	updatedAt?: string;
};

/**
 * サブスクリプションメタデータを取得するヘルパー関数
 */
function getSubscriptionsFromMetadata(
	publicMetadata: Record<string, unknown> | undefined,
): Record<string, SubscriptionMetadata> {
	return (publicMetadata?.subscriptions as Record<string, SubscriptionMetadata>) || {};
}

/**
 * サブスクリプション作成
 * @param userId - Clerk User ID
 * @param contractId - 契約ID（メタデータとして保存）
 * @param amount - 月額料金（最小単位、例: 1000 = 10.00 JPY）
 * @param currency - 通貨コード（例: "JPY"）
 * @returns Subscription ID
 */
export async function createSubscription(
	userId: string,
	contractId: string,
	amount: number,
	currency: string = "JPY",
): Promise<string> {
	const clerkClient = await getClerkClient();

	// サブスクリプションID生成
	const subscriptionId = `sub_${crypto.randomUUID()}`;

	// Clerkのユーザーメタデータにサブスクリプション情報を保存
	// 実際の決済処理は外部サービス（Stripe等）で行い、そのIDをここで管理
	try {
		// 既存のメタデータを取得してマージ
		const user = await clerkClient.users.getUser(userId);
		const existingSubscriptions = getSubscriptionsFromMetadata(
			user.publicMetadata as Record<string, unknown> | undefined,
		);

		await clerkClient.users.updateUserMetadata(userId, {
			publicMetadata: {
				...user.publicMetadata,
				subscriptions: {
					...existingSubscriptions,
					[subscriptionId]: {
						contractId,
						amount,
						currency,
						status: "active",
						createdAt: new Date().toISOString(),
					},
				},
			},
		});

		return subscriptionId;
	} catch (error) {
		console.error("Failed to create subscription:", error);
		throw new Error("Failed to create subscription");
	}
}

/**
 * サブスクリプション更新
 */
export async function updateSubscription(
	subscriptionId: string,
	userId: string,
	updates: {
		amount?: number;
		status?: "active" | "cancelled" | "paused";
	},
): Promise<void> {
	const clerkClient = await getClerkClient();

	try {
		const user = await clerkClient.users.getUser(userId);
		const subscriptions = getSubscriptionsFromMetadata(
			user.publicMetadata as Record<string, unknown> | undefined,
		);

		if (!subscriptions[subscriptionId]) {
			throw new Error("Subscription not found");
		}

		const subscription = subscriptions[subscriptionId];
		const updatedSubscription = {
			...subscription,
			...(updates.amount !== undefined && { amount: updates.amount }),
			...(updates.status !== undefined && { status: updates.status }),
			updatedAt: new Date().toISOString(),
		};

		subscriptions[subscriptionId] = updatedSubscription;

		await clerkClient.users.updateUserMetadata(userId, {
			publicMetadata: {
				...user.publicMetadata,
				subscriptions,
			},
		});
	} catch (error) {
		console.error("Failed to update subscription:", error);
		throw new Error("Failed to update subscription");
	}
}

/**
 * サブスクリプション取得
 */
export async function getSubscription(
	subscriptionId: string,
	userId: string,
): Promise<Subscription | null> {
	const clerkClient = await getClerkClient();

	try {
		const user = await clerkClient.users.getUser(userId);
		const subscriptions = getSubscriptionsFromMetadata(
			user.publicMetadata as Record<string, unknown> | undefined,
		);

		const subscription = subscriptions[subscriptionId];
		if (!subscription) {
			return null;
		}

		return {
			id: subscriptionId,
			status: subscription.status as "active" | "cancelled" | "paused",
			amount: subscription.amount,
			currency: subscription.currency,
			contractId: subscription.contractId,
			userId,
		};
	} catch (error) {
		console.error("Failed to get subscription:", error);
		throw new Error("Failed to get subscription");
	}
}

/**
 * サブスクリプションキャンセル
 */
export async function cancelSubscription(
	subscriptionId: string,
	userId: string,
): Promise<void> {
	await updateSubscription(subscriptionId, userId, { status: "cancelled" });
}
