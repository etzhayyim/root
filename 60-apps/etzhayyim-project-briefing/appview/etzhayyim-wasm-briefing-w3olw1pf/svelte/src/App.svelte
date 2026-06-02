<script lang="ts">
  import { onMount } from 'svelte';

  const SIGNAL_URL = 'wss://briefing-signal.etzhayyim.com';
  const SIGNAL_HTTP = 'https://briefing-signal.etzhayyim.com';
  const ICE_SERVERS: RTCIceServer[] = [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' },
    { urls: 'stun:stun.cloudflare.com:3478' },
  ];

  /** Multi-DID Actor members for briefing projects. */
  const PROJECT_ACTORS = [
    { did: 'did:web:briefing.etzhayyim.com:actor:transcriber', role: 'Transcription', description: 'Speech-to-text via Whisper' },
    { did: 'did:web:briefing.etzhayyim.com:actor:translator', role: 'Translation', description: 'Auto-translate via LLM' },
    { did: 'did:web:briefing.etzhayyim.com:actor:recorder', role: 'Recording', description: 'Audio recording + R2 storage' },
    { did: 'did:web:briefing.etzhayyim.com:actor:summarizer', role: 'Summarizer', description: 'Meeting summary generation' },
  ];

  let roomId = $state('');
  let displayName = $state('');
  let embedMode = $state(false);
  let myPeerId = `peer-${Math.random().toString(36).slice(2, 8)}`;
  let status = $state<'idle' | 'media' | 'joining' | 'joined'>('idle');
  let mediaError = $state('');
  let localStream = $state<MediaStream | null>(null);
  let remotePeers = $state<Map<string, { name: string; stream: MediaStream | null; state: string }>>(new Map());
  let eventLog = $state<string[]>([]);
  let audioMuted = $state(false);
  let videoOff = $state(false);

  // Recording state
  let isRecording = $state(false);
  let recordingDuration = $state(0);
  let recordingStatus = $state<'' | 'recording' | 'uploading' | 'transcribing' | 'translating' | 'done'>('');
  let mediaRecorder: MediaRecorder | null = null;
  let recordingChunks: Blob[] = [];
  let recordingTimer: number | null = null;

  // Transcript state
  let transcript = $state<{ text: string; translatedText: string; language: string } | null>(null);

  // Convo project state
  let convoId = $state('');
  let projectActors = $state<typeof PROJECT_ACTORS>([]);

  let localVideoEl: HTMLVideoElement | undefined = $state(undefined);
  let ws: WebSocket | null = null;
  let peerConnections: Map<string, RTCPeerConnection> = new Map();

  // Reactive: bind localStream to video element whenever either changes
  $effect(() => {
    if (localVideoEl && localStream) {
      localVideoEl.srcObject = localStream;
    }
  });

  // Auto-join from URL params (?embed=1&room=xxx or ?room=xxx)
  onMount(() => {
    const params = new URLSearchParams(window.location.search);
    const urlRoom = params.get('room');
    if (params.has('embed')) embedMode = true;
    if (urlRoom) {
      roomId = urlRoom;
      // Auto-join after a tick
      setTimeout(() => requestMedia(), 100);
    }
  });

  function log(msg: string) {
    const ts = new Date().toLocaleTimeString();
    eventLog = [`[${ts}] ${msg}`, ...eventLog.slice(0, 49)];
  }

  // ─── Step 1: Get camera/mic permission BEFORE joining ───

  async function requestMedia() {
    if (!roomId.trim()) roomId = `room-${Date.now()}`;
    status = 'media';
    mediaError = '';
    try {
      localStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: true });
      // $effect will bind to video element
      log('Camera + mic ready');
    } catch (e: any) {
      // Fallback: try audio only
      try {
        localStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
        log('Mic only (no camera)');
      } catch {
        // Fallback: try video only
        try {
          localStream = await navigator.mediaDevices.getUserMedia({ audio: false, video: true });
          // $effect will bind to video element
          log('Camera only (no mic)');
        } catch {
          const msg = e.name === 'NotAllowedError'
            ? 'Blocked. Click lock icon in address bar to allow.'
            : 'No camera/mic found on this device.';
          mediaError = msg;
          log(`Media: ${msg}`);
        }
      }
    }
    // Join room regardless of media result
    connectSignaling();
  }

  // ─── Step 2: WebSocket signaling ───

  function connectSignaling() {
    const name = displayName.trim() || myPeerId;
    const url = `${SIGNAL_URL}/rooms/${encodeURIComponent(roomId)}/ws`;
    log(`Connecting to room: ${roomId}`);
    status = 'joining';

    ws = new WebSocket(url);

    ws.onopen = () => {
      log('Connected');
      ws!.send(JSON.stringify({ type: 'join', peerId: myPeerId, displayName: name }));
      status = 'joined';
      createProject();
    };

    ws.onmessage = async (ev) => {
      try {
        await handleSignal(JSON.parse(ev.data));
      } catch (e: any) {
        console.warn('[signal]', e);
      }
    };

    ws.onclose = () => {
      log('Disconnected');
      if (status === 'joined') leaveRoom();
    };

    ws.onerror = () => log('Connection error');
  }

  async function handleSignal(msg: any) {
    switch (msg.type) {
      case 'peers':
        log(`${msg.peers.length} peer(s) in room`);
        for (const p of msg.peers) {
          remotePeers.set(p.peerId, { name: p.displayName, stream: null, state: 'connecting' });
          await createPeerConnection(p.peerId, true);
        }
        remotePeers = new Map(remotePeers);
        break;

      case 'peer-joined':
        log(`${msg.displayName} joined`);
        remotePeers.set(msg.peerId, { name: msg.displayName, stream: null, state: 'new' });
        remotePeers = new Map(remotePeers);
        break;

      case 'peer-left':
        log(`${remotePeers.get(msg.peerId)?.name ?? msg.peerId} left`);
        closePeerConnection(msg.peerId);
        remotePeers.delete(msg.peerId);
        remotePeers = new Map(remotePeers);
        break;

      case 'offer':
        log(`Offer from ${remotePeers.get(msg.from)?.name ?? msg.from}`);
        await handleOffer(msg.from, msg.sdp);
        break;

      case 'answer':
        log(`Answer from ${remotePeers.get(msg.from)?.name ?? msg.from}`);
        await handleAnswer(msg.from, msg.sdp);
        break;

      case 'ice-candidate':
        await handleIceCandidate(msg.from, msg.candidate);
        break;
    }
  }

  function sendSignal(msg: any) {
    if (ws?.readyState === WebSocket.OPEN) ws.send(JSON.stringify(msg));
  }

  // ─── Step 3: WebRTC peer connections ───

  async function createPeerConnection(peerId: string, isInitiator: boolean) {
    if (peerConnections.has(peerId)) return;

    const pc = new RTCPeerConnection({ iceServers: ICE_SERVERS });
    peerConnections.set(peerId, pc);

    // Add local tracks if available
    if (localStream) {
      for (const track of localStream.getTracks()) {
        pc.addTrack(track, localStream);
      }
    } else {
      // No local media — add transceiver so we can still RECEIVE
      pc.addTransceiver('audio', { direction: 'recvonly' });
      pc.addTransceiver('video', { direction: 'recvonly' });
    }

    pc.onicecandidate = (ev) => {
      if (ev.candidate) {
        sendSignal({ type: 'ice-candidate', to: peerId, candidate: ev.candidate.toJSON() });
      }
    };

    pc.ontrack = (ev) => {
      log(`Track: ${ev.track.kind} from ${remotePeers.get(peerId)?.name ?? peerId}`);
      const peer = remotePeers.get(peerId);
      if (peer) {
        peer.stream = ev.streams[0] || new MediaStream([ev.track]);
        peer.state = 'connected';
        remotePeers = new Map(remotePeers);
      }
    };

    pc.oniceconnectionstatechange = () => {
      const state = pc.iceConnectionState;
      const peer = remotePeers.get(peerId);
      if (peer) {
        peer.state = state;
        remotePeers = new Map(remotePeers);
      }
      if (state === 'connected' || state === 'completed') {
        log(`Connected to ${peer?.name ?? peerId}`);
      } else if (state === 'failed') {
        log(`Connection failed to ${peer?.name ?? peerId}`);
      }
    };

    pc.onnegotiationneeded = async () => {
      // Handle renegotiation (e.g., tracks added later)
      if (isInitiator || pc.signalingState === 'stable') {
        try {
          const offer = await pc.createOffer();
          await pc.setLocalDescription(offer);
          sendSignal({ type: 'offer', to: peerId, sdp: offer.sdp });
        } catch (e) {
          console.warn('[rtc] renegotiation error:', e);
        }
      }
    };

    if (isInitiator) {
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);
      sendSignal({ type: 'offer', to: peerId, sdp: offer.sdp });
    }
  }

  async function handleOffer(from: string, sdp: string) {
    if (!peerConnections.has(from)) {
      await createPeerConnection(from, false);
    }
    const pc = peerConnections.get(from)!;
    await pc.setRemoteDescription({ type: 'offer', sdp });
    const answer = await pc.createAnswer();
    await pc.setLocalDescription(answer);
    sendSignal({ type: 'answer', to: from, sdp: answer.sdp });
  }

  async function handleAnswer(from: string, sdp: string) {
    const pc = peerConnections.get(from);
    if (pc && pc.signalingState === 'have-local-offer') {
      await pc.setRemoteDescription({ type: 'answer', sdp });
    }
  }

  async function handleIceCandidate(from: string, candidate: any) {
    const pc = peerConnections.get(from);
    if (pc && candidate) {
      try {
        await pc.addIceCandidate(candidate);
      } catch (e) {
        // Ignore ICE errors for candidates arriving before remote desc
      }
    }
  }

  function closePeerConnection(peerId: string) {
    const pc = peerConnections.get(peerId);
    if (pc) { pc.close(); peerConnections.delete(peerId); }
  }

  // ─── Room actions ───

  function leaveRoom() {
    ws?.close();
    ws = null;
    for (const [id] of peerConnections) closePeerConnection(id);
    remotePeers = new Map();
    if (localStream) {
      localStream.getTracks().forEach(t => t.stop());
      localStream = null;
    }
    if (isRecording) stopRecording();
    status = 'idle';
    mediaError = '';
    recordingStatus = '';
    transcript = null;
    convoId = '';
  }

  async function retryMedia() {
    mediaError = '';
    try {
      localStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: true });
    } catch {
      try {
        localStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
      } catch {
        try {
          localStream = await navigator.mediaDevices.getUserMedia({ audio: false, video: true });
        } catch (e: any) {
          mediaError = 'No camera/mic available.';
          log(`Media: ${mediaError}`);
          return;
        }
      }
    }
    // $effect will bind to video element
    const kinds = localStream!.getTracks().map(t => t.kind).join('+');
    log(`Media ready: ${kinds}`);
    // Add tracks to existing peer connections
    for (const [peerId, pc] of peerConnections) {
      for (const track of localStream!.getTracks()) {
        pc.addTrack(track, localStream!);
      }
      log(`Added ${kinds} to ${peerId}`);
    }
  }

  function toggleMute() {
    if (!localStream) return;
    const t = localStream.getAudioTracks()[0];
    if (t) { t.enabled = !t.enabled; audioMuted = !t.enabled; }
  }

  function toggleVideo() {
    if (!localStream) return;
    const t = localStream.getVideoTracks()[0];
    if (t) { t.enabled = !t.enabled; videoOff = !t.enabled; }
  }

  // ─── Recording ───

  function toggleRecording() {
    if (isRecording) stopRecording();
    else startRecording();
  }

  function startRecording() {
    // Collect all audio: local + remote streams
    const ctx = new AudioContext();
    const dest = ctx.createMediaStreamDestination();

    // Add local audio
    if (localStream) {
      const localAudio = localStream.getAudioTracks()[0];
      if (localAudio) {
        ctx.createMediaStreamSource(new MediaStream([localAudio])).connect(dest);
      }
    }

    // Add remote audio
    for (const [, peer] of remotePeers) {
      if (peer.stream) {
        const remoteAudio = peer.stream.getAudioTracks()[0];
        if (remoteAudio) {
          ctx.createMediaStreamSource(new MediaStream([remoteAudio])).connect(dest);
        }
      }
    }

    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus' : 'audio/webm';

    recordingChunks = [];
    mediaRecorder = new MediaRecorder(dest.stream, { mimeType });
    mediaRecorder.ondataavailable = (ev) => {
      if (ev.data.size > 0) recordingChunks.push(ev.data);
    };
    mediaRecorder.onstop = () => processRecording();
    mediaRecorder.start(1000); // chunk every 1s

    isRecording = true;
    recordingDuration = 0;
    recordingStatus = 'recording';
    recordingTimer = window.setInterval(() => { recordingDuration += 1; }, 1000);
    log('Recording started');
  }

  function stopRecording() {
    if (mediaRecorder?.state === 'recording') {
      mediaRecorder.stop();
    }
    if (recordingTimer) {
      clearInterval(recordingTimer);
      recordingTimer = null;
    }
    isRecording = false;
    log(`Recording stopped (${recordingDuration}s)`);
  }

  async function processRecording() {
    const blob = new Blob(recordingChunks, { type: 'audio/webm;codecs=opus' });
    const recordingId = crypto.randomUUID();

    // 1. Upload to R2 via briefing-signal
    recordingStatus = 'uploading';
    log('Uploading recording...');
    const form = new FormData();
    form.append('file', blob, `${recordingId}.webm`);
    form.append('roomId', roomId);
    form.append('recordingId', recordingId);

    let r2Key = '';
    try {
      const uploadResp = await fetch(`${SIGNAL_HTTP}/upload`, { method: 'POST', body: form });
      const uploadResult = await uploadResp.json() as any;
      if (!uploadResult.ok) { log(`Upload error: ${uploadResult.error}`); recordingStatus = ''; return; }
      r2Key = uploadResult.r2Key;
      log(`Uploaded: ${(uploadResult.size / 1024).toFixed(0)} KB`);
    } catch (e: any) {
      log(`Upload failed: ${e.message}`); recordingStatus = ''; return;
    }

    // 2. Store recording metadata via XRPC
    try {
      await fetch(`/xrpc/com.etzhayyim.apps.briefing.uploadRecording`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ roomId, recordingId, r2Key, durationMs: recordingDuration * 1000, mimeType: 'audio/webm', convoId }),
      });
    } catch { /* fire-and-forget */ }

    // 3. Transcribe via briefing-signal Workers AI
    recordingStatus = 'transcribing';
    log('Transcribing...');
    try {
      const txResp = await fetch(`${SIGNAL_HTTP}/transcribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ r2Key }),
      });
      const txResult = await txResp.json() as any;
      if (!txResult.ok) { log(`Transcription error: ${txResult.error}`); recordingStatus = ''; return; }
      log(`Transcribed (${txResult.detectedLanguage}): ${txResult.text.substring(0, 80)}...`);

      // 4. Save transcript + auto-translate via XRPC
      recordingStatus = 'translating';
      log('Translating...');
      const saveResp = await fetch(`/xrpc/com.etzhayyim.apps.briefing.saveTranscript`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          roomId, recordingId,
          text: txResult.text,
          segments: txResult.segments,
          detectedLanguage: txResult.detectedLanguage,
          convoId,
        }),
      });
      const saveResult = await saveResp.json() as any;
      if (saveResult.ok) {
        transcript = {
          text: saveResult.originalText,
          translatedText: saveResult.translatedText || '',
          language: saveResult.detectedLanguage,
        };
        log('Transcript + translation saved');
      }
    } catch (e: any) {
      log(`Transcription failed: ${e.message}`);
    }

    recordingStatus = 'done';
  }

  // ─── Convo Project ───

  async function createProject() {
    if (convoId) return;
    try {
      // Create room record
      await fetch(`/xrpc/com.etzhayyim.apps.briefing.createRoom`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          roomId,
          name: `Briefing: ${roomId}`,
          actors: PROJECT_ACTORS.map(a => a.did),
        }),
      });

      convoId = roomId;
      projectActors = [...PROJECT_ACTORS];
      log(`Project: ${roomId} (${PROJECT_ACTORS.length} actors)`);
      for (const a of PROJECT_ACTORS) {
        log(`  Actor: ${a.role} → ${a.did}`);
      }
    } catch (e: any) {
      log(`Project: ${e.message}`);
    }
  }

  /** Svelte action: bind video element to MediaStream */
  function bindStream(el: HTMLVideoElement, stream: MediaStream | null) {
    if (stream) el.srcObject = stream;
    return {
      update(s: MediaStream | null) { if (s) el.srcObject = s; },
    };
  }
</script>

<div class="app">
  <header>
    <h1>Briefing</h1>
    <span class="badge">KAMI WebRTC</span>
  </header>

  {#if status === 'idle' || status === 'media' || status === 'joining'}
    <section class="panel">
      <h2>Join Room</h2>
      <div class="form-grid">
        <label>
          <span>Room ID</span>
          <input bind:value={roomId} placeholder="room name..." />
        </label>
        <label>
          <span>Display Name</span>
          <input bind:value={displayName} placeholder="Your name" />
        </label>
      </div>
      {#if mediaError}
        <p class="media-warn">{mediaError} — joining without camera</p>
      {/if}
      <button class="btn primary" onclick={requestMedia} disabled={status !== 'idle'}>
        {status === 'idle' ? 'Join Room' : 'Connecting...'}
      </button>
    </section>
  {/if}

  {#if status === 'joined'}
    <section class="panel">
      <div class="room-header">
        <h2>Room: {roomId}</h2>
        <span class="peer-count">{remotePeers.size} peer{remotePeers.size !== 1 ? 's' : ''}</span>
        {#if convoId}
          <span class="badge project-badge">Project</span>
        {/if}
        <button class="btn danger" onclick={leaveRoom}>Leave</button>
      </div>

      <div class="video-grid">
        <div class="video-cell">
          <div class="video-container">
            <video bind:this={localVideoEl} autoplay muted playsinline></video>
            {#if !localStream || videoOff}
              <div class="video-placeholder">You</div>
            {/if}
          </div>
          <div class="video-label">{displayName || myPeerId} (You)</div>
        </div>

        {#each [...remotePeers] as [peerId, peer]}
          <div class="video-cell">
            <div class="video-container">
              {#if peer.stream}
                <video autoplay playsinline use:bindStream={peer.stream}></video>
              {/if}
              {#if !peer.stream}
                <div class="video-placeholder">
                  {peer.state === 'connected' || peer.state === 'completed' ? peer.name : `${peer.name} (${peer.state})`}
                </div>
              {/if}
            </div>
            <div class="video-label">
              {peer.name}
              {#if peer.state === 'connected' || peer.state === 'completed'}
                <span class="connected-dot"></span>
              {/if}
            </div>
          </div>
        {/each}
      </div>

      {#if mediaError}
        <p class="media-warn">{mediaError}</p>
      {/if}

      <div class="media-controls">
        {#if localStream}
          <button class="btn" class:active={!audioMuted} onclick={toggleMute}>
            {audioMuted ? 'Unmute' : 'Mute'}
          </button>
          <button class="btn" class:active={!videoOff} onclick={toggleVideo}>
            {videoOff ? 'Camera On' : 'Camera Off'}
          </button>
        {:else}
          <button class="btn primary" onclick={retryMedia}>Allow Camera & Mic</button>
        {/if}
        <button
          class="btn"
          class:recording={isRecording}
          onclick={toggleRecording}
          disabled={recordingStatus === 'uploading' || recordingStatus === 'transcribing' || recordingStatus === 'translating'}
        >
          {#if isRecording}
            Stop ({Math.floor(recordingDuration / 60)}:{(recordingDuration % 60).toString().padStart(2, '0')})
          {:else if recordingStatus && recordingStatus !== 'done' && recordingStatus !== 'recording'}
            {recordingStatus}...
          {:else}
            Record
          {/if}
        </button>
      </div>
    </section>

    {#if projectActors.length > 0}
      <section class="panel actors-panel">
        <h3>Project Actors ({projectActors.length} DIDs)</h3>
        <div class="actor-list">
          {#each projectActors as actor}
            <div class="actor-item">
              <span class="actor-role">{actor.role}</span>
              <span class="actor-did">{actor.did.split(':').pop()}</span>
            </div>
          {/each}
        </div>
      </section>
    {/if}

    {#if transcript}
      <section class="panel">
        <h3>Transcript ({transcript.language})</h3>
        <div class="transcript-text">{transcript.text}</div>
        {#if transcript.translatedText}
          <h3>Translation</h3>
          <div class="transcript-text translated">{transcript.translatedText}</div>
        {/if}
      </section>
    {/if}
  {/if}

  <section class="panel log-panel">
    <h3>Event Log</h3>
    <div class="log">
      {#each eventLog as entry}
        <div class="log-entry">{entry}</div>
      {/each}
      {#if eventLog.length === 0}
        <div class="log-entry dim">No events yet</div>
      {/if}
    </div>
  </section>
</div>

<style>
  :global(body) {
    margin: 0;
    font-family: 'Nunito', system-ui, -apple-system, sans-serif;
    background: #f0ead6; color: #1a1a2e;
  }
  .app {
    max-width: 700px; margin: 0 auto; padding: 1rem;
    min-height: 100vh; display: flex; flex-direction: column; gap: 1rem;
  }
  header { display: flex; align-items: center; gap: 0.75rem; }
  header h1 { margin: 0; font-size: 1.5rem; font-weight: 800; }
  .badge {
    background: #e74c6f; color: white;
    padding: 0.2rem 0.6rem; border-radius: 999px;
    font-size: 0.7rem; font-weight: 700;
  }
  .panel {
    background: white; border-radius: 16px; padding: 1.25rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  }
  .panel h2 { margin: 0 0 1rem; font-size: 1.1rem; font-weight: 700; }
  .panel h3 { margin: 0.5rem 0; font-size: 0.9rem; font-weight: 700; }
  .form-grid { display: flex; flex-direction: column; gap: 0.75rem; margin-bottom: 1rem; }
  .form-grid label { display: flex; flex-direction: column; gap: 0.25rem; font-size: 0.8rem; font-weight: 600; }
  .form-grid input {
    padding: 0.5rem 0.75rem; border: 2px solid #e2dcc8; border-radius: 10px;
    font-size: 0.9rem; background: #faf8f0;
  }
  .form-grid input:focus { outline: none; border-color: #e74c6f; }
  .media-warn { color: #d97706; font-size: 0.8rem; font-weight: 600; margin: 0 0 0.5rem; }
  .btn {
    padding: 0.5rem 1rem; border: none; border-radius: 10px;
    font-size: 0.85rem; font-weight: 700; cursor: pointer;
    background: #e2dcc8; color: #1a1a2e;
  }
  .btn:hover { transform: translateY(-1px); }
  .btn.primary { background: #e74c6f; color: white; }
  .btn.danger { background: #dc2626; color: white; }
  .btn.active { background: #16a34a; color: white; }
  .btn:disabled { opacity: 0.5; cursor: not-allowed; }
  .room-header { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem; }
  .room-header h2 { margin: 0; flex: 1; }
  .peer-count {
    background: #16a34a; color: white;
    padding: 0.2rem 0.6rem; border-radius: 999px;
    font-size: 0.75rem; font-weight: 700;
  }
  .video-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 0.75rem; margin-bottom: 1rem;
  }
  .video-cell { text-align: center; }
  .video-container {
    position: relative; width: 100%; aspect-ratio: 4/3;
    background: #1a1a2e; border-radius: 12px; overflow: hidden;
  }
  .video-container video { width: 100%; height: 100%; object-fit: cover; }
  .video-placeholder {
    position: absolute; inset: 0; display: grid; place-content: center;
    color: #6b7280; font-weight: 600; font-size: 0.85rem;
  }
  .video-label { font-size: 0.75rem; font-weight: 600; margin-top: 0.3rem; color: #4b5563; }
  .connected-dot {
    display: inline-block; width: 8px; height: 8px;
    background: #16a34a; border-radius: 50%; margin-left: 0.3rem;
    vertical-align: middle;
  }
  .media-controls { display: flex; gap: 0.5rem; justify-content: center; }
  .log-panel { flex: 1; min-height: 100px; }
  .log {
    max-height: 150px; overflow-y: auto;
    font-family: 'SF Mono', monospace; font-size: 0.7rem; line-height: 1.4;
  }
  .log-entry { padding: 0.1rem 0; border-bottom: 1px solid #f0ead6; }
  .log-entry.dim { color: #9ca3af; }
  .btn.recording { background: #dc2626; color: white; animation: pulse 1s infinite; }
  @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.7; } }
  .project-badge { background: #2563eb; }
  .transcript-text {
    font-size: 0.85rem; line-height: 1.5;
    padding: 0.75rem; background: #faf8f0; border-radius: 8px;
    margin-bottom: 0.5rem; white-space: pre-wrap;
    max-height: 200px; overflow-y: auto;
  }
  .transcript-text.translated { background: #eff6ff; border-left: 3px solid #2563eb; }
  .actor-list { display: flex; flex-direction: column; gap: 0.3rem; }
  .actor-item {
    display: flex; justify-content: space-between; align-items: center;
    padding: 0.4rem 0.6rem; background: #faf8f0; border-radius: 8px;
    font-size: 0.75rem;
  }
  .actor-role { font-weight: 700; color: #1a1a2e; }
  .actor-did { font-family: 'SF Mono', monospace; color: #6b7280; font-size: 0.65rem; }
</style>
