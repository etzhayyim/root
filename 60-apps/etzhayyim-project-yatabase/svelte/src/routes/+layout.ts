// Static + CSR — the entire Studio renders on the client against the
// edge Worker, no SSR roundtrip. adapter-static + fallback=index.html.
export const prerender = true;
export const ssr = false;
