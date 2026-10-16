export type CompanyEntity = {
  id: string;
  kind: string;
  title: string;
  excerpt?: string;
  description?: string;
  source_type?: string;
  department?: string;
  timestamp?: string;
  enabled?: boolean;
  synthetic?: boolean;
  classification?: string;
  url?: string;
  [key: string]: unknown;
};
export type CompanyEdge = {
  source: string;
  target: string;
  relation: string;
  source_ids: string[];
};
export type CompanyGraph = { nodes: CompanyEntity[]; edges: CompanyEdge[] };
export type CommitmentCheck = {
  client: string;
  title: string;
  sunday_required: boolean | null;
  status: string;
  rule_ids: string[];
  source_ids: string[];
};
export type CompanyReceipt = {
  id: string;
  title: string;
  summary: string;
  commitment_context?: boolean;
  alerts?: {
    category: string;
    severity: "info" | "warning" | "success";
    title: string;
    message: string;
    source_ids: string[];
  }[];
  citations?: string[];
  provider?: string;
  model?: string;
  provider_note?: string;
  documents_to_review?: {
    id: string;
    title: string;
    source_id: string;
    reason: string;
  }[];
  assessment: string;
  checks: CommitmentCheck[];
  sources: CompanyEntity[];
  graph: CompanyGraph;
  revision: number;
  stale: boolean;
  mode: string;
  followups: string[];
  trace: { tool: string; rows: number; ms?: number }[];
  total_ms: number;
  agent_error?: string;
  request: {
    effective_at: string;
    known_at: string;
    focus_id?: string;
    client: string;
  };
};
export type CompanySession = {
  company?: CompanyEntity | null;
  clients: CompanyEntity[];
  demo?: {
    title: string;
    description: string;
    question: string;
    effective_at: string;
    known_at: string;
    before_effective: string;
    before_known: string;
    examples: { label: string; question: string }[];
    events: {
      id: "amendment" | "withdraw";
      label: string;
      description: string;
    }[];
  } | null;
  session_id: string;
  stats: {
    entities: number;
    connections: number;
    revision: number;
    labels: Record<string, number>;
  };
  sources: CompanyEntity[];
  graph: CompanyGraph;
  gemini_configured: boolean;
  investigator_configured: boolean;
  amendment_loaded: boolean;
  receipts: CompanyReceipt[];
  disclosure: string;
};
export type Preview = {
  assessment: string;
  rows: (CommitmentCheck & {
    consignments: number;
    before: string;
    after: string;
    alternative: string;
    queued_before: number;
    queued_after: number;
    queued_alternative: number | null;
  })[];
  scenario_sunday: string;
  known_at: string;
  base_unchanged: boolean;
  revision: number;
  method: string;
  cost: {
    before_inr: number;
    proposed_inr: number;
    alternative_inr: number | null;
    source_id: string;
  };
  documents_to_review: string[];
  assumptions: string[];
};
