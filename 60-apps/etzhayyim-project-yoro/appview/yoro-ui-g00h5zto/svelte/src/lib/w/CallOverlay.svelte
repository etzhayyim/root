<script lang="ts">
	import { Button } from '@etzhayyim/design-system';
	import { sendCallOffer, sendCallAnswer, sendCallICE, hangupCall, memberLabel, getICEServers } from '$lib/atproto-agent';
	import type { Did, ConvoId, CallSignal } from '$lib/atproto-agent';

	interface Props {
		convoId: ConvoId;
		selfDid: Did;
		peerDid: Did;
		/** Incoming call signal to answer. If undefined, this is an outgoing call. */
		incomingOffer?: CallSignal;
		mediaType?: 'audio' | 'video';
		onClose?: () => void;
	}

	let {
		convoId,
		selfDid,
		peerDid,
		incomingOffer,
		mediaType = 'audio',
		onClose,
	}: Props = $props();

	type CallState = 'idle' | 'ringing' | 'connecting' | 'active' | 'ended';
	let callState = $state<CallState>('idle');
	let callId = $state(`call_${Date.now()}`);
	let duration = $state(0);
	let durationInterval = $state<ReturnType<typeof setInterval> | null>(null);

	// ── WebRTC state ──
	let pc = $state<RTCPeerConnection | null>(null);
	let localStream = $state<MediaStream | null>(null);
	let remoteStream = $state<MediaStream | null>(null);
	let localVideoEl: HTMLVideoElement | undefined = $state();
	let remoteVideoEl: HTMLVideoElement | undefined = $state();

	$effect(() => {
		if (incomingOffer && callState === 'idle') {
			callState = 'ringing';
			callId = incomingOffer.callId;
		}
	});

	// Bind remote stream to video element
	$effect(() => {
		if (remoteVideoEl && remoteStream) {
			remoteVideoEl.srcObject = remoteStream;
		}
	});
	$effect(() => {
		if (localVideoEl && localStream) {
			localVideoEl.srcObject = localStream;
		}
	});

	// Cleanup on unmount
	$effect(() => {
		return () => {
			cleanup();
		};
	});

	function startTimer() {
		duration = 0;
		durationInterval = setInterval(() => { duration += 1; }, 1000);
	}

	function stopTimer() {
		if (durationInterval) { clearInterval(durationInterval); durationInterval = null; }
	}

	function formatDuration(secs: number): string {
		const m = Math.floor(secs / 60);
		const s = secs % 60;
		return `${m}:${s.toString().padStart(2, '0')}`;
	}

	function cleanup() {
		stopTimer();
		localStream?.getTracks().forEach(t => t.stop());
		localStream = null;
		remoteStream = null;
		pc?.close();
		pc = null;
	}

	async function createPeerConnection(): Promise<RTCPeerConnection> {
		const iceServers = await getICEServers();
		const conn = new RTCPeerConnection({ iceServers });

		// Send ICE candidates to peer via AT Protocol signaling
		conn.onicecandidate = (ev) => {
			if (ev.candidate) {
				sendCallICE(convoId, callId, ev.candidate.candidate, ev.candidate.sdpMid ?? undefined, ev.candidate.sdpMLineIndex ?? undefined);
			}
		};

		conn.onconnectionstatechange = () => {
			if (conn.connectionState === 'connected') {
				callState = 'active';
				startTimer();
			} else if (conn.connectionState === 'failed' || conn.connectionState === 'disconnected' || conn.connectionState === 'closed') {
				if (callState === 'active' || callState === 'connecting') {
					handleHangup();
				}
			}
		};

		// Receive remote tracks
		const rs = new MediaStream();
		remoteStream = rs;
		conn.ontrack = (ev) => {
			ev.streams[0]?.getTracks().forEach(t => rs.addTrack(t));
		};

		return conn;
	}

	async function acquireMedia(): Promise<MediaStream> {
		const constraints: MediaStreamConstraints = mediaType === 'video'
			? { audio: true, video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } } }
			: { audio: true, video: false };
		return navigator.mediaDevices.getUserMedia(constraints);
	}

	// ── Outgoing call ──
	async function handleCall() {
		callState = 'connecting';
		try {
			localStream = await acquireMedia();
			const conn = await createPeerConnection();
			pc = conn;
			localStream.getTracks().forEach(t => conn.addTrack(t, localStream!));

			const offer = await conn.createOffer();
			await conn.setLocalDescription(offer);
			await sendCallOffer(convoId, peerDid, callId, offer.sdp!, mediaType);
		} catch {
			callState = 'ended';
			cleanup();
		}
	}

	// ── Answer incoming call ──
	async function handleAnswer() {
		if (!incomingOffer?.sdp) return;
		callState = 'connecting';
		try {
			localStream = await acquireMedia();
			const conn = await createPeerConnection();
			pc = conn;
			localStream.getTracks().forEach(t => conn.addTrack(t, localStream!));

			await conn.setRemoteDescription(new RTCSessionDescription({ type: 'offer', sdp: incomingOffer.sdp }));
			const answer = await conn.createAnswer();
			await conn.setLocalDescription(answer);
			await sendCallAnswer(convoId, callId, answer.sdp!);
		} catch {
			callState = 'ended';
			cleanup();
		}
	}

	// ── Handle incoming answer SDP (called externally when peer answers) ──
	export async function handleRemoteAnswer(sdp: string) {
		if (pc && pc.signalingState === 'have-local-offer') {
			await pc.setRemoteDescription(new RTCSessionDescription({ type: 'answer', sdp }));
		}
	}

	// ── Handle incoming ICE candidate (called externally) ──
	export async function handleRemoteICE(candidate: string, sdpMid?: string, sdpMLineIndex?: number) {
		if (pc) {
			await pc.addIceCandidate(new RTCIceCandidate({
				candidate,
				sdpMid: sdpMid ?? null,
				sdpMLineIndex: sdpMLineIndex ?? null,
			}));
		}
	}

	export async function handleHangup() {
		cleanup();
		callState = 'ended';
		try {
			await hangupCall(convoId, callId, 'user_hangup');
		} catch { /* ignore */ }
		setTimeout(() => { onClose?.(); }, 1500);
	}

	async function handleDecline() {
		cleanup();
		callState = 'ended';
		try {
			await hangupCall(convoId, callId, 'declined');
		} catch { /* ignore */ }
		setTimeout(() => { onClose?.(); }, 500);
	}
