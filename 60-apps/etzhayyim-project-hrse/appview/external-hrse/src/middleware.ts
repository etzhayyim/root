import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

// /auth/signup/complete は認証必須のため、パブリックルートから除外
const isSignupCompleteRoute = createRouteMatcher(["/auth/signup/complete(.*)"]);

const isPublicRoute = createRouteMatcher([
	"/",
	"/auth/signin(.*)",
	"/auth/signup(.*)", // /auth/signup/complete は下のチェックで除外される
	"/api/webhooks(.*)",
	"/api/connect(.*)", // Connect-Go API（バックエンド側で認証/認可を実施）
]);

// 動的ルート（[orgId]を含む）も認証必須
const isDynamicRoute = createRouteMatcher([
	"/(.*)/agency(.*)",
]);

const isAdminRoute = createRouteMatcher(["/admin(.*)"]);

function emitMiddlewareDebug(
	location: string,
	message: string,
	data: Record<string, unknown>,
	hypothesisId: string,
): void {
	if (process.env.NODE_ENV !== "development") return;
	console.debug("[middleware-debug][unsupported-network-sink]", {
		location,
		message,
		data,
		hypothesisId,
		timestamp: Date.now(),
		sessionId: "debug-session",
	});
}

export default clerkMiddleware(async (auth, request) => {
	// #region agent log
	emitMiddlewareDebug("middleware.ts:22", "Middleware entry", {
		pathname: request.nextUrl.pathname,
		search: request.nextUrl.search,
		method: request.method,
	}, "A,B,C,D");
	// #endregion

	// /auth/signup/complete は認証必須（パブリックルートより先にチェック）
	if (isSignupCompleteRoute(request)) {
		// #region agent log
		emitMiddlewareDebug("middleware.ts:24", "Signup complete route detected", {
			pathname: request.nextUrl.pathname,
		}, "B");
		// #endregion
		await auth.protect();
		return;
	}

	// パブリックルート以外は認証必須
	if (!isPublicRoute(request)) {
		// #region agent log
		emitMiddlewareDebug("middleware.ts:30", "Non-public route - protecting", {
			pathname: request.nextUrl.pathname,
		}, "C");
		// #endregion
		const authState = await auth.protect();
		// #region agent log
		emitMiddlewareDebug("middleware.ts:31", "Auth state after protect", {
			orgId: authState.orgId,
			userId: authState.userId,
			pathname: request.nextUrl.pathname,
		}, "C");
		// #endregion

		// SSRリダイレクト: /agency/* などに orgId なしで来た場合、clerkOrgId（active org）を付与
		const url = request.nextUrl;
		const pathname = url.pathname;
		const search = url.search;

		// /agency/* または /agency-recruiter/* パスで org プレフィックスが必要かチェック
		const isOrgPrefixed = /^\/[^/]+\/(agency|agency-recruiter)(\/|$)/.test(pathname);
		const needsOrgPrefix =
			!isOrgPrefixed &&
			(pathname.startsWith("/agency") || pathname.startsWith("/agency-recruiter"));

		// #region agent log
		emitMiddlewareDebug("middleware.ts:38-44", "Redirect check", {
			pathname,
			isOrgPrefixed,
			needsOrgPrefix,
			hasOrgId: !!authState.orgId,
			orgId: authState.orgId,
		}, "A,B,D");
		// #endregion

		if (needsOrgPrefix && authState.orgId) {
			const redirectPath = `/${authState.orgId}${pathname}${search}`;
			// #region agent log
			emitMiddlewareDebug("middleware.ts:43-44", "Redirecting to orgId path", {
				from: pathname,
				to: redirectPath,
			}, "B");
			// #endregion
			return NextResponse.redirect(new URL(redirectPath, url));
		}
		// #region agent log
		emitMiddlewareDebug("middleware.ts:46", "No redirect needed - continuing", {
			pathname,
			isOrgPrefixed,
			needsOrgPrefix,
		}, "A,D");
		// #endregion
	}

	// 動的ルート（組織IDを含む）も認証必須
	if (isDynamicRoute(request)) {
		await auth.protect();
	}

	// 管理ページは認証必須（将来的に管理者ロールチェックを追加可能）
	if (isAdminRoute(request)) {
		await auth.protect();
	}
});

export const config = {
	matcher: [
		// Skip Next.js internals and all static files, unless found in search params
		"/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
		// Always run for API routes
		"/(api|trpc)(.*)",
	],
};
