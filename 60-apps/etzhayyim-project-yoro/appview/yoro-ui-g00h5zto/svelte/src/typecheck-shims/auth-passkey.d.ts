declare module '$lib/auth/passkey' {
  export function getSessionToken(): Promise<string | null>;
}
