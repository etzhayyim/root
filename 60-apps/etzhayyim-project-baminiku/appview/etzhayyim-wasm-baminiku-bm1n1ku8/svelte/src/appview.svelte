<script lang="ts">
	import type { ActorContext } from './lib/types';
	import { Gift, Send, X } from 'lucide-svelte';

	let { ctx }: { ctx: ActorContext } = $props();

	// ── Cypher proxy (via ActorContext) ──

	async function cypherQuery<T = Record<string, unknown>[]>(statement: string, parameters: Record<string, unknown> = {}): Promise<T> {
		return ctx.cypher.query(statement, parameters) as Promise<T>;
	}

	async function cypherExec(statement: string, parameters: Record<string, unknown> = {}): Promise<void> {
		return ctx.cypher.exec(statement, parameters);
	}

	// ── State ──
	let streamId = $state('');
	let convoId = $state('');
	let agentName = $state('');
	let agentAvatarUrl = $state('');
	let subtitle = $state('');
	let chatMessages = $state<Array<{ sender: string; text: string; type: string }>>([]);
	let chatInput = $state('');
	let sending = $state(false);
	let showTipModal = $state(false);
	let tipAmount = $state(100);
	let tipMessage = $state('');
	let tipAnimation = $state<{ amount: number; sender: string; effect: string } | null>(null);
	let error = $state<string | null>(null);

	// ── Audio context for lip sync ──
	let audioCtx: AudioContext | null = null;
	let analyser: AnalyserNode | null = null;
	let mouthOpen = $state(0);

	function ensureAudioCtx() {
		if (!audioCtx) {
			audioCtx = new AudioContext();
			analyser = audioCtx.createAnalyser();
			analyser.fftSize = 256;
		}
	}

	async function playTTS(blobKey: string) {
		if (!blobKey) return;
		ensureAudioCtx();
		try {
			const resp = await fetch(`https://atproto.etzhayyim.com/xrpc/com.etzhayyim.files.getBlob?nanoid=${ctx.nanoid}&key=${blobKey}`);
			const buf = await resp.arrayBuffer();
			const decoded = await audioCtx!.decodeAudioData(buf);
			const source = audioCtx!.createBufferSource();
			source.buffer = decoded;
			source.connect(analyser!);
			analyser!.connect(audioCtx!.destination);
			source.start();

			const dataArr = new Uint8Array(analyser!.frequencyBinCount);
			const animLoop = () => {
				analyser!.getByteFrequencyData(dataArr);
				let sum = 0;
				for (let i = 0; i < dataArr.length; i++) sum += dataArr[i];
				mouthOpen = Math.min(1, (sum / dataArr.length / 128));
				if (source.context.state === 'running') requestAnimationFrame(animLoop);
			};
			animLoop();
			source.onended = () => { mouthOpen = 0; };
		} catch { /* audio playback optional */ }
	}

	function genId(prefix: string) { return `${prefix}-${Date.now()}`; }
	function nowTS() { return new Date().toISOString(); }

	// ── Commands (browser Cypher proxy direct) ──

	async function createStream(agentId: string, title: string) {
		const sid = genId('stream');
		const chId = genId('ch');
		const now = nowTS();
		await cypherExec(`CREATE (s:Stream {
			'stream_id': '${sid}', 'org_id': 'anon', 'user_id': 'anon', 'actor_id': '',
			'agent_id': '${agentId}', title: '${title}', description: '',
			status: 'live', visibility: 'public', 'channel_id': '${chId}',
			'started_at': '${now}', 'ended_at': '', 'viewer_count': 0, 'peak_viewers': 0,
			'total_tips_jpy': 0, 'tip_count': 0, language: 'ja',
			'created_at': '${now}', 'updated_at': '${now}'
		})`);
		await cypherExec(`MATCH (a:AgentProfile {'agent_id': '${agentId}'}), (s:Stream {'stream_id': '${sid}'}) CREATE (a)-[:HOSTS]->(s)`);
		return { 'stream_id': sid, 'channel_id': chId };
	}

	async function sendChat() {
		if (!chatInput.trim() || !streamId) return;
		const text = chatInput.trim();
		chatInput = '';
		sending = true;
		error = null;

		chatMessages = [...chatMessages, { sender: 'You', text, type: 'viewer' }];

		try {
			// Agent response via murakumo LLM (outbound HTTP — only WASM op that needs server)
			// For MVP: echo response (LLM integration requires server-side AgentConverse)
			const agentReply = `Thanks for saying "${text}"! 🎤`;
			chatMessages = [...chatMessages, { sender: agentName || 'Agent', text: agentReply, type: 'agent' }];
			subtitle = agentReply;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Chat failed';
		} finally {
			sending = false;
		}
	}

	async function sendTip() {
		if (!streamId || tipAmount <= 0) return;
		error = null;
		try {
			const tipId = genId('tip');
			const now = nowTS();
			const effectType = tipAmount >= 10000 ? 'rainbow' : tipAmount >= 1000 ? 'gold' : 'normal';

			await cypherExec(`CREATE (t:Tip {
				'tip_id': '${tipId}', 'org_id': 'anon', 'user_id': 'anon', 'actor_id': '',
				'stream_id': '${streamId}', 'sender_did': '', 'sender_name': 'Viewer',
				amount: ${tipAmount}, currency: 'JPY',
				message: '${tipMessage.replace(/'/g, "\\'")}', 'effect_type': '${effectType}',
				'created_at': '${now}'
			})`);
			await cypherExec(`MATCH (t:Tip {'tip_id': '${tipId}'}), (s:Stream {'stream_id': '${streamId}'}) CREATE (t)-[:TIPPED_IN]->(s)`);
			await cypherExec(`MATCH (s:Stream {'stream_id': '${streamId}'}) SET s.total_tips_jpy = s.total_tips_jpy + ${tipAmount}, s.tip_count = s.tip_count + 1, s.updated_at = '${now}'`);

			tipAnimation = { amount: tipAmount, sender: 'Viewer', effect: effectType };
			chatMessages = [...chatMessages, {
				sender: 'Viewer', text: `Tipped ¥${tipAmount.toLocaleString()}${tipMessage ? ': ' + tipMessage : ''}`, type: 'tip'
			}];
			showTipModal = false;
			tipMessage = '';
			setTimeout(() => { tipAnimation = null; }, 3000);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Tip failed';
		}
	}

	// ── Queries (browser Cypher proxy direct) ──

	async function joinStream(sid: string) {
		try {
			const res = await cypherQuery<{ rows: string[][] }>(`MATCH (s:Stream {'stream_id': '${sid}'})
				OPTIONAL MATCH (a:AgentProfile)-[:HOSTS]->(s)
				RETURN s.stream_id, s.channel_id, s.title, s.status, a.display_name, a.avatar_model_url`);
			if (res.rows?.length > 0) {
				const r = res.rows[0];
				streamId = r[0] || sid;
				convoId = r[1] || '';
				agentName = r[4] || 'Agent';
				agentAvatarUrl = r[5] || '';
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to join stream';
		}
	}

	async function loadLiveStreams() {
		try {
			const res = await cypherQuery<{ rows: string[][] }>(`MATCH (s:Stream {status: 'live'}) RETURN s.stream_id LIMIT 1`);
			if (res.rows?.length > 0) {
				await joinStream(res.rows[0][0]);
			}
		} catch { /* no live streams */ }
	}

	loadLiveStreams();
</script>

<div style="display:flex;flex-direction:column;height:100%;max-width:440px;margin:0 auto;background:#0f0f1a;color:#fff;font-family:system-ui,sans-serif;">
	<!-- Avatar Canvas -->
	<div style="position:relative;flex:0 0 280px;background:linear-gradient(135deg,#1a1a2e,#16213e);display:flex;align-items:center;justify-content:center;overflow:hidden;">
		<!-- SVG Sprite Avatar (MVP) -->
		<svg viewBox="0 0 200 280" style="width:180px;height:260px;">
			<!-- Head -->
			<circle cx="100" cy="90" r="50" fill="#ffd6b0" />
			<!-- Eyes -->
			<ellipse cx="80" cy="80" rx="6" ry="7" fill="#333" />
			<ellipse cx="120" cy="80" rx="6" ry="7" fill="#333" />
			<!-- Mouth (lip sync) -->
			<ellipse cx="100" cy="108" rx="12" ry={4 + mouthOpen * 10} fill="#e55" />
			<!-- Hair -->
			<path d="M50 70 Q60 20 100 25 Q140 20 150 70 Q145 50 100 45 Q55 50 50 70Z" fill="#6366f1" />
			<!-- Body -->
			<rect x="70" y="140" width="60" height="80" rx="10" fill="#6366f1" />
			<!-- Arms -->
			<rect x="45" y="150" width="25" height="60" rx="8" fill="#6366f1" />
			<rect x="130" y="150" width="25" height="60" rx="8" fill="#6366f1" />
		</svg>

		<!-- Live badge -->
		{#if streamId}
			<div style="position:absolute;top:12px;left:12px;background:#e11d48;color:#fff;padding:2px 10px;border-radius:4px;font-size:12px;font-weight:700;letter-spacing:1px;">
				LIVE
			</div>
		{/if}

		<!-- Agent name -->
		<div style="position:absolute;bottom:0;left:0;right:0;padding:8px 12px;background:linear-gradient(transparent,rgba(0,0,0,0.7));">
			<div style="font-size:14px;font-weight:600;">{agentName || 'Waiting for stream...'}</div>
		</div>

		<!-- Subtitle bar -->
		{#if subtitle}
			<div style="position:absolute;bottom:36px;left:12px;right:12px;background:rgba(0,0,0,0.6);padding:6px 10px;border-radius:6px;font-size:13px;text-align:center;">
				{subtitle}
			</div>
		{/if}

		<!-- Tip animation overlay -->
		{#if tipAnimation}
			<div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;pointer-events:none;animation:tipFadeIn 0.3s ease-out;">
				<div style="font-size:32px;font-weight:800;text-shadow:0 0 20px {tipAnimation.effect === 'rainbow' ? '#ff0' : tipAnimation.effect === 'gold' ? '#ffd700' : '#fff'};color:{tipAnimation.effect === 'rainbow' ? '#ff6b6b' : tipAnimation.effect === 'gold' ? '#ffd700' : '#fff'};">
					¥{tipAnimation.amount.toLocaleString()}
				</div>
			</div>
		{/if}
	</div>

	<!-- Chat area -->
	<div style="flex:1;overflow-y:auto;padding:8px 12px;display:flex;flex-direction:column;gap:6px;">
		{#if error}
			<div style="background:#7f1d1d;color:#fca5a5;padding:8px 12px;border-radius:8px;font-size:13px;">{error}</div>
		{/if}

		{#if !streamId}
			<div style="text-align:center;color:#666;padding:40px 0;font-size:14px;">No live streams available</div>
		{/if}

		{#each chatMessages as msg}
			<div style="display:flex;gap:8px;align-items:flex-start;">
				<div style="font-size:12px;font-weight:600;color:{msg.type === 'agent' ? '#818cf8' : msg.type === 'tip' ? '#fbbf24' : '#9ca3af'};min-width:60px;">
					{msg.sender}
				</div>
				<div style="font-size:13px;color:{msg.type === 'tip' ? '#fde68a' : '#e5e7eb'};">
					{msg.text}
				</div>
			</div>
		{/each}
	</div>

	<!-- Bottom action bar -->
	<div style="flex:0 0 auto;padding:8px 12px;border-top:1px solid #1f2937;display:flex;gap:8px;align-items:center;">
		<input
			type="text"
			placeholder={streamId ? 'Say something...' : 'No stream'}
			bind:value={chatInput}
			disabled={!streamId || sending}
			onkeydown={(e) => { if (e.key === 'Enter') sendChat(); }}
			style="flex:1;background:#1f2937;border:none;border-radius:20px;padding:8px 14px;color:#fff;font-size:14px;outline:none;"
		/>
		<button
			onclick={sendChat}
			disabled={!streamId || sending || !chatInput.trim()}
			style="background:#6366f1;border:none;border-radius:50%;width:36px;height:36px;display:flex;align-items:center;justify-content:center;cursor:pointer;opacity:{!streamId || sending ? 0.4 : 1};"
		>
			<Send size={16} color="#fff" />
		</button>
		<button
			onclick={() => { showTipModal = true; }}
			disabled={!streamId}
			style="background:#e11d48;border:none;border-radius:50%;width:36px;height:36px;display:flex;align-items:center;justify-content:center;cursor:pointer;opacity:{!streamId ? 0.4 : 1};"
		>
			<Gift size={16} color="#fff" />
		</button>
	</div>

	<!-- Tip Modal -->
	{#if showTipModal}
		<div style="position:fixed;inset:0;background:rgba(0,0,0,0.6);display:flex;align-items:flex-end;justify-content:center;z-index:50;">
			<div style="background:#1f2937;border-radius:16px 16px 0 0;padding:20px;width:100%;max-width:440px;">
				<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
					<span style="font-size:16px;font-weight:600;">Send Tip</span>
					<button onclick={() => { showTipModal = false; }} style="background:none;border:none;cursor:pointer;">
						<X size={20} color="#9ca3af" />
					</button>
				</div>
				<div style="display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;">
					{#each [100, 500, 1000, 5000, 10000] as amt}
						<button
							onclick={() => { tipAmount = amt; }}
							style="padding:6px 14px;border-radius:20px;border:{tipAmount === amt ? '2px solid #e11d48' : '1px solid #374151'};background:{tipAmount === amt ? '#e11d4820' : 'transparent'};color:#fff;font-size:14px;cursor:pointer;"
						>
							¥{amt.toLocaleString()}
						</button>
					{/each}
				</div>
				<input
					type="text"
					placeholder="Message (optional)"
					bind:value={tipMessage}
					style="width:100%;background:#111827;border:1px solid #374151;border-radius:8px;padding:10px;color:#fff;font-size:14px;margin-bottom:12px;outline:none;box-sizing:border-box;"
				/>
				<button
					onclick={sendTip}
					style="width:100%;background:#e11d48;border:none;border-radius:8px;padding:12px;color:#fff;font-size:15px;font-weight:600;cursor:pointer;"
				>
					Send ¥{tipAmount.toLocaleString()}
				</button>
			</div>
		</div>
	{/if}
</div>

<style>
	@keyframes tipFadeIn {
		from { opacity: 0; transform: scale(0.5); }
		to { opacity: 1; transform: scale(1); }
	}
</style>
