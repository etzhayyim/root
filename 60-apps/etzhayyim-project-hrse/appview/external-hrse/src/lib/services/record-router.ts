// @etzhayyim/cyber-freelance#RecordRouter
// レコード振り分けサービス
// Connect-Web を使用してバックエンドと通信
// Go 側の RecordRouterService を呼び出す

import type { EmailAnalysisResult } from "@/lib/services/email-analyzer";
import type { EntityType } from "@/lib/llm/openai";
import { getRecordRouterServiceClient } from "@/lib/connect/server-client";
import { create } from "@bufbuild/protobuf";
import {
	RouteRecordRequestSchema,
} from "@/gen/proto/hrse/v1/record_router_pb";

export interface RoutingResult {
	success: boolean;
	action: "created" | "updated" | "skipped" | null;
	'entityType': EntityType | null;
	'entityId': string | null;
	message: string | null;
	error: string | null;
}

export async function routeRecord(
	analysis: EmailAnalysisResult,
): Promise<RoutingResult> {
	try {
		const client = await getRecordRouterServiceClient();

		// EmailAnalysisResult を RouteRecordRequest に変換
		const request = create(RouteRecordRequestSchema, {
			success: analysis.success,
			entityType: analysis.entityType || "",
			confidence: analysis.confidence ?? undefined,
			extractedData: analysis.extractedData as any,
			emailMetadata: analysis.emailMetadata
				? {
						from: analysis.emailMetadata.from,
						to: analysis.emailMetadata.to,
						subject: analysis.emailMetadata.subject,
						date: analysis.emailMetadata.date,
					}
				: undefined,
			error: analysis.error ?? undefined,
		});

		const response = await client.routeRecord(request);

		return {
			success: response.success,
			action: (response.action as "created" | "updated" | "skipped" | null) || null,
			'entityType': (response.entityType as EntityType | null) || null,
			'entityId': response.entityId || null,
			message: response.message || null,
			error: response.error || null,
		};
	} catch (error) {
		return {
			success: false,
			action: null,
			'entityType': analysis.entityType,
			'entityId': null,
			message: null,
			error: error instanceof Error ? error.message : "Unknown error",
		};
	}
}
