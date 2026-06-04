declare module '@etzhayyim/ameno/inference' {
  export type ChatMessage = any;
  export type GenerationStats = any;
  export type InferenceState = any;

  export function checkWebGPU(): Promise<boolean>;
  export function generate(...args: any[]): Promise<GenerationStats>;
  export function getActiveAdapterIds(): string[];
  export function getGPUInfo(): Promise<string>;
  export function loadModel(...args: any[]): Promise<any>;
  export function setLoraAdapters(...args: any[]): void;
}
