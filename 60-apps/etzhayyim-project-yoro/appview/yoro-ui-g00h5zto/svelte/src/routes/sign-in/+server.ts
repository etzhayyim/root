import { redirect } from '@sveltejs/kit';

import type { RequestHandler } from './$types';

// ADR-2606061500: sign-in is a same-origin passkey → CACAO ceremony in the
// client (no authn.etzhayyim.com hop, no server-minted session). This legacy
// endpoint now redirects to the same-origin onboarding gate, which runs the
// CACAO ceremony; the return target is preserved for post-sign-in navigation.
export const GET: RequestHandler = ({ url }) => {
  const returnTo = url.searchParams.get('redirect_url') || url.searchParams.get('return_to');
  const dest = new URL('/welcome', url.origin);
  if (returnTo) dest.searchParams.set('return_to', returnTo);
  throw redirect(302, dest.pathname + dest.search);
};
