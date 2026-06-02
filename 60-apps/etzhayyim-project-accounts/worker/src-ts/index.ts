// SCAFFOLD ONLY (ADR-0024 Step 3)
// 本 Worker はまだ deploy しない。wrangler.jsonc.disabled が有効化される PR で
// auth Worker から以下の handler を移設する。
//
// 移設対象 (auth Worker src-ts/index.ts):
//   - GET  /manage                                    (Svelte SPA delegate)
//   - GET  /api/accounts/session                      → handleAccountsSession
//   - POST /xrpc/com.etzhayyim.auth.linkEmailBegin          → handleLinkEmailBegin
//   - POST /xrpc/com.etzhayyim.auth.linkEmailVerify         → handleLinkEmailVerify
//   - POST /xrpc/com.etzhayyim.auth.linkOAuthStart          → handleLinkOAuthStart
//   - POST /xrpc/com.etzhayyim.auth.unlinkMethod            → handleUnlinkMethod
//   - GET  /oauth/link/google/callback                → handleOAuthLinkCallback
//   - GET  /oauth/link/microsoft/callback             → handleOAuthLinkCallback
//
// NSID rename (ADR-0024 責務マトリクス):
//   com.etzhayyim.auth.linkEmailBegin    → com.etzhayyim.accounts.linkEmailBegin
//   com.etzhayyim.auth.linkEmailVerify   → com.etzhayyim.accounts.linkEmailVerify
//   com.etzhayyim.auth.linkOAuthStart    → com.etzhayyim.accounts.linkOAuthStart
//   com.etzhayyim.auth.unlinkMethod      → com.etzhayyim.accounts.unlinkMethod
// 旧 NSID は 90 日 alias 期間で受け付ける。

interface Env {
  ACCOUNTS_DB: D1Database;
  AUTH_SERVICE: Fetcher;
  ASSETS?: Fetcher;
  GOOGLE_OAUTH_CLIENT_ID?: string;
  GOOGLE_OAUTH_CLIENT_SECRET?: string;
  MICROSOFT_OAUTH_CLIENT_ID?: string;
  MICROSOFT_OAUTH_CLIENT_SECRET?: string;
}

export default {
  async fetch(_request: Request, _env: Env): Promise<Response> {
    return new Response("accounts.etzhayyim.com scaffold — not yet deployed (ADR-0024 Step 3)", {
      status: 501,
      headers: { "content-type": "text/plain" },
    });
  },
};
