import { redirect } from '@sveltejs/kit';

// Root `/` lands on the generated-world gallery (WebGPU canvas), not the
// appview placeholder. worlds.htm is a static asset served by the same
// worker (kami-app-isekai WASM + kami_usd::to_usda world catalog).
export const prerender = false;

export function load() {
  redirect(307, '/worlds.htm');
}
