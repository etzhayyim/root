<script lang="ts">
	/** Map pin card — renders a static map image with pin overlay.
	 *  Uses OpenStreetMap static tile (no JS map library needed). */

	interface MapPinPayload {
		center: { lat: number; lng: number };
		pins: Array<{ lat: number; lng: number; label: string; icon?: string }>;
		zoom?: number;
	}

	interface Props {
		payload: MapPinPayload;
		onAction?: (action: string) => void;
	}

	let { payload, onAction }: Props = $props();
	const zoom = $derived(payload.zoom ?? 14);

	// Static tile URL (OpenStreetMap)
	function tileUrl(lat: number, lng: number, z: number): string {
		const x = Math.floor(((lng + 180) / 360) * Math.pow(2, z));
		const latRad = (lat * Math.PI) / 180;
		const y = Math.floor((1 - Math.log(Math.tan(latRad) + 1 / Math.cos(latRad)) / Math.PI) / 2 * Math.pow(2, z));
		return `https://tile.openstreetmap.org/${z}/${x}/${y}.png`;
	}
</script>

<div class="rounded-2xl bg-gv2-bg-card border border-gv2-border/20 overflow-hidden">
	<!-- Static map preview -->
	<div class="relative h-[180px] bg-gv2-bg-hover">
		<img
			src={tileUrl(payload.center.lat, payload.center.lng, zoom)}
			alt="Map"
			class="h-full w-full object-cover opacity-80"
			loading="lazy"
		/>
		<!-- Center pin -->
		<div class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-full text-[24px]">📍</div>
	</div>
	<!-- Pin list -->
	{#if payload.pins.length > 0}
		<div class="divide-y divide-gv2-border/10">
			{#each payload.pins as pin, i (i)}
				<button
					type="button"
					class="flex w-full items-center gap-2 px-3 py-2.5 text-left touch-manipulation active:bg-gv2-bg-hover/50"
					onclick={() => onAction?.(`pin:${i}`)}
				>
					<span class="text-[16px] shrink-0">{pin.icon ?? '📍'}</span>
					<span class="text-[14px] text-gv2-text-primary truncate">{pin.label}</span>
					<span class="ml-auto text-[11px] text-gv2-text-muted shrink-0">{pin.lat.toFixed(4)}, {pin.lng.toFixed(4)}</span>
				</button>
			{/each}
		</div>
	{/if}
</div>
