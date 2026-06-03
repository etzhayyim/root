// @etzhayyim/cyber-freelance#AuthHelpersClient
// 認証チェックヘルパー関数（クライアントサイド）

"use client";

import { useUser, useAuth, SignedIn, SignedOut, RedirectToSignIn } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

/**
 * 認証を必須としてチェック（クライアントサイド）
 * 認証されていない場合はリダイレクト
 *
 * @param redirectTo リダイレクト先（デフォルト: /auth/signin）
 * @returns 認証されたユーザー情報（認証されていない場合はnull）
 *
 * @example
 * ```tsx
 * const user = useRequireAuth();
 * if (!user) return null; // リダイレクト中
 * // user は必ず存在することが保証される
 * ```
 */
export function useRequireAuth(redirectTo: string = "/auth/signin") {
	const { user, isLoaded } = useUser();
	const router = useRouter();

	useEffect(() => {
		if (isLoaded && !user) {
			router.push(redirectTo);
		}
	}, [isLoaded, user, router, redirectTo]);

	return user;
}

/**
 * 認証状態をチェック（クライアントサイド）
 * 認証されていない場合もエラーを投げない
 *
 * @returns 認証状態とユーザー情報
 *
 * @example
 * ```tsx
 * const { isAuthenticated, user } = useAuthCheck();
 * if (isAuthenticated) {
 *   // user を使用
 * }
 * ```
 */
export function useAuthCheck() {
	const { user, isLoaded } = useUser();
	const { getToken } = useAuth();

	return {
		isAuthenticated: isLoaded && !!user,
		isLoaded,
		user: user || null,
		getToken,
	};
}

/**
 * 認証チェック付きでコンポーネントをレンダリング
 * 認証されていない場合はローディングまたはリダイレクト
 *
 * @param children 認証が必要なコンポーネント
 * @param redirectTo リダイレクト先（デフォルト: /auth/signin）
 * @param loadingComponent ローディング中のコンポーネント
 *
 * @example
 * ```tsx
 * <AuthGuard>
 *   <AgencyProfilePage />
 * </AuthGuard>
 * ```
 */
export function AuthGuard({
	children,
	redirectTo = "/auth/signin",
	loadingComponent,
}: {
	children: React.ReactNode;
	redirectTo?: string;
	loadingComponent?: React.ReactNode;
}) {
	const { isAuthenticated, isLoaded } = useAuthCheck();
	const router = useRouter();

	useEffect(() => {
		if (isLoaded && !isAuthenticated) {
			router.push(redirectTo);
		}
	}, [isLoaded, isAuthenticated, router, redirectTo]);

	if (!isLoaded) {
		if (loadingComponent) {
			return loadingComponent;
		}
		return <div>読み込み中...</div>;
	}

	if (!isAuthenticated) {
		return null; // リダイレクト中
	}

	return <>{children}</>;
}

/**
 * ClerkのSignedIn/SignedOutコンポーネントを使用した認証ガード
 * Clerk公式クイックスタートパターンに準拠（推奨）
 * https://clerk.com/docs/nextjs/getting-started/quickstart
 *
 * SSR対応: 認証状態が読み込まれるまでローディングを表示
 *
 * @param children 認証が必要なコンポーネント
 * @param fallback 認証されていない場合に表示するコンポーネント（デフォルト: RedirectToSignIn）
 *
 * @example
 * ```tsx
 * export default function AgencyProfilePage() {
 *   return (
 *     <RequireAuth>
 *       <AgencyProfileContent />
 *     </RequireAuth>
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * <RequireAuth fallback={<div>ログインが必要です</div>}>
 *   <AgencyProfileContent />
 * </RequireAuth>
 * ```
 */
export function RequireAuth({
	children,
	fallback,
}: {
	children: ReactNode;
	fallback?: ReactNode;
}) {
	const { isLoaded } = useAuth();
	const { isLoaded: userLoaded } = useUser();

	// 認証状態が読み込まれるまでローディングを表示（SSR対応）
	if (!isLoaded || !userLoaded) {
		return (
			<div className="flex min-h-screen items-center justify-center">
				<div className="text-lg">読み込み中...</div>
			</div>
		);
	}

	return (
		<>
			<SignedIn>{children}</SignedIn>
			<SignedOut>{fallback || <RedirectToSignIn />}</SignedOut>
		</>
	);
}
