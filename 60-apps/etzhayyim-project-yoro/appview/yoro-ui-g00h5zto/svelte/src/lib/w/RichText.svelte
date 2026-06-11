<script lang="ts">
	interface Facet {
		index: { byteStart: number; byteEnd: number };
		features: Array<
			| { $type: 'app.bsky.richtext.facet#mention'; did: string }
			| { $type: 'app.bsky.richtext.facet#link'; uri: string }
			| { $type: 'app.bsky.richtext.facet#tag'; tag: string }
		>;
	}

	interface Segment {
		text: string;
		type: 'text' | 'mention' | 'link' | 'tag';
		href?: string;
		did?: string;
	}

	interface Props {
		text: string;
		facets?: Facet[];
		class?: string;
	}

	let { text, facets, class: className = '' }: Props = $props();

	// Auto-detect facets from text when none provided
	function autoDetectSegments(input: string): Segment[] {
		const pattern = /(@[\w.-]+\.[\w.-]+)|((https?:\/\/)\S+)|(#[\w\u3000-\u9fff\u4e00-\u9faf\uac00-\ud7af]+)/g;
		const segments: Segment[] = [];
		let lastIndex = 0;
		let match: RegExpExecArray | null;

		while ((match = pattern.exec(input)) !== null) {
			if (match.index > lastIndex) {
				segments.push({ text: input.slice(lastIndex, match.index), type: 'text' });
			}
			if (match[1]) {
				// @mention
				segments.push({ text: match[1], type: 'mention', href: `/profile/${encodeURIComponent(match[1].slice(1))}` });
			} else if (match[2]) {
				// URL
				segments.push({ text: match[2], type: 'link', href: match[2] });
			} else if (match[4]) {
				// #hashtag
				segments.push({ text: match[4], type: 'tag' });
			}
			lastIndex = match.index + match[0].length;
		}
		if (lastIndex < input.length) {
			segments.push({ text: input.slice(lastIndex), type: 'text' });
		}
		return segments.length > 0 ? segments : [{ text: input, type: 'text' }];
	}

	// Parse facets with byte offsets
	function parseFacetSegments(input: string, facetList: Facet[]): Segment[] {
		const encoder = new TextEncoder();
		const bytes = encoder.encode(input);
		// Filter out invalid facets (missing index or byteStart/byteEnd)
		const valid = facetList.filter(f => f?.index && typeof f.index.byteStart === 'number' && typeof f.index.byteEnd === 'number');
		if (valid.length === 0) return autoDetectSegments(input);
		const sorted = [...valid].sort((a, b) => a.index.byteStart - b.index.byteStart);
		const decoder = new TextDecoder();
		const segments: Segment[] = [];
		let bytePos = 0;

		for (const facet of sorted) {
			if (facet.index.byteStart > bytePos) {
				segments.push({ text: decoder.decode(bytes.slice(bytePos, facet.index.byteStart)), type: 'text' });
			}
			const facetText = decoder.decode(bytes.slice(facet.index.byteStart, facet.index.byteEnd));
			const feature = facet.features[0];
			if (!feature) {
				segments.push({ text: facetText, type: 'text' });
			} else if (feature.$type === 'app.bsky.richtext.facet#mention') {
				segments.push({ text: facetText, type: 'mention', did: feature.did, href: `/profile/${encodeURIComponent(feature.did)}` });
			} else if (feature.$type === 'app.bsky.richtext.facet#link') {
				segments.push({ text: facetText, type: 'link', href: feature.uri });
			} else if (feature.$type === 'app.bsky.richtext.facet#tag') {
				segments.push({ text: facetText, type: 'tag' });
			} else {
				segments.push({ text: facetText, type: 'text' });
			}
			bytePos = facet.index.byteEnd;
		}
		if (bytePos < bytes.length) {
			segments.push({ text: decoder.decode(bytes.slice(bytePos)), type: 'text' });
		}
		return segments;
	}

	const segments = $derived(
		facets && facets.length > 0
			? parseFacetSegments(text, facets)
			: autoDetectSegments(text)
	);
</script>

<span class="whitespace-pre-wrap break-words {className}">{#each segments as seg}{#if seg.type === 'mention'}<a href={seg.href} class="text-[#1185FE] no-underline active:underline" onclick={(e) => e.stopPropagation()}>{seg.text}</a>{:else if seg.type === 'link'}<a href={seg.href} class="text-[#1185FE] no-underline active:underline" target="_blank" rel="noopener noreferrer" onclick={(e) => e.stopPropagation()}>{seg.text}</a>{:else if seg.type === 'tag'}<span class="text-[#1185FE]">{seg.text}</span>{:else}{seg.text}{/if}{/each}</span>
