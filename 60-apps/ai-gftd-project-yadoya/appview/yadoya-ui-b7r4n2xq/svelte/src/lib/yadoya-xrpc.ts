// yadoya XRPC client — talks to atproto.etzhayyim.com pipethrough → yadoya Worker.
// AT Protocol semantics: query = GET with URLSearchParams, procedure = POST
// with JSON body. No legacy wproto / nanoid host calls.

const DEFAULT_SERVICE = 'https://atproto.etzhayyim.com';

function service(): string {
  if (typeof window !== 'undefined') {
    const override = (window as any).__YADOYA_SERVICE__;
    if (typeof override === 'string' && override) return override;
    const isLocalhost =
      window.location.hostname === 'localhost' ||
      window.location.hostname === '127.0.0.1';
    if (!isLocalhost && window.location.origin.endsWith('etzhayyim.com')) {
      return window.location.origin;
    }
  }
  return DEFAULT_SERVICE;
}

async function xrpcQuery<T = unknown>(
  nsid: string,
  params: Record<string, string | number | undefined> = {},
): Promise<T> {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === '') continue;
    sp.set(k, String(v));
  }
  const url = `${service()}/xrpc/${nsid}${sp.toString() ? `?${sp}` : ''}`;
  const resp = await fetch(url, { headers: { accept: 'application/json' } });
  if (!resp.ok) {
    const text = await resp.text().catch(() => '');
    throw new Error(`${nsid} ${resp.status}: ${text}`);
  }
  return (await resp.json()) as T;
}

async function xrpcProcedure<T = unknown>(
  nsid: string,
  body: Record<string, unknown>,
  options: { bearer?: string } = {},
): Promise<T> {
  const headers: Record<string, string> = { 'content-type': 'application/json' };
  if (options.bearer) headers.authorization = `Bearer ${options.bearer}`;
  const resp = await fetch(`${service()}/xrpc/${nsid}`, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    const text = await resp.text().catch(() => '');
    throw new Error(`${nsid} ${resp.status}: ${text}`);
  }
  return (await resp.json()) as T;
}

// ── Typed wrappers for com.etzhayyim.apps.yadoya.* ──

export interface YadoyaHotel {
  vertex_id: string;
  hotel_slug: string;
  osm_id: string | null;
  chain_did: string | null;
  property_did: string | null;
  name: string;
  country: string;
  region: string | null;
  city: string | null;
  lat: number | null;
  lon: number | null;
  isic_code: string;
  price_jpy_min: number | null;
  price_jpy_max: number | null;
  capacity_rooms: number | null;
  source_url: string | null;
  status: string;
}

export interface YadoyaReservation {
  vertex_id: string;
  reservation_id: string;
  hotel_vid: string;
  guest_did: string;
  checkin: string;
  checkout: string;
  guests: number;
  nights: number | null;
  currency: string | null;
  channel: string;
  status: string;
  cancelled_at: string | null;
  cancel_reason: string | null;
}

export interface SearchHotelsParams {
  country?: string;
  region?: string;
  city?: string;
  chainDid?: string;
  isicCode?: string;
  checkin?: string;
  checkout?: string;
  guests?: number;
  priceJpyMax?: number;
  limit?: number;
  cursor?: string;
}

export function searchHotels(params: SearchHotelsParams = {}) {
  return xrpcQuery<{ hotels: YadoyaHotel[]; total: number; cursor?: string }>(
    'com.etzhayyim.apps.yadoya.searchHotels',
    params as Record<string, string | number | undefined>,
  );
}

export function listHotels(params: { region?: string; chainDid?: string; limit?: number; offset?: number } = {}) {
  return xrpcQuery<{ hotels: YadoyaHotel[]; total: number; offset: number; limit: number }>(
    'com.etzhayyim.apps.yadoya.listHotels',
    params as Record<string, string | number | undefined>,
  );
}

export interface CreateReservationInput {
  hotelId: string;
  checkin: string;
  checkout: string;
  guests: number;
  guestDid?: string;
  guestSummary?: string;
  amountJpy?: number;
  currency?: string;
  channel?: 'ai-agent' | 'b2c' | 'b2b' | 'corp';
}

export function createReservation(input: CreateReservationInput, bearer?: string) {
  return xrpcProcedure<{ reservationId: string; uri: string; status: 'pending' | 'confirmed' | 'duplicate' }>(
    'com.etzhayyim.apps.yadoya.createReservation',
    input as unknown as Record<string, unknown>,
    { bearer },
  );
}

export function getReservation(reservationId: string) {
  return xrpcQuery<{ reservation: YadoyaReservation }>(
    'com.etzhayyim.apps.yadoya.getReservation',
    { reservationId },
  );
}

export interface ConfirmReservationOutput {
  reservationId: string;
  status: 'confirmed' | 'already-confirmed';
  flowEventId?: string;
  flowVertexId?: string;
}

export function confirmReservation(
  input: { reservationId: string; amountJpy?: number; fiscalPeriod?: string; currency?: string },
  bearer?: string,
) {
  return xrpcProcedure<ConfirmReservationOutput>(
    'com.etzhayyim.apps.yadoya.confirmReservation',
    input as unknown as Record<string, unknown>,
    { bearer },
  );
}

export function cancelReservation(reservationId: string, reason?: string, bearer?: string) {
  return xrpcProcedure<{ reservationId: string; status: 'cancelled' | 'already-cancelled' }>(
    'com.etzhayyim.apps.yadoya.cancelReservation',
    { reservationId, reason },
    { bearer },
  );
}
