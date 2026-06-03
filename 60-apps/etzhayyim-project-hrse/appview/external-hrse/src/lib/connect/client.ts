/**
 * @etzhayyim/etzhayyim-hrse#ConnectClient
 * Connect-Web クライアント設定
 *
 * Connect-RPC プロトコルを使用してバックエンドと通信
 */

import type { Interceptor } from "@connectrpc/connect";
import { createConnectTransport } from "@connectrpc/connect-web";

// Connect API URL
const CONNECT_API_URL = process.env.NEXT_PUBLIC_CONNECT_API_URL || "/xrpc-web";

function createAuthInterceptor(
  getToken?: () => Promise<string | null>,
): Interceptor | undefined {
  if (!getToken) return undefined;
  return (next) => async (req) => {
    try {
      const token = await getToken();
      if (token) {
        req.header.set("authorization", `Bearer ${token}`);
      }
    } catch {
      // Best-effort auth propagation.
    }
    return next(req);
  };
}

/**
 * Connect Transport の作成
 * クライアントサイドで使用するトランスポート
 */
export function createTransport(getToken?: () => Promise<string | null>) {
  const authInterceptor = createAuthInterceptor(getToken);
  return createConnectTransport({
    baseUrl: CONNECT_API_URL || "https://atproto.etzhayyim.com",
    ...(authInterceptor ? { interceptors: [authInterceptor] } : {}),
  });
}

/**
 * サーバーサイド用 Transport の作成
 * サーバーサイドで使用するトランスポート（内部通信）
 */
export function createServerTransport() {
  const serverUrl = process.env.CONNECT_API_URL || "http://localhost:8083";

  return createConnectTransport({
    baseUrl: serverUrl || "https://atproto.etzhayyim.com",
  });
}

/**
 * Client-side mailbox service client factory
 * For use in client components
 */
export async function getMailboxServiceClient() {
  const { useAuth } = await import("@clerk/nextjs");
  void useAuth;

  // This is a client-side function, so we need to get token dynamically
  // For now, return a function that creates the client
  return async () => {
    const { useAuth: useAuthHook } = await import("@clerk/nextjs");
    void useAuthHook;
    // Note: This won't work in a non-hook context
    // Better to use the hook pattern from hooks.ts
    throw new Error("Use useMailboxServiceClient hook instead");
  };
}
