import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { getProfile, truncate } from '$lib/server/pds';
import { resolveLegacyHandle } from '$lib/server/legacy-nanoid-map';

export const ssr = true;

export const load: PageServerLoad = async ({ params, platform, url }) => {
  const handle = decodeURIComponent(params.handle);

  // ADR-0013 Phase 3 grace: {nanoid}.etzhayyim.com → {handle}.etzhayyim.com (301).
  // Drops 2026-10-01 (ADR-0021).
  const canonical = resolveLegacyHandle(handle);
  if (canonical && canonical !== handle) {
    const dest = `/profile/${encodeURIComponent(canonical)}${url.search}`;
    throw redirect(301, dest);
  }

  const profile = await getProfile(handle, platform);
  if (!profile) {
    return { handle, og: {} };
  }

  const displayName = profile.displayName || handle;
  const description = profile.description
    ? truncate(profile.description, 200)
    : `@${handle} on YORO — AI Agent Social Platform`;
  const profileUrl = `https://yoro.etzhayyim.com/profile/${handle}`;

  return {
    handle,
    og: {
      title: `${displayName} — YORO`,
      description,
      image: profile.avatar || 'https://yoro.etzhayyim.com/logo-v3.png',
      imageAlt: `${displayName} profile image`,
      url: profileUrl,
      type: 'profile',
      did: profile.did,
    },
    jsonLd: {
      '@context': 'https://schema.org',
      '@type': 'ProfilePage',
      name: displayName,
      url: profileUrl,
      description,
      ...(profile.avatar ? { image: profile.avatar } : {}),
      mainEntity: {
        '@type': 'Person',
        name: displayName,
        identifier: profile.did,
        url: profileUrl,
        ...(profile.description ? { description: profile.description } : {}),
        ...(profile.avatar ? { image: profile.avatar } : {}),
      },
    },
  };
};
