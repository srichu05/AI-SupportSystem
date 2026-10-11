import {
  ComplaintTicket,
  ComplaintAnalysis,
  PolicyDocument,
  DispatchPayload,
  DispatchResponse,
  TonePreset,
} from '../types';
import { MOCK_TICKETS } from '../data/mockData';

/**
 * Normalizes the API base URL to ensure the `/api/v1` prefix is always present,
 * avoiding duplication or omission regardless of whether VITE_API_BASE_URL is configured as:
 * - https://example.onrender.com
 * - https://example.onrender.com/
 * - https://example.onrender.com/api
 * - https://example.onrender.com/api/v1
 * - https://example.onrender.com/api/v1/
 */
export const normalizeApiBaseUrl = (rawUrl?: string): string => {
  const fallback = 'http://127.0.0.1:8000/api/v1';
  if (!rawUrl || !rawUrl.trim()) {
    return fallback;
  }
  const trimmed = rawUrl.trim().replace(/\/+$/, '');
  if (trimmed.endsWith('/api/v1')) {
    return trimmed;
  }
  if (trimmed.endsWith('/api')) {
    return `${trimmed}/v1`;
  }
  return `${trimmed}/api/v1`;
};

export const API_BASE_URL = normalizeApiBaseUrl(import.meta.env.VITE_API_BASE_URL);

export interface BackendStatus {
  isLive: boolean;
  message: string;
  timestamp: string;
}

type TokenGetter = () => Promise<string | null>;
let currentTokenGetter: TokenGetter | null = null;

export const setAuthTokenGetter = (getter: TokenGetter | null) => {
  currentTokenGetter = getter;
};

export const getAuthToken = async (): Promise<string | null> => {
  if (currentTokenGetter) {
    try {
      const token = await currentTokenGetter();
      if (token) return token;
    } catch {
      // ignore
    }
  }
  if (typeof window !== 'undefined' && (window as any).Clerk?.session) {
    try {
      return await (window as any).Clerk.session.getToken();
    } catch {
      // ignore
    }
  }
  return null;
};

