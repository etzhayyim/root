"use client";

import { useUser, useAuth } from "@clerk/nextjs";
import { useState, useEffect } from "react";

/**
 * 認証状態を表示するデバッグパネル
 * 開発環境でのみ表示
 */
export function AuthDebugPanel() {
	const { user, isLoaded: userLoaded } = useUser();
	const { getToken, isLoaded: authLoaded, sessionId } = useAuth();
	const [tokenPreview, setTokenPreview] = useState<string | null>(null);
	const [fullToken, setFullToken] = useState<string | null>(null);
	const [tokenInfo, setTokenInfo] = useState<{
		isJWT: boolean;
		header?: any;
		payload?: any;
		parts?: string[];
	} | null>(null);
	const [loadingToken, setLoadingToken] = useState(false);
	const [showFullToken, setShowFullToken] = useState(false);
	const [isMounted, setIsMounted] = useState(false);

	// クライアント側でのみマウントされたことを確認（ハイドレーションエラーを防ぐ）
	useEffect(() => {
		setIsMounted(true);
	}, []);

	// JWTトークンを解析する関数
	const parseJWT = (token: string) => {
		try {
			const parts = token.split('.');
			if (parts.length !== 3) {
				return { isJWT: false, parts };
			}

			// Base64URLデコード（簡易実装）
			const base64UrlDecode = (str: string) => {
				// Base64URLをBase64に変換
				let base64 = str.replace(/-/g, '+').replace(/_/g, '/');
				// パディングを追加
				while (base64.length % 4) {
					base64 += '=';
				}
				try {
					const decoded = atob(base64);
					return JSON.parse(decoded);
				} catch (e) {
					return null;
				}
			};

			const header = base64UrlDecode(parts[0]);
			const payload = base64UrlDecode(parts[1]);

			return {
				isJWT: true,
				header,
				payload,
				parts: parts.map((p, i) => {
					if (i === 0) return `Header (${p.length} chars)`;
					if (i === 1) return `Payload (${p.length} chars)`;
					return `Signature (${p.length} chars)`;
				}),
			};
		} catch (error) {
			return { isJWT: false, error: error instanceof Error ? error.message : String(error) };
		}
	};

	const handleShowToken = async () => {
		if (!getToken) return;
		setLoadingToken(true);
		try {
			const token = await getToken();
			if (token) {
				// トークンの最初と最後の20文字のみを表示
				const preview = `${token.substring(0, 20)}...${token.substring(token.length - 20)}`;
				setTokenPreview(preview);
				setFullToken(token);

				// JWT形式のトークンの場合、解析情報を設定
				const parsed = parseJWT(token);
				setTokenInfo(parsed);
			} else {
				setTokenPreview("null");
				setFullToken(null);
				setTokenInfo(null);
			}
		} catch (error) {
			setTokenPreview(`Error: ${error instanceof Error ? error.message : String(error)}`);
			setFullToken(null);
			setTokenInfo(null);
		} finally {
			setLoadingToken(false);
		}
	};


	// 本番環境では表示しない
	if (process.env.NODE_ENV === "production") {
		return null;
	}

	return (
		<div className="fixed bottom-4 right-4 z-50 max-w-md rounded-lg border-2 border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20 p-4 shadow-lg backdrop-blur-sm" style={{ maxHeight: "80vh", overflowY: "auto", fontSize: "11px" }}>
			<div className="mb-2 flex items-center justify-between">
				<h3 className="text-sm font-bold text-yellow-900 dark:text-yellow-100">
					🔍 認証デバッグパネル
				</h3>
				<button
					type="button"
					onClick={() => window.location.reload()}
					className="rounded bg-yellow-600 px-2 py-1 text-xs text-white hover:bg-yellow-700"
				>
					再読み込み
				</button>
			</div>

			<div className="space-y-2 text-xs">
				<div className="flex items-center justify-between">
					<span className="font-semibold text-yellow-900 dark:text-yellow-100">User Loaded:</span>
					<span className={userLoaded ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"}>
						{userLoaded ? "✓ Yes" : "✗ No"}
					</span>
				</div>

				<div className="flex items-center justify-between">
					<span className="font-semibold text-yellow-900 dark:text-yellow-100">Auth Loaded:</span>
					<span className={authLoaded ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"}>
						{authLoaded ? "✓ Yes" : "✗ No"}
					</span>
				</div>

				<div className="flex items-center justify-between">
					<span className="font-semibold text-yellow-900 dark:text-yellow-100">User ID:</span>
					<span className="text-yellow-800 dark:text-yellow-200 font-mono text-xs">
						{user?.id || "null"}
					</span>
				</div>

				<div className="flex items-center justify-between">
					<span className="font-semibold text-yellow-900 dark:text-yellow-100">Email:</span>
					<span className="text-yellow-800 dark:text-yellow-200">
						{user?.primaryEmailAddress?.emailAddress || "null"}
					</span>
				</div>

				<div className="flex items-center justify-between">
					<span className="font-semibold text-yellow-900 dark:text-yellow-100">Session ID:</span>
					<span className="text-yellow-800 dark:text-yellow-200 font-mono text-xs">
						{sessionId || "null"}
					</span>
				</div>

				<div className="flex items-center justify-between" suppressHydrationWarning>
					<span className="font-semibold text-yellow-900 dark:text-yellow-100">getToken:</span>
					<span
						className={isMounted && typeof getToken === "function" ? "text-green-600 dark:text-green-400" : "text-yellow-600 dark:text-yellow-400"}
						suppressHydrationWarning
					>
						{!isMounted ? "⏳ Loading..." : (typeof getToken === "function" ? "✓ Available" : "✗ Not Available")}
					</span>
				</div>

				{tokenPreview && (
					<div className="mt-2 rounded bg-yellow-100 dark:bg-yellow-900/40 p-2">
						<div className="font-semibold text-yellow-900 dark:text-yellow-100 mb-1">Token Preview:</div>
						<div className="font-mono text-xs text-yellow-800 dark:text-yellow-200 break-all">
							{tokenPreview}
						</div>
						{tokenInfo?.isJWT && (
							<div className="mt-2 pt-2 border-t border-yellow-300 dark:border-yellow-700">
								<div className="text-xs font-semibold text-green-600 dark:text-green-400 mb-1">
									✓ JWT形式のトークン
								</div>
								{tokenInfo.parts && (
									<div className="text-xs text-yellow-800 dark:text-yellow-200 mb-2">
										<div>構造: {tokenInfo.parts.join(' + ')}</div>
									</div>
								)}
								{tokenInfo.header && (
									<div className="mb-2">
										<div className="text-xs font-semibold text-yellow-900 dark:text-yellow-100 mb-1">
											Header:
										</div>
										<pre className="text-xs bg-yellow-50 dark:bg-yellow-950 p-1 rounded overflow-x-auto">
											{JSON.stringify(tokenInfo.header, null, 2)}
										</pre>
									</div>
								)}
								{tokenInfo.payload && (
									<div className="mb-2">
										<div className="text-xs font-semibold text-yellow-900 dark:text-yellow-100 mb-1">
											Payload (Claims):
										</div>
										<pre className="text-xs bg-yellow-50 dark:bg-yellow-950 p-1 rounded overflow-x-auto max-h-40 overflow-y-auto">
											{JSON.stringify(tokenInfo.payload, null, 2)}
										</pre>
										{tokenInfo.payload.sub && (
											<div className="text-xs text-green-600 dark:text-green-400 mt-1">
												User ID (sub): {tokenInfo.payload.sub}
											</div>
										)}
										{tokenInfo.payload.exp && (
											<div className="text-xs text-yellow-700 dark:text-yellow-300 mt-1">
												Expires: {new Date(tokenInfo.payload.exp * 1000).toLocaleString()}
											</div>
										)}
									</div>
								)}
								{fullToken && (
									<div className="mt-2">
										<button
											type="button"
											onClick={() => setShowFullToken(!showFullToken)}
											className="text-xs text-yellow-700 dark:text-yellow-300 hover:underline"
										>
											{showFullToken ? "Hide" : "Show"} Full Token
										</button>
										{showFullToken && (
											<div className="mt-1 font-mono text-xs bg-yellow-50 dark:bg-yellow-950 p-2 rounded break-all max-h-32 overflow-y-auto">
												{fullToken}
											</div>
										)}
									</div>
								)}
							</div>
						)}
						{tokenInfo && !tokenInfo.isJWT && (
							<div className="mt-2 pt-2 border-t border-yellow-300 dark:border-yellow-700">
								<div className="text-xs text-yellow-600 dark:text-yellow-400">
									⚠ JWT形式ではありません（3 partsではありません）
								</div>
							</div>
						)}
					</div>
				)}

					<button
						type="button"
						onClick={handleShowToken}
						disabled={loadingToken || !isMounted || typeof getToken !== "function"}
						className="mt-2 w-full rounded bg-yellow-600 px-3 py-1 text-xs text-white hover:bg-yellow-700 disabled:opacity-50 disabled:cursor-not-allowed"
					>
						{loadingToken ? "Loading..." : "Show Token Preview"}
					</button>

					{/* Connect-Web 状態の表示 */}
					<div className="mt-3 pt-3 border-t border-yellow-300 dark:border-yellow-700">
						<div className="text-xs font-semibold text-yellow-900 dark:text-yellow-100 mb-1">
							Connect-Web 状態:
						</div>
						<div className="text-xs text-yellow-800 dark:text-yellow-200 mb-2">
							{isMounted && userLoaded && authLoaded && typeof getToken === "function" ? (
							<span className="text-green-600 dark:text-green-400">✓ Ready with token getter</span>
						) : (
							<span className="text-yellow-600 dark:text-yellow-400">⏳ Waiting for auth...</span>
						)}
					</div>
				</div>
			</div>
		</div>
	);
}
