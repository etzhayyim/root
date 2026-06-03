/**
 * Game bridge: sets up window.gftdBridgeSend → fetch /api/game/{convo}
 * and window.gftdBridgeReceive for Godot/HTML game responses.
 */

declare global {
	interface Window {
		gftdBridgeSend?: (msg: string) => void;
		gftdBridgeReceive?: (json: string) => void;
	}
}

export function setupGameBridge(appBaseUrl: string): () => void {
	window.gftdBridgeSend = async (msgJson: string) => {
		try {
			const msg = JSON.parse(msgJson);
			const convo = msg.convo as string;
			const payload = msg.payload as Record<string, unknown>;
			if (!convo) return;

			const resp = await fetch(`${appBaseUrl}/api/game/${convo}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(payload),
			});

			if (!resp.ok) return;

			const data = await resp.json();
			if (window.gftdBridgeReceive) {
				window.gftdBridgeReceive(JSON.stringify({ convo, payload: data }));
			}
		} catch {
			// Bridge errors are silently ignored — game continues
		}
	};

	return () => {
		delete window.gftdBridgeSend;
	};
}
