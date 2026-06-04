import { getMarketInfo, type MarketInfo } from './market-client.js';

let _market = $state<MarketInfo | null>(null);
let marketInterval: ReturnType<typeof setInterval> | null = null;

async function refreshMarketInternal() {
	try {
		_market = await getMarketInfo();
	} catch {
		// coordinator may be offline
	}
}

export function useProviderMarket() {
	return {
		get market() { return _market; },
		startPolling(intervalMs = 10000) {
			refreshMarketInternal();
			marketInterval = setInterval(refreshMarketInternal, intervalMs);
		},
		stopPolling() {
			if (marketInterval) {
				clearInterval(marketInterval);
				marketInterval = null;
			}
		},
	};
}
