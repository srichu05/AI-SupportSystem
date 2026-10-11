import React from 'react';
import { AlertTriangle, ShieldCheck } from 'lucide-react';
import { GuardrailReport } from '../../types';

interface GuardrailBannerProps {
  report: GuardrailReport;
}

export const GuardrailBanner: React.FC<GuardrailBannerProps> = ({ report }) => {
  const isFlagged = report.verdict === 'FLAGGED';

  // If passed, show a subtle quiet confirmation without screaming at the agent
  if (!isFlagged) {
    return (
      <div className="p-3 rounded-lg bg-[#162620]/60 border border-[#234235] text-[#72B095] text-xs flex items-center justify-between mb-5">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 shrink-0 text-[#72B095]" />
          <span>Automated Policy Verification: Compliant with standard frontline thresholds. Human sign-off required.</span>
        </div>
        <span className="text-[10px] font-mono text-[#72B095]/80 uppercase">Passed</span>
      </div>
    );
  }

  // If flagged, show a restrained, purposeful warning
  return (
    <div className="p-4 rounded-xl bg-[#261616] border border-[#4A2525] text-[#E8EAED] text-xs mb-5 space-y-2.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-[#D97373] font-medium text-xs">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>Policy Restriction Detected</span>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#4A2525]/60 text-[#D97373] border border-[#4A2525]">
          Commitment Blocked
        </span>
      </div>

      <div className="space-y-2 pt-1 text-xs">
        {report.unsupported_commitments_detected.map((item, idx) => (
          <div
            key={idx}
            className="p-3 rounded-lg bg-[#181C22]/80 border border-[#4A2525]/50 text-xs"
          >
            <div className="font-medium text-[#E8EAED] mb-1">
              Unauthorized concession: <span className="text-[#D97373]">"{item.claim}"</span>
            </div>
            <div className="text-[#9299A5] text-[11px] leading-relaxed">
              {item.reason}
            </div>
          </div>
        ))}
        <div className="text-[11px] text-[#9299A5] font-mono pt-0.5">
          Action required: Revise or remove this commitment in the draft response below before authorizing dispatch.
        </div>
      </div>
    </div>
  );
};
