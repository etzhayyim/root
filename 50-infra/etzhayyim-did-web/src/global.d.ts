// Type declarations for asset imports in Cloudflare Worker

declare module "*.wasm" {
  const content: Uint8Array;
  export default content;
}

declare module "*.js" {
  const content: string;
  export default content;
}