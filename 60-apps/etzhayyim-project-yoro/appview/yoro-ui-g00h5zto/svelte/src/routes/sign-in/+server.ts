import { redirect } from '@sveltejs/kit';

import type { RequestHandler } from './$types';

/**
 * Legacy `/sign-in` entry. Same-origin passkey auth (ADR-2606061800) has no
 * separate hosted sign-in page — auth happens in-app via the header / profile
 * buttons (WebAuthn → did:key, no authn.etzhayyim.com / mcp.etzhayyim.com). So
 * this route just bounces into the SPA (preserving any same-origin return
 * target) where the in-app sign-in lives, instead of redirecting to the retired
 * auth host.
 */
export const GET: RequestHandler = ({ url }) => {
  const returnTo = url.searchParams.get('redirect_url') || url.searchParams.get('return_to');
  let target = '/';
  if (returnTo) {
    try {
      // Only honor same-origin return targets (anti-open-redirect).
      const u = new URL(returnTo, url.origin);
      if (u.origin === url.origin) target = u.pathname + u.search;
    } catch {
      /* malformed return_to → default to '/' */
    }
  }
  throw redirect(302, target);
};
