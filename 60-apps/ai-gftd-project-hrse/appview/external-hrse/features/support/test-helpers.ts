// @etzhayyim/cyber-freelance#TestHelpers
// BDDテスト用のヘルパー関数

/**
 * モックLLMServiceの結果を返す
 * 実際のLLMServiceの代わりに使用して、カバレッジを測定する
 */
export function createMockLLMResult(email: {
	from: string;
	to: string;
	subject: string;
}): {
	'entityType': "JobSeeker" | "Job" | "Agency" | "Unknown";
	confidence: number;
	'extractedData': Record<string, unknown>;
} {
	const subject = email.subject.toLowerCase();
	let entityType: "JobSeeker" | "Job" | "Agency" | "Unknown" = "Unknown";
	let confidence = 0.5;

	if (subject.includes("job") || subject.includes("position") || subject.includes("career")) {
		entityType = "Job";
		confidence = 0.9;
	} else if (
		subject.includes("application") ||
		subject.includes("resume") ||
		subject.includes("cv")
	) {
		entityType = "JobSeeker";
		confidence = 0.9;
	} else if (subject.includes("agency") || subject.includes("recruitment")) {
		entityType = "Agency";
		confidence = 0.9;
	}

	return {
		'entityType': entityType,
		confidence,
		'extractedData': {
			name: email.from.split("@")[0],
			email: email.from,
		},
	};
}

/**
 * モックRecordRouterServiceの結果を返す
 */
export function createMockRoutingResult(analysis: {
	success: boolean;
	'entityType': string | null;
	confidence: number | null;
	error: string | null;
}): {
	success: boolean;
	action: "created" | "updated" | "skipped" | null;
	entityType: string;
	entityId: string | null;
	message: string | null;
	error: string | null;
} {
	if (!analysis.success || analysis.error) {
		return {
			success: false,
			action: null,
			entityType: analysis.entityType || "",
			entityId: null,
			message: null,
			error: analysis.error || "Routing failed",
		};
	}

	const action = analysis.confidence && analysis.confidence > 0.7 ? "created" : "skipped";

	return {
		success: true,
		action,
		entityType: analysis.entityType || "",
		entityId: action === "created" ? `mock-${(analysis.entityType || "").toLowerCase()}-id` : null,
		message: action === "created" ? "Record created successfully" : "Record skipped",
		error: null,
	};
}
