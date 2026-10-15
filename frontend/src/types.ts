export type Entity = {
  id: string;
  kind: string;
  title: string;
  excerpt?: string;
  source_type?: string;
  timestamp?: string;
  enabled?: boolean;
  value?: number;
  partner?: string;
  status?: string;
  valid_from?: string;
  valid_to?: string;
  recorded_from?: string;
  recorded_to?: string;
  approved?: boolean;
  description?: string;
  role?: string;
  [key: string]: unknown;
};
export type Graph = {
  nodes: Entity[];
  edges: { source: string; target: string; relation: string }[];
  revision?: number;
};
export type Check = {
  partner: string;
  status: string;
  minimum_ms: number | null;
  proposed_ms: number;
  reason: string;
};
export type Receipt = {
  id: string;
  title: string;
  assessment: string;
  created_at: string;
  revision: number;
  stale: boolean;
  sources: Entity[];
  checks: Check[];
  conflicts: { partner: string; message: string; source_id: string }[];
  gaps: string[];
  trace: { tool: string; scope: string; ms: number; rows: number }[];
  graph: Graph;
  graph_ms: number;
  model_ms: number;
  total_ms: number;
  mode: string;
  agent_error?: string;
  agent_summary?: { summary: string; source_ids: string[]; next_step: string };
  request: Record<string, unknown>;
};
export type Action = {
  id: string;
  status: string;
  markdown: string;
  reviewer: string;
};
export type Rehearsal = {
  before: Check[];
  alternative: Check[];
  base_unchanged: boolean;
  revision: number;
  method: string;
  assumptions: string[];
};
