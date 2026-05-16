/**
 * @gftd/vectorization
 * Embedding/vector index orchestration interfaces.
 */

export interface VectorizationService {
  embed(text: string): Promise<number[]>;
}
