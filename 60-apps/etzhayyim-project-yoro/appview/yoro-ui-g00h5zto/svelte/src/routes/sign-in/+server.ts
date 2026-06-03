import { redirect } from '@sveltejs/kit';

import type { RequestHandler } from './$types';

export const GET: RequestHandler = ({ url }) => {
  const redirectUrl = new URL('/sign-in', 'https://authn.etzhayyim.com');
  const returnTo = url.searchParams.get('redirect_url') || url.searchParams.get('return_to');
  if (returnTo) {
    redirectUrl.searchParams.set('redirect_url', returnTo);
  }
  throw redirect(302, redirectUrl.toString());
};
