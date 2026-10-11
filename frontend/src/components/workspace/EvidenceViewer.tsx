import React from 'react';
import { BookOpen, AlertCircle, FileText } from 'lucide-react';
import { DecomposedConcern } from '../../types';
import { Badge } from '../ui/Badge';

interface EvidenceViewerProps {
  concern?: DecomposedConcern;
}

export const EvidenceViewer: React.FC<EvidenceViewerProps> = ({ concern }) => {
  if (!concern) {
    return (
      <div className="p-6 rounded-xl bg-[#181C22] border border-[#292E36] text-center text-xs text-[#9299A5]">
        Select an identified issue to inspect supporting policy evidence.
      </div>
    );
  }

  return (
    <div className="bg-[#181C22] border border-[#292E36] rounded-xl p-5 shadow-sm flex flex-col gap-3.5">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-[#292E36]/60">
        <div className="flex items-center gap-2">
          <BookOpen className="w-3.5 h-3.5 text-[#8BA7D9]" />
          <h3 className="text-xs font-semibold uppercase tracking-wider text-[#E8EAED]">
            Policy Evidence
          </h3>
        </div>
        <Badge status={concern.status} size="sm" />
      </div>

      {/* Active Focus */}
      <div className="text-xs text-[#9299A5]">
        Active focus: <span className="text-[#E8EAED] font-medium">{concern.category}</span>
      </div>

      {/* Citations List */}
      {concern.citations.length === 0 ? (
        <div className="p-3.5 rounded-lg bg-[#272016]/40 border border-[#483A24] text-[#D3A365] text-xs flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-[#D3A365]" />
          <div>
            <span className="font-medium block mb-0.5">No Matching Policy Clauses</span>
            <p className="text-[#9299A5] leading-relaxed text-[11px]">
              Active policy documents do not contain specific guidance for this inquiry. Flagged for agent discretion.
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {concern.citations.map((cit) => (
            <div
              key={cit.citation_id}
              className="p-3.5 rounded-lg bg-[#13161B] border border-[#292E36] space-y-2 text-xs"
            >
              {/* Clause ID & Section Reference */}
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-xs font-semibold text-[#8BA7D9]">
                  {cit.clause_id}
                </span>
                <span className="text-[11px] font-mono text-[#9299A5]">
                  {cit.section_name} {cit.page_number && `• Page ${cit.page_number}`}
                </span>
              </div>

              {/* Document Title */}
              <div className="text-[11px] text-[#9299A5] font-mono">
                {cit.document_title}
              </div>

              {/* Verified Policy Excerpt */}
              <div className="p-3 rounded bg-[#0D0F12] border-l-2 border-[#8BA7D9] text-xs text-[#E8EAED] leading-relaxed font-sans">
                "{cit.excerpt}"
              </div>

              {/* Concise Policy Indication */}
              <div className="text-[11px] text-[#9299A5] pt-0.5 flex items-center gap-1.5">
                <FileText className="w-3 h-3 text-[#8BA7D9]" />
                <span>
                  {concern.status === 'prohibited'
                    ? 'Restricts compensation or concessions'
                    : concern.status === 'covered'
                    ? 'Authorizes replacement or return'
                    : 'Provides partial guidance for claim'}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
