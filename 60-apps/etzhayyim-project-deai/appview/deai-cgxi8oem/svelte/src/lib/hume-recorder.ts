/**
 * HumeRecorder — MediaRecorder + real-time Hume face/prosody via CF Worker WS proxy
 *
 * Stage A: MediaRecorder (WebM on web/Android, MP4 on iOS WKWebView)
 * Stage B: Per-word timestamp markers for reaction-time linkage
 * Stage C: Hume WS via CF Worker proxy (graceful if unavailable)
 * Stage D: Capacitor Filesystem save (graceful if not in native shell)
 */

export interface WordMark {
  wordId: number;
  word: string;
  startMs: number;
  endMs: number;
}

export type HumeScores = Record<string, number>;

export interface SessionResult {
  blob: Blob;
  mimeType: string;
  wordMarks: WordMark[];
  durationMs: number;
  filePath?: string; // set if Capacitor saved successfully
}

const HUME_EMOTIONS = [
  "joy", "sadness", "anger", "fear", "disgust",
  "calm", "focus", "surprise", "confusion", "awe",
] as const;

function pickMimeType(): string {
  const candidates = [
    "video/webm;codecs=vp9,opus",
    "video/webm;codecs=vp8,opus",
    "video/webm",
    "video/mp4",
  ];
  for (const c of candidates) {
    if (MediaRecorder.isTypeSupported(c)) return c;
  }
  return "";
}

export class HumeRecorder {
  private stream: MediaStream | null = null;
  private recorder: MediaRecorder | null = null;
  private chunks: Blob[] = [];

  private sessionStart = 0;
  private wordMarks: WordMark[] = [];
  private currentWordId = -1;
  private currentWordStart = 0;
  private currentWordLabel = "";

  // Emotion accumulation per wordId
  private wordEmotions = new Map<number, HumeScores[]>();

  // Hume WS
  private ws: WebSocket | null = null;
  private wsReady = false;
  private captureCanvas: HTMLCanvasElement;
  private captureCtx: CanvasRenderingContext2D;
  private captureInterval: ReturnType<typeof setInterval> | null = null;

  readonly mimeType: string;
  private videoEl: HTMLVideoElement | null = null;

  constructor(
    private readonly proxyWsUrl?: string,
    private readonly captureHz = 2, // face frames per second
  ) {
    this.mimeType = pickMimeType();
    this.captureCanvas = document.createElement("canvas");
    this.captureCanvas.width = 320;
    this.captureCanvas.height = 240;
    this.captureCtx = this.captureCanvas.getContext("2d")!;
  }

  /** Returns the live MediaStream so the CameraPreview can render it. */
  get liveStream(): MediaStream | null {
    return this.stream;
  }

  /** Attach a live <video> element for frame capture. */
  attachVideo(el: HTMLVideoElement) {
    this.videoEl = el;
  }

  // ── Session lifecycle ───────────────────────────────────────

