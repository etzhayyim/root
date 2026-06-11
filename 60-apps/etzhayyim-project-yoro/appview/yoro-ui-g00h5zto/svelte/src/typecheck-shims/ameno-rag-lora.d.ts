declare module '@etzhayyim/ameno/rag-lora' {
  export type RagLoraContext = any;
  export type RagResult = any;

  export function buildRagContextPrompt(...args: any[]): string;
  export function ragLoraSelect(...args: any[]): Promise<any>;
  export function ragSearch(...args: any[]): Promise<RagResult[]>;
}
