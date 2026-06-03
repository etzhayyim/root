declare module '@etzhayyim/ameno/lora-runtime' {
  export type AdapterMergeSpec = any;
  export type LoadedLoraAdapter = any;

  export function applyLoraAdapters(...args: any[]): Promise<any>;
  export function fetchLoraAdapter(...args: any[]): Promise<LoadedLoraAdapter>;
}
