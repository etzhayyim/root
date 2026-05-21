// @etzhayyim/cyber-freelance#ServiceWrapper
// BDDテスト用のサービス関数ラッパー
// 循環依存を回避するために、遅延ロードを使用

let emailAnalyzerModule: typeof import("@/lib/services/email-analyzer.js") | null = null;
let recordRouterModule: typeof import("@/lib/services/record-router.js") | null = null;

/**
 * Email Analyzerサービスを遅延ロードして呼び出す
 */
export async function callAnalyzeEmail(
	email: import("@/lib/services/email-analyzer.js").EmailContent,
): Promise<import("@/lib/services/email-analyzer.js").EmailAnalysisResult> {
	if (!emailAnalyzerModule) {
		emailAnalyzerModule = await import("@/lib/services/email-analyzer.js");
	}
	return emailAnalyzerModule.analyzeEmail(email);
}

/**
 * Record Routerサービスを遅延ロードして呼び出す
 */
export async function callRouteRecord(
	analysis: import("@/lib/services/email-analyzer.js").EmailAnalysisResult,
): Promise<import("@/lib/services/record-router.js").RoutingResult> {
	if (!recordRouterModule) {
		recordRouterModule = await import("@/lib/services/record-router.js");
	}
	return recordRouterModule.routeRecord(analysis);
}