  async startSession(): Promise<boolean> {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: { ideal: 640 }, height: { ideal: 480 } },
        audio: { echoCancellation: true, noiseSuppression: true },
      });
    } catch (e) {
      console.warn("[HumeRecorder] getUserMedia failed:", e);
      return false;
    }

    this.chunks = [];
    this.wordMarks = [];
    this.wordEmotions = new Map();
    this.sessionStart = Date.now();
    this.currentWordId = -1;

    // MediaRecorder
    const opts: MediaRecorderOptions = {};
    if (this.mimeType) opts.mimeType = this.mimeType;
    try {
      this.recorder = new MediaRecorder(this.stream, opts);
    } catch {
      this.recorder = new MediaRecorder(this.stream); // iOS fallback (no opts)
    }
    this.recorder.ondataavailable = (e) => {
      if (e.data.size > 0) this.chunks.push(e.data);
    };
    this.recorder.start(1000); // 1-second chunks

    // Hume WS (optional)
    if (this.proxyWsUrl) this.connectHume();

    return true;
  }

  /** Mark the start of a new word display. Call when the word appears on screen. */
  markWord(wordId: number, word: string) {
    const now = Date.now();

    // Seal previous word
    if (this.currentWordId >= 0) {
      this.wordMarks.push({
        wordId: this.currentWordId,
        word: this.currentWordLabel,
        startMs: this.currentWordStart - this.sessionStart,
        endMs: now - this.sessionStart,
      });
    }

    this.currentWordId = wordId;
    this.currentWordLabel = word;
    this.currentWordStart = now;
    if (!this.wordEmotions.has(wordId)) {
      this.wordEmotions.set(wordId, []);
    }
  }

  /** Get averaged Hume scores for a word. Falls back to mock if no real data. */
  getWordScores(wordId: number): HumeScores {
    const snaps = this.wordEmotions.get(wordId) ?? [];
    if (snaps.length === 0) return mockScores();
    const avg: HumeScores = {};
    for (const k of HUME_EMOTIONS) {
      avg[k] = Math.round(snaps.reduce((s, e) => s + (e[k] ?? 0), 0) / snaps.length);
    }
    return avg;
  }

  async stopSession(): Promise<SessionResult | null> {
    if (!this.stream) return null;

    // Seal last word
    if (this.currentWordId >= 0) {
      this.wordMarks.push({
        wordId: this.currentWordId,
        word: this.currentWordLabel,
        startMs: this.currentWordStart - this.sessionStart,
        endMs: Date.now() - this.sessionStart,
      });
      this.currentWordId = -1;
    }

    // Stop WS capture
    if (this.captureInterval) {
      clearInterval(this.captureInterval);
      this.captureInterval = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    // Stop recorder
    await new Promise<void>((resolve) => {
      if (!this.recorder || this.recorder.state === "inactive") {
        resolve();
        return;
      }
      this.recorder.onstop = () => resolve();
      this.recorder.stop();
    });

    const durationMs = Date.now() - this.sessionStart;

    // Stop tracks
    this.stream.getTracks().forEach((t) => t.stop());
    this.stream = null;

    const blob = new Blob(this.chunks, {
      type: this.mimeType || "video/webm",
    });

    const filePath = await this.saveToFilesystem(blob);

    return { blob, mimeType: this.mimeType, wordMarks: this.wordMarks, durationMs, filePath };
  }

  // ── Capacitor Filesystem (Stage D) ─────────────────────────

  private async saveToFilesystem(blob: Blob): Promise<string | undefined> {
    try {
      // Access Capacitor via the global injected by the native shell (WKWebView / Android WebView).
      // Avoids any static import so Vite never tries to resolve @capacitor/filesystem.
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const cap = (window as any).Capacitor;
      if (!cap?.isNativePlatform?.()) return undefined;

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const { Filesystem } = cap.Plugins as { Filesystem: any };
      const ext = this.mimeType.includes("mp4") ? "mp4" : "webm";
      const fileName = `spirit-session-${Date.now()}.${ext}`;
      const base64 = await blobToBase64(blob);
      await Filesystem.writeFile({
        path: `SpiritInPhysics/${fileName}`,
        data: base64,
        directory: "DOCUMENTS", // Directory.Documents enum value
        recursive: true,
      });
      return `SpiritInPhysics/${fileName}`;
    } catch {
      return undefined;
    }
  }

  // ── Hume AI WebSocket (Stage C) ────────────────────────────

  private connectHume() {
    if (!this.proxyWsUrl) return;
    try {
      this.ws = new WebSocket(this.proxyWsUrl);
      this.ws.onopen = () => {
        this.wsReady = true;
        this.startFaceCapture();
      };
      this.ws.onmessage = (ev) => this.handleHumeMessage(ev.data);
      this.ws.onerror = () => {
        this.wsReady = false;
      };
      this.ws.onclose = () => {
        this.wsReady = false;
        if (this.captureInterval) {
          clearInterval(this.captureInterval);
          this.captureInterval = null;
        }
      };
    } catch (e) {
      console.warn("[HumeRecorder] Hume WS connect failed:", e);
    }
  }

  private startFaceCapture() {
    const intervalMs = Math.round(1000 / this.captureHz);
    this.captureInterval = setInterval(() => {
      if (!this.wsReady || !this.videoEl || this.ws?.readyState !== WebSocket.OPEN) return;
      this.captureCtx.drawImage(this.videoEl, 0, 0, 320, 240);
      const dataUrl = this.captureCanvas.toDataURL("image/jpeg", 0.7);
      const base64 = dataUrl.split(",")[1];
      this.ws.send(JSON.stringify({
        data: base64,
        models: { face: {}, prosody: {} },
      }));
    }, intervalMs);
  }

  private handleHumeMessage(raw: string) {
    try {
      const msg = JSON.parse(raw);
      // Hume streaming face response shape: msg.face.predictions[].emotions[]
      const faceEmotions = msg?.face?.predictions?.[0]?.emotions as
        Array<{ name: string; score: number }> | undefined;
      if (!faceEmotions?.length) return;

      const scores: HumeScores = {};
      for (const e of faceEmotions) {
        const key = e.name.toLowerCase();
        if ((HUME_EMOTIONS as readonly string[]).includes(key)) {
          scores[key] = Math.round(e.score * 1000);
        }
      }

      if (this.currentWordId >= 0) {
        const arr = this.wordEmotions.get(this.currentWordId)!;
        arr.push(scores);
      }
    } catch {
      // ignore parse errors
    }
  }
}

// ── Helpers ────────────────────────────────────────────────────

function mockScores(): HumeScores {
  const rand = () => Math.round(Math.random() * 800 + 100);
  return {
    joy: rand(), sadness: rand(), anger: rand(), fear: rand(), disgust: rand(),
    calm: rand(), focus: rand(), surprise: rand(), confusion: rand(), awe: rand(),
  };
}

function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const result = reader.result as string;
      resolve(result.split(",")[1]);
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}