</script>

<!-- Call overlay — full-screen dark overlay anchored at the center -->
<div class="fixed inset-0 z-[60] flex flex-col items-center justify-center bg-black/95 backdrop-blur-xl">
	<!-- Remote video (full background when video call active) -->
	{#if mediaType === 'video' && remoteStream}
		<video
			bind:this={remoteVideoEl}
			autoplay
			playsinline
			class="absolute inset-0 h-full w-full object-cover"
		></video>
	{/if}

	<!-- Local video preview (picture-in-picture) -->
	{#if mediaType === 'video' && localStream}
		<video
			bind:this={localVideoEl}
			autoplay
			playsinline
			muted
			class="absolute top-4 right-4 z-10 h-32 w-24 rounded-xl object-cover border-2 border-white/20"
		></video>
	{/if}

	<!-- Peer info -->
	<div class="relative z-10 flex flex-col items-center gap-4 mb-8">
		{#if !(mediaType === 'video' && callState === 'active')}
			<div class="flex h-24 w-24 items-center justify-center rounded-full bg-[var(--gv2-accent,#06c755)]/20 text-[32px] font-bold text-[var(--gv2-accent,#06c755)]">
				{memberLabel(peerDid).slice(0, 2).toUpperCase()}
			</div>
			<p class="text-[20px] font-bold text-white">{memberLabel(peerDid)}</p>
		{/if}
		<p class="text-[14px] text-white/50">
			{#if callState === 'idle'}
				{mediaType === 'video' ? 'Video call' : 'Voice call'}
			{:else if callState === 'ringing'}
				Incoming {mediaType} call...
			{:else if callState === 'connecting'}
				Connecting...
			{:else if callState === 'active'}
				{formatDuration(duration)}
			{:else}
				Call ended
			{/if}
		</p>
	</div>

	<!-- Action buttons -->
	<div class="relative z-10 flex items-center gap-6">
		{#if callState === 'idle'}
			<button
				type="button"
				class="flex h-16 w-16 items-center justify-center rounded-full bg-[var(--gv2-accent,#06c755)] text-white shadow-lg touch-manipulation active:scale-95 transition-transform"
				onclick={handleCall}
				aria-label="Start call"
			>
				<svg class="h-7 w-7" viewBox="0 0 24 24" fill="currentColor">
					<path d="M20.01 15.38c-1.23 0-2.42-.2-3.53-.56a.977.977 0 00-1.01.24l-1.57 1.97c-2.83-1.35-5.48-3.9-6.89-6.83l1.95-1.66c.27-.28.35-.67.24-1.02-.37-1.11-.56-2.3-.56-3.53 0-.54-.45-.99-.99-.99H4.19C3.65 3 3 3.24 3 3.99 3 13.28 10.73 21 20.01 21c.71 0 .99-.63.99-1.18v-3.45c0-.54-.45-.99-.99-.99z" />
				</svg>
			</button>
			<button
				type="button"
				class="flex h-12 w-12 items-center justify-center rounded-full bg-white/10 text-white/60 touch-manipulation active:scale-95 transition-transform"
				onclick={() => onClose?.()}
				aria-label="Cancel"
			>
				<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M18 6L6 18M6 6l12 12" /></svg>
			</button>
		{:else if callState === 'ringing'}
			<!-- Answer -->
			<button
				type="button"
				class="flex h-16 w-16 items-center justify-center rounded-full bg-[var(--gv2-accent,#06c755)] text-white shadow-lg touch-manipulation active:scale-95 transition-transform animate-pulse"
				onclick={handleAnswer}
				aria-label="Answer"
			>
				<svg class="h-7 w-7" viewBox="0 0 24 24" fill="currentColor">
					<path d="M20.01 15.38c-1.23 0-2.42-.2-3.53-.56a.977.977 0 00-1.01.24l-1.57 1.97c-2.83-1.35-5.48-3.9-6.89-6.83l1.95-1.66c.27-.28.35-.67.24-1.02-.37-1.11-.56-2.3-.56-3.53 0-.54-.45-.99-.99-.99H4.19C3.65 3 3 3.24 3 3.99 3 13.28 10.73 21 20.01 21c.71 0 .99-.63.99-1.18v-3.45c0-.54-.45-.99-.99-.99z" />
				</svg>
			</button>
			<!-- Decline -->
			<button
				type="button"
				class="flex h-16 w-16 items-center justify-center rounded-full bg-red-500 text-white shadow-lg touch-manipulation active:scale-95 transition-transform"
				onclick={handleDecline}
				aria-label="Decline"
			>
				<svg class="h-7 w-7 rotate-[135deg]" viewBox="0 0 24 24" fill="currentColor">
					<path d="M20.01 15.38c-1.23 0-2.42-.2-3.53-.56a.977.977 0 00-1.01.24l-1.57 1.97c-2.83-1.35-5.48-3.9-6.89-6.83l1.95-1.66c.27-.28.35-.67.24-1.02-.37-1.11-.56-2.3-.56-3.53 0-.54-.45-.99-.99-.99H4.19C3.65 3 3 3.24 3 3.99 3 13.28 10.73 21 20.01 21c.71 0 .99-.63.99-1.18v-3.45c0-.54-.45-.99-.99-.99z" />
				</svg>
			</button>
		{:else if callState === 'active' || callState === 'connecting'}
			<!-- Hangup -->
			<button
				type="button"
				class="flex h-16 w-16 items-center justify-center rounded-full bg-red-500 text-white shadow-lg touch-manipulation active:scale-95 transition-transform"
				onclick={handleHangup}
				aria-label="Hang up"
			>
				<svg class="h-7 w-7 rotate-[135deg]" viewBox="0 0 24 24" fill="currentColor">
					<path d="M20.01 15.38c-1.23 0-2.42-.2-3.53-.56a.977.977 0 00-1.01.24l-1.57 1.97c-2.83-1.35-5.48-3.9-6.89-6.83l1.95-1.66c.27-.28.35-.67.24-1.02-.37-1.11-.56-2.3-.56-3.53 0-.54-.45-.99-.99-.99H4.19C3.65 3 3 3.24 3 3.99 3 13.28 10.73 21 20.01 21c.71 0 .99-.63.99-1.18v-3.45c0-.54-.45-.99-.99-.99z" />
				</svg>
			</button>
		{:else}
			<button
				type="button"
				class="flex h-12 w-12 items-center justify-center rounded-full bg-white/10 text-white/60 touch-manipulation active:scale-95 transition-transform"
				onclick={() => onClose?.()}
				aria-label="Close"
			>
				<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M18 6L6 18M6 6l12 12" /></svg>
			</button>
		{/if}
	</div>
</div>
