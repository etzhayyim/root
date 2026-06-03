/**
 * yoro convo store — thin adapter over convos from $lib/atproto-agent.
 *
 * Provides backward-compatible property names used by yoro route files.
 */

import { convos } from '$lib/w';

export const yoroConvos = {
	get convoList() { return convos.convoList; },
	get activeConvoId() { return convos.activeConvoId; },
	get activeConvo() { return convos.activeConvo; },
	get activeConvoRecords() { return convos.activeConvoEnvelopes; },
	get isLoading() { return convos.isSyncing; },
	get directConvoIds() { return convos.snapshot?.directConvoIds ?? []; },

	setActiveConvo(convoId: string) { convos.setActiveConvo(convoId); },
	subscribe() { convos.subscribe(); },
	unsubscribe() { convos.unsubscribe(); },
	async refresh() { await convos.refresh(); },
	async loadMessages(_convoId: string) { await convos.refresh(); },
};
