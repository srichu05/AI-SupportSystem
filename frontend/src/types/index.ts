// Issue coverage states explicitly defined in PRD & API_SPEC
export type IssueCoverageStatus =
  | 'covered'
  | 'partially_covered'
  | 'uncovered'
  | 'prohibited'
  | 'conflict'
  | 'needs_human_review';

export type TonePreset = 'empathetic' | 'concise' | 'formal';

export type GuardrailVerdict = 'PASSED' | 'FLAGGED';

export interface Citation {
  citation_id: string;
  document_title: string;
  clause_id: string;
  section_name: string;
  page_number?: number;
  excerpt: string;
  confidence_score: number;
}

export interface DecomposedConcern {
  concern_id: string;
  category: string;
  summary: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: IssueCoverageStatus;
  rationale?: string;
  citations: Citation[];
}

export interface UnsupportedCommitment {
  claim: string;
  reason: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
}

export interface GuardrailReport {
  verdict: GuardrailVerdict;
  unsupported_commitments_detected: UnsupportedCommitment[];
  policy_conflicts_detected: string[];
  policy_gaps_detected: string[];
}

export interface GroundedDraft {
  tone: TonePreset;
  subject: string;
  body: string;
  anchored_clause_ids: string[];
}

export interface ComplaintTicket {
  complaint_id: string;
  customer_id: string;
  customer_name: string;
  customer_email?: string;
  channel: 'email' | 'chat' | 'ticket' | 'phone_transcript';
  received_at: string;
  raw_text: string;
  overall_sentiment: 'negative' | 'frustrated' | 'neutral' | 'urgent';
  overall_severity: 'low' | 'medium' | 'high' | 'critical';
  review_status: 'PENDING_REVIEW' | 'APPROVED' | 'SIMULATED_DISPATCH' | 'ESCALATED' | 'REJECTED';
}

export interface ComplaintAnalysis {
  complaint_id: string;
  analysis_timestamp: string;
  overall_sentiment: string;
  overall_severity: 'low' | 'medium' | 'high' | 'critical';
  decomposed_concerns: DecomposedConcern[];
  guardrail_report: GuardrailReport;
  grounded_draft: GroundedDraft;
  human_review_required: boolean;
  review_reasons: string[];
}

export interface PolicyDocument {
  policy_id: string;
  title: string;
  version: string;
  category: string;
  updated_at: string;
  total_chunks: number;
  status: 'active' | 'archived' | 'draft';
  is_demo_fixture?: boolean;
}

export interface DispatchPayload {
  complaint_id: string;
  agent_id: string;
  agent_name: string;
  action: 'APPROVE' | 'REJECT' | 'ESCALATE';
  final_text: string;
  notes?: string;
  override_reasons?: string[];
}

export interface DispatchResponse {
  dispatch_id: string;
  complaint_id: string;
  status: 'SIMULATED_DISPATCH' | 'ESCALATED' | 'REJECTED';
  dispatched_at: string;
  audit_log_id: string;
  delivery_channel?: string;
}
