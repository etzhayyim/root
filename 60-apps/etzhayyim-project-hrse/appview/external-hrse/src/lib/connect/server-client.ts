/**
 * @etzhayyim/etzhayyim-hrse#ConnectServerClient
 * Connect-Web サーバーサイドクライアント
 *
 * API Routes や Server Components で使用する Connect クライアント
 * サーバーサイドでは直接バックエンドに接続（プロキシ経由ではなく）
 */

import { AtpBaseClient } from "@etzhayyim/sdk/atproto";
import { auth as clerkAuth } from "@clerk/nextjs/server";

/**
 * サーバーサイド用 Connect URL
 * - Vercel環境: https://{VERCEL_URL}/xrpc-web (同一デプロイ内)
 * - ローカル環境: CONNECT_API_URL環境変数 または http://localhost:8083
 */
function getConnectApiUrl(): string {
  // 明示的にCONNECT_API_URLが設定されている場合はそれを優先
  if (process.env.CONNECT_API_URL) {
    return process.env.CONNECT_API_URL;
  }

  // Vercel環境の検出
  const isVercel = process.env.VERCEL === "1" || process.env.VERCEL_ENV !== undefined;

  if (isVercel) {
    // Vercel環境では同一デプロイ内のGo serverless functionを使用
    const vercelUrl = process.env.VERCEL_URL;
    if (vercelUrl) {
      return `https://${vercelUrl}/xrpc-web`;
    }

    // フォールバック: NEXT_PUBLIC_APP_URLを使用
    const appUrl = process.env.NEXT_PUBLIC_APP_URL;
    if (appUrl) {
      return `${appUrl}/xrpc-web`;
    }

    // 最終フォールバック: 本番ドメイン
    return "https://hrse.etzhayyim.com/xrpc-web";
  }

  // ローカル開発環境
  return "http://localhost:8083";
}

const CONNECT_API_URL = getConnectApiUrl();

/**
 * サーバーサイドで使用する Connect クライアントを作成
 * Clerk の認証トークンを自動的に取得して設定
 */
export async function getServerConnectClient<T>(Service: T) {
  void Service;
  const { getToken } = await clerkAuth();
  const transport = new AtpBaseClient({
    service: () => CONNECT_API_URL || "https://atproto.etzhayyim.com",
  });

  const getClerkToken = async (): Promise<string | null> => {
    try {
      return await getToken();
    } catch {
      return null;
    }
  };

  const auth = {
    async resolve() {
      const h: Record<string, string> = { "content-type": "application/json" };
      const token = await getClerkToken();
      if (token) h["authorization"] = `Bearer ${token}`;
      return h;
    },
  };

  async function connectPost<T>(method: string, body = {}): Promise<T> {
    const headers = await auth.resolve();
    const response = await transport.call(`com.etzhayyim.apps.hrse.${method}`, undefined, body, { headers });
    return response.data as T;
  }

  console.log("[Server Connect Client] Using baseUrl:", CONNECT_API_URL);

  return new Proxy(
    {},
    {
      get(_target, prop) {
        if (typeof prop !== "string") {
          return undefined;
        }
        return (request: Record<string, unknown> = {}) => connectPost(prop, request);
      },
    },
  ) as any;
}

/**
 * JobSeekerService のサーバーサイドクライアントを取得
 */
export async function getJobSeekerServiceClient() {
  return getServerConnectClient("JobSeekerService");
}

/**
 * AgencyService のサーバーサイドクライアントを取得
 */
export async function getAgencyServiceClient() {
  return getServerConnectClient("AgencyService");
}

/**
 * JobService のサーバーサイドクライアントを取得
 */
export async function getJobServiceClient() {
  return getServerConnectClient("JobService");
}

/**
 * AdminService のサーバーサイドクライアントを取得
 */
export async function getAdminServiceClient() {
  return getServerConnectClient("AdminService");
}

/**
 * RecordRouterService のサーバーサイドクライアントを取得
 */
export async function getRecordRouterServiceClient() {
  return getServerConnectClient("RecordRouterService");
}

/**
 * EmailAgentService のサーバーサイドクライアントを取得
 */
export async function getEmailAgentServiceClient() {
  return getServerConnectClient("EmailAgentService");
}

/**
 * MailboxService のサーバーサイドクライアントを取得
 */
export async function getMailboxServiceClient() {
  return getServerConnectClient("MailboxService");
}
