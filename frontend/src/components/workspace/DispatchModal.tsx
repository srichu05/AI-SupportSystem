import React, { useState } from 'react';
import { ShieldCheck, CheckCircle2, AlertTriangle, Send, X } from 'lucide-react';
import { Button } from '../ui/Button';

interface DispatchModalProps {
  isOpen: boolean;
  onClose: () => void;
  actionType: 'APPROVE' | 'ESCALATE' | 'REJECT';
  complaintId: string;
  customerName: string;
  onConfirm: (notes: string) => void;
  isSubmitting?: boolean;
  errorMessage?: string | null;
}

export const DispatchModal: React.FC<DispatchModalProps> = ({
  isOpen,
  onClose,
  actionType,
  complaintId,
  customerName,
  onConfirm,
  isSubmitting = false,
  errorMessage,
}) => {
  const [notes, setNotes] = useState('');
  const [confirmedCheck, setConfirmedCheck] = useState(false);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
      <div className="relative w-full max-w-lg rounded-xl bg-[#181C22] border border-[#292E36] p-6 shadow-2xl text-[#E8EAED]">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-[#9299A5] hover:text-[#E8EAED] transition-colors p-1"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-3 mb-5">
          <div className="w-9 h-9 rounded-lg bg-[#13161B] border border-[#292E36] flex items-center justify-center text-[#8BA7D9]">
            {actionType === 'APPROVE' ? (
              <ShieldCheck className="w-5 h-5" />
            ) : (
              <AlertTriangle className="w-5 h-5 text-[#D3A365]" />
            )}
          </div>
          <div>
            <h3 className="text-sm font-semibold text-[#E8EAED]">
              {actionType === 'APPROVE'
                ? 'Authorize Response Sign-Off'
                : actionType === 'ESCALATE'
                ? 'Escalate to Tier-2 Lead'
                : 'Reject & Reset Draft'}
            </h3>
            <span className="text-[11px] text-[#9299A5] font-mono">
              Case {complaintId} • {customerName}
            </span>
          </div>
        </div>

        {/* Human Review Checklist */}
        <div className="p-3.5 rounded-lg bg-[#13161B] border border-[#292E36] mb-4 space-y-2 text-xs text-[#E8EAED]">
          <div className="font-medium text-[#9299A5] uppercase tracking-wider text-[10px] mb-1 font-mono">
            Mandatory Agent Certification
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-[#72B095]" />
            <span>Response verified against cited enterprise policy clauses.</span>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-[#72B095]" />
            <span>Commitment scanner confirmed for unauthorized promises.</span>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-[#72B095]" />
            <span>Tone appropriateness and customer PII inspected.</span>
          </div>
        </div>

        {/* Audit Mode Notice */}
        <div className="p-2.5 rounded-md bg-[#13161B] border border-[#292E36] text-[11px] text-[#9299A5] font-mono mb-4">
          External CRM Dispatch: Demo Simulation Mode (Records cryptographic compliance audit entry).
        </div>

        {/* Notes */}
        <div className="mb-4">
          <label className="text-xs text-[#9299A5] block mb-1.5 font-medium">
            Agent Audit Notes (Optional)
          </label>
          <textarea
            rows={3}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Add operational notes or justification for authorization..."
            className="w-full p-3 rounded-lg bg-[#13161B] border border-[#292E36] text-xs text-[#E8EAED] placeholder-[#9299A5] focus:outline-none focus:border-[#8BA7D9]"
          />
        </div>

        {/* Confirmation Checkbox */}
        <label className="flex items-center gap-2.5 mb-5 text-xs text-[#E8EAED] cursor-pointer select-none">
          <input
            type="checkbox"
            checked={confirmedCheck}
            onChange={(e) => setConfirmedCheck(e.target.checked)}
            className="rounded border-[#292E36] bg-[#13161B] text-[#8BA7D9] focus:ring-0 cursor-pointer"
          />
          <span>I formally certify this communication as an authorized support professional.</span>
        </label>

        {/* Error Alert if Submission Fails */}
        {errorMessage && (
          <div className="mb-4 p-3 rounded-lg bg-[#2A1515] border border-[#522323] text-[#F87171] text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0 text-[#F87171]" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-[#292E36]">
          <Button variant="ghost" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            size="md"
            disabled={!confirmedCheck || isSubmitting}
            onClick={() => onConfirm(notes)}
            icon={<Send className="w-3.5 h-3.5" />}
          >
            {isSubmitting ? 'Recording Audit...' : 'Confirm & Log Audit'}
          </Button>
        </div>
      </div>
    </div>
  );
};
