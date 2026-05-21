import type { RequestHandler } from './$types';

// Manage UI lives on auth.gftd.ai (static asset); redirect there until
// the full manage page is ported to accounts.gftd.ai.
export const GET: RequestHandler = () =>
  Response.redirect('https://auth.gftd.ai/manage', 302);
