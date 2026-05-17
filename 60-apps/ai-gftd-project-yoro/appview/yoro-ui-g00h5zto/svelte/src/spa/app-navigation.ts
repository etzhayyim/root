import { navigate } from "./router";

export function goto(url: string | URL, opts?: { replaceState?: boolean; noScroll?: boolean }): Promise<void> {
  return navigate(url, opts);
}

export function invalidate(_resource?: string | URL | ((url: URL) => boolean)): Promise<void> {
  return Promise.resolve();
}

export function invalidateAll(): Promise<void> {
  return Promise.resolve();
}

export function preloadCode(_pathname: string): Promise<void> {
  return Promise.resolve();
}

export function preloadData(_url: string): Promise<{ type: "loaded"; status: number; data: Record<string, never> }> {
  return Promise.resolve({ type: "loaded", status: 200, data: {} });
}

export function replaceState(url: string | URL, state: Record<string, unknown>): void {
  const next = typeof url === "string" ? new URL(url, window.location.origin) : url;
  history.replaceState(state, "", `${next.pathname}${next.search}${next.hash}`);
}

export function pushState(url: string | URL, state: Record<string, unknown>): void {
  const next = typeof url === "string" ? new URL(url, window.location.origin) : url;
  history.pushState(state, "", `${next.pathname}${next.search}${next.hash}`);
}

export function beforeNavigate(_callback: (navigation: unknown) => void): () => void {
  return () => {};
}

export function afterNavigate(_callback: (navigation: unknown) => void): () => void {
  return () => {};
}

export function onNavigate(_callback: (navigation: unknown) => void): () => void {
  return () => {};
}

export function disableScrollHandling(): void {}

