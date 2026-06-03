<script lang="ts">
	import { onMount } from 'svelte';
	import { Detector, classColor } from './lib/detect.svelte.ts';

	const det = new Detector();
	let imgEl = $state<HTMLImageElement | null>(null);
	let overlay = $state<HTMLCanvasElement | null>(null);
	let imageUrl = $state('');
	let imgTick = $state(0); // bumped on image load to retrigger overlay sizing
	let webgpu = $state(true);

	onMount(() => {
		webgpu = Detector.webgpuAvailable();
		det.start();
		return () => det.dispose();
	});

	// Redraw boxes whenever detections or layout change.
	$effect(() => {
		// touch reactive deps
		const dets = det.detections;
		imgTick; // redraw when a new image finishes loading
		if (!overlay || !imgEl || !imgEl.complete || imgEl.naturalWidth === 0) return;
		const dispW = imgEl.clientWidth;
		const dispH = imgEl.clientHeight;
		overlay.width = dispW;
		overlay.height = dispH;
		const sx = dispW / imgEl.naturalWidth;
		const sy = dispH / imgEl.naturalHeight;
		const ctx = overlay.getContext('2d')!;
		ctx.clearRect(0, 0, dispW, dispH);
		ctx.lineWidth = 2;
		ctx.font = '13px ui-sans-serif, system-ui';
		ctx.textBaseline = 'top';
		for (const d of dets) {
			const x = d.x1 * sx;
			const y = d.y1 * sy;
			const w = (d.x2 - d.x1) * sx;
			const h = (d.y2 - d.y1) * sy;
			const color = classColor(d.classId);
			ctx.strokeStyle = color;
			ctx.strokeRect(x, y, w, h);
			const tag = `${d.label} ${(d.score * 100).toFixed(0)}%`;
			const tw = ctx.measureText(tag).width + 8;
			ctx.fillStyle = color;
			ctx.fillRect(x, Math.max(0, y - 18), tw, 18);
			ctx.fillStyle = '#000';
			ctx.fillText(tag, x + 4, Math.max(0, y - 17));
		}
	});

	function onFile(e: Event) {
		const file = (e.target as HTMLInputElement).files?.[0];
		if (!file) return;
		if (imageUrl) URL.revokeObjectURL(imageUrl);
		imageUrl = URL.createObjectURL(file);
		det.detections = [];
	}

	async function runDetect() {
		if (!imgEl) return;
		await det.detect(imgEl);
	}
</script>

<main class="wrap">
	<header>
		<h1>眼 <span class="sub">manako · browser-local YOLO26</span></h1>
		<p class="tagline">On-device object detection — WebGPU/wasm, zero upload, zero server inference.</p>
	</header>

	{#if !webgpu}
		<div class="warn">WebGPU 非対応ブラウザです。wasm フォールバックで動作しますが低速になります（Chrome/Edge 113+ 推奨）。</div>
	{/if}

	<section class="controls">
		<label>
			Model
			<select bind:value={det.modelId} disabled={det.loading}>
				{#each det.models as m}
					<option value={m.id}>{m.label} (~{m.sizeMb}MB)</option>
				{/each}
			</select>
		</label>
		<button onclick={() => det.loadModel()} disabled={det.loading || det.loaded}>
			{det.loaded ? '✓ Loaded' : det.loading ? 'Loading…' : 'Load model'}
		</button>
		<label class="slider">conf {det.confThreshold.toFixed(2)}
			<input type="range" min="0.05" max="0.9" step="0.05" bind:value={det.confThreshold} />
		</label>
		<label class="slider">IoU {det.iouThreshold.toFixed(2)}
			<input type="range" min="0.1" max="0.9" step="0.05" bind:value={det.iouThreshold} />
		</label>
	</section>

	<section class="controls">
		<input type="file" accept="image/*" onchange={onFile} />
		<button onclick={runDetect} disabled={!det.loaded || !imageUrl}>Detect</button>
		<span class="status">{det.statusLabel}{det.provider ? '' : ''}</span>
	</section>

	{#if det.loading}
		<div class="bar"><div class="fill" style="width:{det.progress}%"></div></div>
	{/if}
	{#if det.error}
		<div class="err">⚠ {det.error}</div>
	{/if}

	<section class="stage">
		{#if imageUrl}
			<div class="canvas-wrap">
				<!-- svelte-ignore a11y_missing_attribute -->
				<img bind:this={imgEl} src={imageUrl} onload={() => (imgTick += 1)} />
				<canvas bind:this={overlay}></canvas>
			</div>
		{:else}
			<div class="placeholder">画像を選択してください（画像はブラウザ内で処理され、外部に送信されません）。</div>
		{/if}
	</section>

	{#if det.detections.length}
		<section class="list">
			{#each det.detections as d}
				<span class="chip" style="border-color:{classColor(d.classId)}">{d.label} {(d.score * 100).toFixed(0)}%</span>
			{/each}
		</section>
	{/if}

	<footer>
		Apache-2.0 + etzhayyim Charter Rider. Model weights operator-supplied (Ultralytics YOLO26 = AGPL-3.0; not bundled).
		On-device only · no telemetry · object detection only (no face-ID / no surveillance).
	</footer>
</main>
