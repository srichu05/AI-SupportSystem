import React, { useState } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  FileText,
  ExternalLink,
  Layers,
} from 'lucide-react';
import { Badge } from '../ui/Badge';
import { MOCK_TICKETS, MOCK_ANALYSES } from '../../data/mockData';
import { DecomposedConcern } from '../../types';
import { useInView } from '../../hooks/useInView';

interface InteractiveDemoProps {
  onLaunchStudioWithTicket: (ticketId: string) => void;
}

export const InteractiveDemo: React.FC<InteractiveDemoProps> = ({
  onLaunchStudioWithTicket,
}) => {
  const { ref, isInView } = useInView({ threshold: 0.1 });
  const [selectedTicketId, setSelectedTicketId] = useState<string>('CMP-2026-9042');
  const [selectedConcernIndex, setSelectedConcernIndex] = useState<number>(0);
  const [isTransitioning, setIsTransitioning] = useState<boolean>(false);

  const activeTicket =
    MOCK_TICKETS.find((t) => t.complaint_id === selectedTicketId) || MOCK_TICKETS[0];
  const activeAnalysis = MOCK_ANALYSES[selectedTicketId]?.empathetic;
  const activeConcern: DecomposedConcern | undefined =
    activeAnalysis?.decomposed_concerns[selectedConcernIndex];

  const handleSelectTicket = (id: string) => {
    if (id === selectedTicketId) return;
    setIsTransitioning(true);
    setTimeout(() => {
      setSelectedTicketId(id);
      setSelectedConcernIndex(0);
      setIsTransitioning(false);
    }, 120);
  };

  return (
    <section
      id="demo"
      ref={ref}
      className="py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto bg-transparent"
    >
      {/* Section Header */}
      <div
        className={`flex flex-col md:flex-row md:items-end justify-between gap-6 pb-8 border-b border-[#292E36] mb-10 transition-all duration-700 ${
          isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'
        }`}
      >
        <div>
          <span className="text-[10px] font-mono uppercase tracking-widest text-[#9299A5] block mb-2">
            INTERACTIVE PREVIEW
          </span>
          <h2
            className="text-3xl sm:text-4xl lg:text-5xl text-[#E8EAED] tracking-tight leading-tight font-normal"
            style={{ fontFamily: "'Instrument Serif', serif" }}
          >
            See policy grounding in action.
          </h2>
        </div>
        <p className="text-xs sm:text-sm text-[#9299A5] max-w-md font-sans font-normal leading-relaxed">
          Select an enterprise ticket scenario to inspect atomic decomposition, retrieved handbook citations, and commitment guardrails in real time.
        </p>
      </div>

      {/* Visual Pipeline Stages */}
      <div className="hidden sm:flex items-center gap-3 text-[11px] font-mono text-[#9299A5] mb-6 px-1">
        <span className="flex items-center gap-1.5 text-[#E8EAED]">
          <span className="w-1.5 h-1.5 rounded-full bg-[#72B095]" />
          Raw Inbound Statement
        </span>
        <span className="text-[#292E36]">→</span>
        <span className="flex items-center gap-1.5 text-[#E8EAED]/85">
          <Layers className="w-3 h-3 text-[#9299A5]" />
          Atomic Decomposition
        </span>
        <span className="text-[#292E36]">→</span>
        <span className="flex items-center gap-1.5 text-[#8BA7D9]">
          <FileText className="w-3 h-3" />
          Policy Evidence
        </span>
        <span className="text-[#292E36]">→</span>
        <span className="flex items-center gap-1.5 text-[#9299A5]">
          <ShieldCheck className="w-3 h-3" />
          Guardrail Verification
        </span>
      </div>

      {/* Scenario / Ticket Selector */}
      <div className="flex flex-wrap items-center gap-2 mb-8">
        {MOCK_TICKETS.map((t) => {
          const isSelected = t.complaint_id === selectedTicketId;
          return (
            <button
              key={t.complaint_id}
              onClick={() => handleSelectTicket(t.complaint_id)}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all duration-150 border cursor-pointer ${
                isSelected
                  ? 'bg-[#1E232B] text-[#E8EAED] border-[#8BA7D9] shadow-xs'
                  : 'bg-[#181C22] text-[#9299A5] border-[#292E36] hover:text-[#E8EAED] hover:border-[#292E36]/80'
              }`}
            >
              <span className="font-mono text-[#9299A5] mr-1.5">{t.complaint_id}:</span>
              <span>{t.customer_name}</span>
            </button>
          );
        })}
      </div>

      {/* Main Console Surface */}
      <div
        className={`rounded-2xl bg-[#181C22] border border-[#292E36] overflow-hidden p-6 sm:p-8 transition-opacity duration-150 shadow-sm ${
          isTransitioning ? 'opacity-40' : 'opacity-100'
        }`}
      >
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Column: Raw Ticket & Decomposed Issues (5 cols) */}
          <div className="lg:col-span-5 flex flex-col gap-6">
            {/* Raw Ticket Statement Box */}
            <div className="p-4 sm:p-5 rounded-xl bg-[#13161B] border border-[#292E36]">
              <div className="flex items-center justify-between mb-3 text-xs">
                <span className="font-mono text-[10px] text-[#9299A5] uppercase tracking-wider">
                  Raw Inbound Statement
                </span>
                <span className="text-[10px] text-[#9299A5] font-mono bg-[#181C22] px-2 py-0.5 rounded border border-[#292E36] uppercase">
                  {activeTicket.channel}
                </span>
              </div>
              <p className="text-xs sm:text-[13px] text-[#E8EAED] leading-relaxed font-sans font-light italic">
                "{activeTicket.raw_text}"
              </p>
            </div>

            {/* Decomposed Issues */}
            <div>
              <div className="flex items-center justify-between mb-3 text-xs">
                <span className="font-mono text-[10px] text-[#9299A5] uppercase tracking-wider flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-[#8BA7D9]" />
                  Identified Issues ({activeAnalysis?.decomposed_concerns.length})
                </span>
                <span className="text-[10px] text-[#9299A5] font-mono">Select to inspect</span>
              </div>

              <div className="space-y-2">
                {activeAnalysis?.decomposed_concerns.map((concern, idx) => {
                  const isActive = idx === selectedConcernIndex;
                  return (
                    <div
                      key={concern.concern_id}
                      onClick={() => setSelectedConcernIndex(idx)}
                      className={`p-3.5 rounded-xl border text-left cursor-pointer transition-all duration-150 ${
                        isActive
                          ? 'bg-[#13161B] border-[#8BA7D9] shadow-xs'
                          : 'bg-[#13161B]/50 border-[#292E36] hover:bg-[#13161B] hover:border-[#292E36]/80'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2 mb-1.5">
                        <span
                          className={`text-xs font-medium truncate ${
                            isActive ? 'text-[#E8EAED]' : 'text-[#E8EAED]/85'
                          }`}
                        >
                          {concern.category}
                        </span>
                        <Badge status={concern.status} size="sm" />
                      </div>
                      <p className="text-[11px] text-[#9299A5] line-clamp-1 font-light">
                        {concern.summary}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Right Column: Grounded Evidence Citation & Guardrail Report (7 cols) */}
          <div className="lg:col-span-7 flex flex-col justify-between gap-6 p-6 rounded-xl bg-[#13161B] border border-[#292E36]">
            {/* Cited Clause Panel */}
            <div>
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-[#292E36] text-xs">
                <span className="font-mono text-[10px] text-[#9299A5] uppercase tracking-wider flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-[#8BA7D9]" />
                  Retrieved Policy Evidence
                </span>
                <span className="text-[10px] font-mono text-[#9299A5]">
                  Active Concern: {activeConcern?.category}
                </span>
              </div>

              {activeConcern?.citations[0] ? (
                <div className="p-4 rounded-xl bg-[#181C22] border border-[#292E36] space-y-2.5 transition-all duration-150">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono font-medium text-[#8BA7D9]">
                      {activeConcern.citations[0].clause_id}
                    </span>
                    <span className="text-[#9299A5] text-[10px] font-mono">
                      Page {activeConcern.citations[0].page_number}
                    </span>
                  </div>
                  <div className="text-[11px] text-[#9299A5] font-mono">
                    {activeConcern.citations[0].document_title} • {activeConcern.citations[0].section_name}
                  </div>
                  <div className="p-3 rounded-lg bg-[#0D0F12] border-l-2 border-[#8BA7D9] text-xs text-[#E8EAED] font-sans leading-relaxed italic">
                    "{activeConcern.citations[0].excerpt}"
                  </div>
                </div>
              ) : (
                <div className="p-4 rounded-xl bg-[#181C22] border border-[#292E36] text-center text-xs text-[#9299A5] font-mono">
                  No matching policy clause indexed. Issue tagged for human review.
                </div>
              )}
            </div>

            {/* Guardrail Safety Status */}
            <div
              className={`p-4 rounded-xl border flex items-start gap-3 text-xs transition-all duration-150 ${
                activeAnalysis?.guardrail_report.verdict === 'FLAGGED'
                  ? 'bg-[#261616] border-[#4A2525] text-[#E8EAED]'
                  : 'bg-[#162620] border-[#234235] text-[#72B095]'
              }`}
            >
              {activeAnalysis?.guardrail_report.verdict === 'FLAGGED' ? (
                <ShieldAlert className="w-4 h-4 text-[#D97373] shrink-0 mt-0.5" />
              ) : (
                <ShieldCheck className="w-4 h-4 text-[#72B095] shrink-0 mt-0.5" />
              )}
              <div className="flex-1">
                <div className="font-mono text-[10px] uppercase tracking-wider mb-1 flex items-center justify-between">
                  <span>Guardrail Status: {activeAnalysis?.guardrail_report.verdict}</span>
                  {activeAnalysis?.guardrail_report.verdict === 'FLAGGED' && (
                    <span className="text-[#D97373] font-semibold bg-[#4A2525]/60 px-1.5 py-0.5 rounded border border-[#4A2525]">
                      Commitment Blocked
                    </span>
                  )}
                </div>
                {activeAnalysis?.guardrail_report.verdict === 'FLAGGED' ? (
                  <p className="text-[11px] text-[#9299A5] leading-relaxed">
                    {activeAnalysis?.guardrail_report.unsupported_commitments_detected[0]?.reason}
                  </p>
                ) : (
                  <p className="text-[11px] text-[#72B095]/90 leading-relaxed">
                    Zero unauthorized commitments detected. All draft remedies strictly grounded in policy.
                  </p>
                )}
              </div>
            </div>

            {/* Bottom Action Bar */}
            <div className="pt-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-t border-[#292E36]">
              <span className="text-[10px] text-[#9299A5] font-mono">
                Mandatory human review prior to customer dispatch.
              </span>
              <button
                onClick={() => onLaunchStudioWithTicket(selectedTicketId)}
                className="bg-[#8BA7D9] text-[#0D0F12] font-semibold hover:bg-[#9BB7E9] inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs transition-colors cursor-pointer self-start sm:self-auto shadow-xs"
              >
                <span>Review in Agent Studio</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
