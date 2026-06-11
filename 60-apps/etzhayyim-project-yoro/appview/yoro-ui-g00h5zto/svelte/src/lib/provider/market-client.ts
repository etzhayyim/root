export interface MarketInfo {
	'totalWorkers': number;
	'availableWorkers': number;
	'expertCounts': Record<number, number>;
	'avgPricePerCc': number;
	'auditRate': number;
	'totalJobsServed': number;
}

export interface ExpertRecommendation {
	'expertId': number;
	'modelId': string;
	'pricePerCc': number;
	coverage: number;
	reason: string;
}

const WEB4_API_BASE = 'https://web4.etzhayyim.com/api/v1';
const WEB4_XRPC_BASE = 'https://web4.etzhayyim.com/xrpc';

export async function getMarketInfo(): Promise<MarketInfo> {
	const resp = await fetch(`${WEB4_API_BASE}/market`);
	if (!resp.ok) throw new Error(`API error ${resp.status}`);
	return resp.json();
}

export async function recommendExpert(modelId?: string, providerMode?: string): Promise<ExpertRecommendation> {
	const body: Record<string, unknown> = {};
	if (modelId) body.modelId = modelId;
	if (providerMode) body.providerMode = providerMode;
	const resp = await fetch(`${WEB4_XRPC_BASE}/com.etzhayyim.web4.v1.recommendExpert`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body),
	});
	if (!resp.ok) throw new Error(`RecommendExpert API error ${resp.status}`);
	const data = await resp.json();
	return (data.value ?? data) as ExpertRecommendation;
}
