/**
 * @etzhayyim/etzhayyim-hrse#ConnectProxyRoute
 * Connect-RPC API Route - Connect-Go サーバーへのプロキシ
 *
 * クライアントからの Connect リクエストを Go バックエンドにプロキシします
 */

import { NextRequest, NextResponse } from "next/server";

// サーバーサイド用 Connect URL（コンテナ間通信用）
const CONNECT_API_URL = process.env.CONNECT_API_URL || "http://localhost:8083";

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
): Promise<NextResponse> {
  try {
    void request;
    const { path } = await params;
    const servicePath = path.join("/");
    const targetUrl = `${CONNECT_API_URL}/${servicePath}`;
    console.warn("[Connect Proxy] Unsupported direct proxy request:", targetUrl);
    return NextResponse.json(
      {
        code: "unimplemented",
        message:
          "Unsupported: dynamic Connect proxy forwarding is disabled. Use descriptor-backed Connect clients instead.",
        target: targetUrl,
      },
      { status: 501 }
    );
  } catch (error) {
    console.error("[Connect Route] Proxy error:", error);
    console.error("[Connect Route] Error details:", error instanceof Error ? error.stack : String(error));
    return NextResponse.json(
      {
        code: "internal",
        message: "Internal server error",
        details: error instanceof Error ? error.message : String(error)
      },
      { status: 500 }
    );
  }
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
): Promise<NextResponse> {
  const { path } = await params;
  return NextResponse.json({
    message: "Connect endpoint. Use POST method for RPC calls.",
    path: path.join("/"),
  });
}
