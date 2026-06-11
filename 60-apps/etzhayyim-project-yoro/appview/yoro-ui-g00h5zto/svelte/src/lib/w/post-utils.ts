type AnyPost = {
	uri?: string;
	embed?: Record<string, unknown> | null;
	record?: { embed?: Record<string, unknown> | null } | null;
	author?: { did?: string; handle?: string } | null;
};

type BlobRef = {
	$link?: string;
};

type RecordImage = {
	alt?: string;
	image?: {
		ref?: BlobRef;
	};
};

function blobUrl(cid: string): string {
	return `https://cdn.etzhayyim.com/blobs/anonymous/${encodeURIComponent(cid)}`;
}

export function postRkey(postOrUri: AnyPost | string | null | undefined): string {
	const uri = typeof postOrUri === 'string' ? postOrUri : postOrUri?.uri;
	if (!uri) return '';
	const match = uri.match(/\/app\.bsky\.feed\.post\/([^/?#]+)$/);
	return match?.[1] ?? '';
}

export function postRouteActor(author: AnyPost['author'], fallback = ''): string {
	const handle = author?.handle?.trim();
	if (handle && handle !== 'handle.invalid') return handle;
	const did = author?.did?.trim();
	if (did?.startsWith('did:web:')) return did.slice('did:web:'.length);
	return did || fallback;
}

export function didFromRouteActor(actor: string): string {
	const normalized = actor.trim();
	if (normalized.startsWith('did:')) return normalized;
	if (normalized.includes(':')) return `did:web:${normalized}`;
	if (/^[a-z0-9.-]+\.[a-z]{2,}$/i.test(normalized)) return `did:web:${normalized.toLowerCase()}`;
	return '';
}

export function normalizedPostEmbed(post: AnyPost | null | undefined): Record<string, unknown> | null {
	if (post?.embed && typeof post.embed === 'object') return post.embed;
	const recordEmbed = post?.record?.embed;
	if (!recordEmbed || typeof recordEmbed !== 'object') return null;

	const type = String(recordEmbed.$type ?? recordEmbed.type ?? '');
	if (type === 'app.bsky.embed.images' || type === 'images') {
		const images = Array.isArray(recordEmbed.images) ? recordEmbed.images as RecordImage[] : [];
		const normalizedImages = images
			.map((img) => {
				const cid = img.image?.ref?.$link;
				if (!cid) return null;
				const url = blobUrl(cid);
				return { thumb: url, fullsize: url, alt: img.alt ?? '' };
			})
			.filter((img): img is { thumb: string; fullsize: string; alt: string } => !!img);
		return normalizedImages.length ? { type: 'images', images: normalizedImages } : null;
	}

	return null;
}
