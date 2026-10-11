import React, { useState } from 'react';
import {
  Search,
  BookOpen,
  Mail,
  MessageSquare,
  Ticket,
  Shield,
  Layers,
} from 'lucide-react';
import { ComplaintTicket, PolicyDocument } from '../../types';

interface TicketSidebarProps {
  tickets: ComplaintTicket[];
  selectedTicketId: string;
  onSelectTicket: (ticketId: string) => void;
  policies: PolicyDocument[];
  isOpenMobile: boolean;
  onCloseMobile: () => void;
}

export const TicketSidebar: React.FC<TicketSidebarProps> = ({
  tickets,
  selectedTicketId,
  onSelectTicket,
  policies,
  isOpenMobile,
  onCloseMobile,
}) => {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredTickets = tickets.filter(
    (t) =>
      t.customer_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.complaint_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.raw_text.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStatusText = (status: string) => {
    switch (status) {
      case 'SIMULATED_DISPATCH':
      case 'DISPATCHED':
      case 'APPROVED':
        return { label: 'Dispatched', color: 'text-[#72B095] bg-[#162620]' };
      case 'ESCALATED':
        return { label: 'Escalated', color: 'text-[#8BA7D9] bg-[#1A2230]' };
      case 'REJECTED':
        return { label: 'Rejected', color: 'text-[#D97373] bg-[#261616]' };
      default:
        return { label: 'Review', color: 'text-[#D3A365] bg-[#272016]' };
    }
  };

  return (
    <>
      {/* Mobile backdrop */}
      {isOpenMobile && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={onCloseMobile}
        />
      )}

      <aside
        className={`fixed lg:static top-0 bottom-0 left-0 z-50 w-72 bg-[#13161B] border-r border-[#292E36] flex flex-col transition-transform duration-200 ease-in-out shrink-0 select-none ${
          isOpenMobile ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        {/* Compact App Header */}
        <div className="h-14 px-4 border-b border-[#292E36] flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-6 h-6 rounded bg-[#181C22] border border-[#292E36] flex items-center justify-center text-[#8BA7D9]">
              <Shield className="w-3.5 h-3.5" />
            </div>
            <div>
              <span className="text-xs font-semibold text-[#E8EAED] tracking-tight">
                PolicyPulse
              </span>
              <span className="text-[10px] text-[#9299A5] ml-1.5 font-mono">
                Agent
              </span>
            </div>
          </div>
          <span className="text-[11px] font-mono text-[#9299A5]">
            {filteredTickets.length} cases
          </span>
        </div>

        {/* Search */}
        <div className="p-3 border-b border-[#292E36]/60">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-[#9299A5] absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              placeholder="Search complaints or ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 text-xs bg-[#181C22] border border-[#292E36] rounded-md text-[#E8EAED] placeholder-[#9299A5] focus:outline-none focus:border-[#8BA7D9] transition-colors"
            />
          </div>
        </div>

        {/* Compact Ticket List */}
        <div className="flex-1 overflow-y-auto divide-y divide-[#292E36]/40">
          {filteredTickets.map((ticket) => {
            const isSelected = ticket.complaint_id === selectedTicketId;
            const statusInfo = getStatusText(ticket.review_status);

            return (
              <div
                key={ticket.complaint_id}
                onClick={() => {
                  onSelectTicket(ticket.complaint_id);
                  onCloseMobile();
                }}
                className={`p-3 text-left transition-colors cursor-pointer relative ${
                  isSelected
                    ? 'bg-[#181C22]'
                    : 'hover:bg-[#181C22]/60'
                }`}
              >
                {/* Active indicator bar */}
                {isSelected && (
                  <div className="absolute left-0 top-0 bottom-0 w-[2.5px] bg-[#8BA7D9]" />
                )}

                <div className="flex items-center justify-between gap-2 mb-1">
                  <span
                    className={`text-xs truncate font-medium ${
                      isSelected ? 'text-[#E8EAED]' : 'text-[#E8EAED]/85'
                    }`}
                  >
                    {ticket.customer_name}
                  </span>
                  <span
                    className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${statusInfo.color}`}
                  >
                    {statusInfo.label}
                  </span>
                </div>

                <div className="flex items-center gap-2 mb-1.5 text-[11px] font-mono text-[#9299A5]">
                  <span>{ticket.complaint_id}</span>
                  <span>•</span>
                  <span className="capitalize">{ticket.channel}</span>
                </div>

                <p className="text-[11px] text-[#9299A5] line-clamp-1 leading-normal font-sans">
                  {ticket.raw_text}
                </p>
              </div>
            );
          })}
        </div>

        {/* Minimal Policy Footer */}
        <div className="p-3 border-t border-[#292E36] bg-[#101217]">
          <div className="flex items-center justify-between text-[11px] text-[#9299A5]">
            <span className="flex items-center gap-1.5">
              <BookOpen className="w-3.5 h-3.5 text-[#8BA7D9]" />
              <span>{policies.length} Active Policies</span>
            </span>
            <span className="text-[10px] font-mono text-[#72B095]">Synchronized</span>
          </div>
        </div>
      </aside>
    </>
  );
};
