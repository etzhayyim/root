import { writable } from "svelte/store";

type PageComponent = any;

type RouteEntry = {
  id: string;
  regex: RegExp;
  keys: string[];
  score: number;
  component: PageComponent;
};

type RouteMatch = {
  routeId: string;
  component: PageComponent;
  params: Record<string, string>;
};

type PageState = {
  url: URL;
  params: Record<string, string>;
  route: { id: string | null };
  status: number;
  error: unknown;
  data: Record<string, unknown>;
  form: unknown;
  state: Record<string, unknown>;
};

const pageModules = import.meta.glob("../routes/**/+page.svelte", { eager: true }) as Record<
  string,
  { default?: PageComponent }
>;

function normalizeRoutePath(filePath: string): string {
  const withoutPrefix = filePath.replace("../routes", "");
  const routePath = withoutPrefix.replace(/\/\+page\.svelte$/, "");
  return routePath.length === 0 ? "/" : routePath;
}

function compileRoute(routePath: string): { regex: RegExp; keys: string[]; score: number } {
  if (routePath === "/") return { regex: /^\/$/, keys: [], score: 1_000_000 };

  const parts = routePath.split("/").filter(Boolean);
  const keys: string[] = [];
  let score = 0;
  const patternParts = parts.map((part) => {
    if (part.startsWith("[...") && part.endsWith("]")) {
      const key = part.slice(4, -1);
      keys.push(key);
      score += 1;
      return "(.+)";
    }
    if (part.startsWith("[") && part.endsWith("]")) {
      const key = part.slice(1, -1);
      keys.push(key);
      score += 10;
      return "([^/]+)";
    }
    score += 100;
    return part.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  });

  return { regex: new RegExp(`^/${patternParts.join("/")}$`), keys, score };
}

const routes: RouteEntry[] = Object.entries(pageModules)
  .map(([filePath, mod]) => {
    const component = mod.default;
    if (!component) return null;
    const routePath = normalizeRoutePath(filePath);
    const { regex, keys, score } = compileRoute(routePath);
    return { id: routePath, regex, keys, score, component };
  })
  .filter((route): route is RouteEntry => route !== null)
  .sort((a, b) => b.score - a.score);

const routeById = new Map(routes.map((route) => [route.id, route] as const));

function fallbackProfileParams(pathname: string): Record<string, string> | null {
  if (!pathname.startsWith("/profile/")) return null;
  const handle = pathname.slice("/profile/".length).replace(/\/+$/, "");
  if (!handle || handle.includes("/")) return null;
  return { handle: decodeURIComponent(handle) };
}

function findRoute(pathname: string): RouteMatch | null {
  for (const route of routes) {
    const match = route.regex.exec(pathname);
    if (!match) continue;
    const params: Record<string, string> = {};
    route.keys.forEach((key, idx) => {
      const raw = match[idx + 1] ?? "";
      params[key] = decodeURIComponent(raw);
    });
    return { routeId: route.id, component: route.component, params };
  }
  // Fallback for encoded DID profile paths like /profile/did%3Aweb%3A...
  const fallbackParams = fallbackProfileParams(pathname);
  if (fallbackParams) {
    const profileRoute = routeById.get("/profile/[handle]");
    if (profileRoute) {
      return {
        routeId: profileRoute.id,
        component: profileRoute.component,
        params: fallbackParams,
      };
    }
  }
  return null;
}

function currentUrl(): URL {
  return new URL(window.location.href);
}

const initialUrl = typeof window !== "undefined" ? currentUrl() : new URL("https://example.local/");
const initialMatch = findRoute(initialUrl.pathname);
const initialFallbackParams = fallbackProfileParams(initialUrl.pathname);
const initialParams = initialMatch?.params ?? initialFallbackParams ?? {};
const initialRouteId = initialMatch?.routeId ?? (initialFallbackParams ? "/profile/[handle]" : null);

const initialPage: PageState = {
  url: initialUrl,
  params: initialParams,
  route: { id: initialRouteId },
  status: 200,
  error: null,
  data: {},
  form: null,
  state: {},
};

export const pageStore = writable<PageState>(initialPage);
export const routeState = writable<{ match: RouteMatch | null }>({ match: initialMatch });
export const navigatingStore = writable(null);
export const updatedStore = writable({ current: false, check: async () => false });

function syncFromLocation(): void {
  const url = currentUrl();
  const match = findRoute(url.pathname);
  const fallbackParams = fallbackProfileParams(url.pathname);
  const params = match?.params ?? fallbackParams ?? {};
  const routeId = match?.routeId ?? (fallbackParams ? "/profile/[handle]" : null);
  routeState.set({ match });
  pageStore.set({
    url,
    params,
    route: { id: routeId },
    status: match || fallbackParams ? 200 : 404,
    error: null,
    data: {},
    form: null,
    state: history.state ?? {},
  });
}

export function navigate(to: string | URL, options?: { replaceState?: boolean; noScroll?: boolean }): Promise<void> {
  const url = typeof to === "string" ? new URL(to, window.location.origin) : new URL(to);
  const next = `${url.pathname}${url.search}${url.hash}`;
  if (options?.replaceState) history.replaceState(history.state ?? {}, "", next);
  else history.pushState(history.state ?? {}, "", next);
  syncFromLocation();
  if (!options?.noScroll) window.scrollTo({ top: 0, left: 0 });
  return Promise.resolve();
}

if (typeof window !== "undefined") {
  window.addEventListener("popstate", () => {
    syncFromLocation();
  });
}
