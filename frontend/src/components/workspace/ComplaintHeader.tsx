import React from 'react';
import { ComplaintTicket } from '../../types';

interface ComplaintHeaderProps {
  ticket: ComplaintTicket;
}

export const ComplaintHeader: React.FC<ComplaintHeaderProps> = ({ ticket }) => {
  return (
    <div className="bg-[#181C22] border border-[#292E36] rounded-xl p-5 mb-5 shadow-xs">
      {/* Top Details Line */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[#292E36]/60 mb-4">
        <div>
          <div className="flex items-center gap-2.5">
            <h2 className="text-sm font-semibold text-[#E8EAED]">
              {ticket.customer_name}
            </h2>
            <span className="font-mono text-xs text-[#8BA7D9] bg-[#1A2230] px-2 py-0.5 rounded border border-[#2B3952]">
              {ticket.complaint_id}
            </span>
          </div>
          <div className="text-[11px] text-[#9299A5] font-mono mt-0.5">
            {ticket.customer_email || 'customer@example.com'} • {ticket.customer_id}
          </div>
        </div>

        <div className="flex items-center gap-3 text-xs text-[#9299A5] font-mono">
          <span>Channel: <strong className="text-[#E8EAED] uppercase text-[11px]">{ticket.channel}</strong></span>
          <span>•</span>
          <span>Received: <strong className="text-[#E8EAED]">{ticket.received_at}</strong></span>
        </div>
      </div>

      {/* Inbound Customer Statement */}
      <div>
        <span className="text-[10px] font-mono uppercase tracking-wider text-[#9299A5] block mb-1.5">
          Inbound Customer Statement
        </span>
        <div className="p-3.5 rounded-lg bg-[#13161B] border border-[#292E36]/80 text-[#E8EAED] text-xs sm:text-sm leading-relaxed font-sans">
          "{ticket.raw_text}"
        </div>
      </div>
    </div>
  );
};