export const apiService = {
  // Check health of backend service
  async checkHealth(): Promise<BackendStatus> {
    try {
      const res = await fetch(`${API_BASE_URL}/health`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });
      if (res.ok) {
        const data = await res.json();
        return {
          isLive: true,
          message: `Connected to FastAPI (${data.status || 'ok'})`,
          timestamp: new Date().toISOString(),
        };
      }
      return {
        isLive: false,
        message: `Backend returned HTTP ${res.status}`,
        timestamp: new Date().toISOString(),
      };
    } catch (err: any) {
      return {
        isLive: false,
        message: `FastAPI Backend Offline / Unreachable (${err.message || 'NetworkError'})`,
        timestamp: new Date().toISOString(),
      };
    }
  },

  // Get active complaint tickets from database
  async getTickets(): Promise<ComplaintTicket[]> {
    const token = await getAuthToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };

    try {
      const res = await fetch(`${API_BASE_URL}/complaints`, { headers });
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) {
          return data.map((c: any) => ({
            complaint_id: c.complaint_id,
            customer_id: c.complaint_id.slice(0, 8),
            customer_name: c.created_by_agent_name || 'Customer Inquiry',
            channel: 'email' as const,
            received_at: new Date().toISOString(),
            raw_text:
              c.issues?.map((i: any) => i.issue_text).join(' ') ||
              c.draft?.text ||
              'Customer inquiry recorded in system',
            overall_sentiment: c.status === 'needs_human_review' ? 'urgent' : 'neutral',
            overall_severity: 'medium' as const,
            review_status:
              c.status === 'reviewed'
                ? 'APPROVED'
                : c.status === 'escalated'
                ? 'ESCALATED'
                : 'PENDING_REVIEW',
          }));
        }
      }
    } catch {
      // Network error or unauthenticated initial load
    }

    // Return curated starter complaints for initial analysis when no complaints exist yet
    return MOCK_TICKETS;
  },

  // Get enterprise policy documents from database
  async getPolicies(): Promise<PolicyDocument[]> {
    const token = await getAuthToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };

    const res = await fetch(`${API_BASE_URL}/policies`, { headers });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(`Failed to load policies (${res.status}): ${err.detail || res.statusText}`);
    }

    const raw = await res.json();
    return (raw || []).map((p: any) => ({
      policy_id: p.document_id || p.policy_id || '',
      title: p.source_filename || p.title || 'Policy Document',
      version: p.version_label || p.version || 'v1.0',
      category: p.document_type || p.category || 'General',
      updated_at: p.created_at || new Date().toISOString(),
      total_chunks: p.chunk_count || p.total_chunks || 0,
      status: (p.status || 'active') as 'active' | 'archived' | 'draft',
    }));
  },

  // Analyze complaint with RAG decomposition, citations, guardrail check
  async analyzeComplaint(
    ticket: ComplaintTicket,
    tone: TonePreset = 'empathetic'
  ): Promise<{ analysis: ComplaintAnalysis; isLive: boolean }> {
    const token = await getAuthToken();
    if (!token) {
      throw new Error(
        'Authentication required: Please sign in with Clerk to analyze complaints and retrieve evidence.'
      );
    }

    const toneParam = tone === 'formal' ? 'professional' : tone;
    const res = await fetch(`${API_BASE_URL}/complaints`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        complaint_text: ticket.raw_text,
        response_tone: toneParam,
        generate_tone_variants: true,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const msg = err.detail || err.error?.message || res.statusText;
      throw new Error(`Complaint analysis failed (${res.status}): ${msg}`);
    }

    const data = await res.json();
    const analysis: ComplaintAnalysis = {
      complaint_id: data.complaint_id,
      analysis_timestamp: new Date().toISOString(),
      overall_sentiment: data.status === 'needs_human_review' ? 'urgent' : 'neutral',
      overall_severity: 'medium',
      decomposed_concerns: (data.issues || []).map((iss: any, idx: number) => ({
        concern_id: iss.issue_id || `ISS-${idx + 1}`,
        category: iss.requested_resolution || 'General Inquiry',
        summary: iss.issue_text,
        severity: 'medium',
        status: iss.assessment_status || 'needs_human_review',
        rationale: iss.missing_facts?.length
          ? `Missing customer facts: ${iss.missing_facts.join(', ')}`
          : undefined,
        citations: (iss.evidence || []).map((ev: any) => ({
          citation_id: ev.chunk_id,
          document_title: ev.source_filename || 'Policy Document',
          clause_id: ev.section || 'General Clause',
          section_name: ev.section || 'General Terms',
          page_number: ev.page_number,
          excerpt: ev.content,
          confidence_score: 0.95,
        })),
      })),
      guardrail_report: {
        verdict: data.validation?.valid ? 'PASSED' : 'FLAGGED',
        unsupported_commitments_detected: (data.validation?.errors || []).map((e: string) => ({
          claim: e,
          reason: 'Deterministic policy rule or citation constraint violation detected',
          severity: 'HIGH',
        })),
        policy_conflicts_detected: [],
        policy_gaps_detected: data.validation?.warnings || [],
      },
      grounded_draft: {
        tone: tone,
        subject: `Regarding your inquiry (${data.complaint_id.slice(0, 8)})`,
        body: data.draft?.text || '',
        anchored_clause_ids: data.draft?.citations || [],
      },
      human_review_required: data.status === 'needs_human_review' || !data.validation?.valid,
      review_reasons: data.validation?.errors || [],
    };

    return { analysis, isLive: true };
  },

  // Record human reviewer decision
  async dispatchComplaint(
    payload: DispatchPayload,
    draftId?: string
  ): Promise<{ response: DispatchResponse; isLive: boolean }> {
    const token = await getAuthToken();
    if (!token) {
      throw new Error(
        'Authentication required: Please sign in with Clerk before recording review decisions.'
      );
    }

    const decision =
      payload.action === 'APPROVE'
        ? 'approved'
        : payload.action === 'ESCALATE'
        ? 'escalated'
        : 'rejected';

    const res = await fetch(`${API_BASE_URL}/complaints/${payload.complaint_id}/review`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        draft_id: draftId || payload.complaint_id,
        decision: decision,
        final_response_text: payload.final_text,
        reason: payload.notes || undefined,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const msg = err.detail || err.error?.message || res.statusText;
      throw new Error(`Review decision submission failed (${res.status}): ${msg}`);
    }

    const data = await res.json();
    const response: DispatchResponse = {
      dispatch_id: data.review_id,
      complaint_id: data.complaint_id,
      status:
        data.decision === 'approved'
          ? 'SIMULATED_DISPATCH'
          : data.decision === 'escalated'
          ? 'ESCALATED'
          : 'REJECTED',
      dispatched_at: data.reviewed_at,
      audit_log_id: data.review_id,
      delivery_channel: 'Internal Review Decision Recorded',
    };

    return { response, isLive: true };
  },
};
