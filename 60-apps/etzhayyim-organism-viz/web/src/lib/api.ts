import type { Snapshot } from "./types";

const API = "";   // same-origin

export async function fetchState(): Promise<Snapshot> {
  const r = await fetch(API + "/api/state");
  if (!r.ok) throw new Error("state http " + r.status);
  return r.json();
}

export async function chatWith(entityId: string, message: string) {
  const r = await fetch(API + "/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ entity_id: entityId, message }),
  });
  return r.json();
}

export function openEvents(onMsg: (ev: any) => void): EventSource {
  const es = new EventSource(API + "/api/events");
  es.onmessage = (m) => {
    try { onMsg(JSON.parse(m.data)); } catch {}
  };
  return es;
}
