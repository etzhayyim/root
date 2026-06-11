/**
 * SSR loader for /profile/{handle}/post/{rkey}.
 * Generates OG tags + JSON-LD for crawlers via Workers RPC (PDS_SERVICE).
 */
import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { getProfile, getPostThread, makePostUri, postImageUrl, truncate } from '$lib/server/pds';
import { resolveLegacyHandle } from '$lib/server/legacy-nanoid-map';

export const ssr = true;

export const load: PageServerLoad = async ({ params, platform, url }) => {
	const handle = decodeURIComponent(params.handle);
	const rkey = decodeURIComponent(params.rkey);

	// ADR-0013 Phase 3 grace: {nanoid}.etzhayyim.com → {handle}.etzhayyim.com (drops 2026-10-01).
	const canonical = resolveLegacyHandle(handle);
	if (canonical && canonical !== handle) {
		throw redirect(301, `/profile/${encodeURIComponent(canonical)}/post/${encodeURIComponent(rkey)}${url.search}`);
	}

	const profile = await getProfile(handle, platform);
	if (!profile) {
		return { handle, rkey, og: {}, jsonLd: undefined };
	}

	const uri = makePostUri(profile.did, rkey);
	const thread = await getPostThread(uri, platform);
	const post = thread?.thread?.post ?? null;

	if (!post) {
		return {
			handle, rkey,
			og: {
				title: `Post by ${profile.displayName || handle}`,
				description: `@${handle} on YORO`,
				url: `https://yoro.etzhayyim.com/profile/${handle}/post/${rkey}`,
				authorName: profile.displayName || handle,
				authorDid: profile.did,
			},
			jsonLd: undefined,
		};
	}

	const text = post.record.text || '';
	const image = postImageUrl(post) || profile.avatar || null;
	const canonicalUrl = `https://yoro.etzhayyim.com/profile/${handle}/post/${rkey}`;
	const authorName = profile.displayName || handle;
	const title = truncate(text, 70) || `Post by ${authorName}`;
	const description = truncate(text) || `@${handle} on YORO`;

	return {
		handle, rkey,
		og: {
			title,
			description,
			image,
			url: canonicalUrl,
			type: 'article',
			authorName,
			authorDid: profile.did,
			authorAvatar: profile.avatar || null,
			postText: text,
			createdAt: post.record.createdAt,
			replyCount: post.replyCount,
			likeCount: post.likeCount,
			repostCount: post.repostCount,
		},
		jsonLd: {
			'@context': 'https://schema.org',
			'@type': 'SocialMediaPosting',
			headline: title,
			articleBody: text,
			url: canonicalUrl,
			datePublished: post.record.createdAt,
			...(image ? { image } : {}),
			author: {
				'@type': 'Person',
				name: authorName,
				url: `https://yoro.etzhayyim.com/profile/${handle}`,
				...(profile.avatar ? { image: profile.avatar } : {}),
			},
			publisher: {
				'@type': 'Organization',
				name: 'YORO',
				url: 'https://yoro.etzhayyim.com',
				logo: { '@type': 'ImageObject', url: 'https://yoro.etzhayyim.com/logo-v3.png' },
			},
			interactionStatistic: [
				{ '@type': 'InteractionCounter', interactionType: 'https://schema.org/LikeAction', userInteractionCount: post.likeCount || 0 },
				{ '@type': 'InteractionCounter', interactionType: 'https://schema.org/ShareAction', userInteractionCount: post.repostCount || 0 },
				{ '@type': 'InteractionCounter', interactionType: 'https://schema.org/CommentAction', userInteractionCount: post.replyCount || 0 },
			],
		},
	};
};
