export type EntityKind =
  | "axis" | "cell" | "app" | "adr"
  | "organism" | "ecosystem" | "fruit" | "seed";

export interface Entity {
  id: string;
  kind: EntityKind;
  title: string;
  state: Record<string, any>;
  activity: any[];
  chat_invite: string;
  neighbors: string[];
  pruning_severity: number;
}

export interface AliveTuple {
  M_motion: number;
  D_diversity: number;
  C_coupling: number;
  P_pruning: number;
  G_generational: number;
  timestamp: string;
  notes: string[];
}

export interface PruningCandidate {
  id: string;
  kind: string;
  path: string;
  idle_days: number;
  severity: number;
  reasons: string[];
}

export interface Snapshot {
  timestamp: number;
  alive: AliveTuple;
  in_band: Record<string, boolean>;
  axis_scores: Record<string, number>;
  entities: Record<string, Entity>;
  flowers: string[];
  fruits: string[];
  seeds: { id: string; from: string; to: string; carries: string }[];
  activity: any[];
  pruning: PruningCandidate[];
  trajectory: Record<string, number[]>;
  trajectory_cycles: number[];
  trajectory_totals: number[];
}

export interface NodePos {
  id: string;
  kind: EntityKind;
  x: number;
  y: number;
  vx: number;
  vy: number;
  r: number;        // visual radius (for shape sizing + collisions)
  phase: number;    // breathing phase
}
