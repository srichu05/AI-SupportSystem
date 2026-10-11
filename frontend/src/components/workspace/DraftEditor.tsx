import React from 'react';
import { Send, AlertTriangle, RotateCcw } from 'lucide-react';
import { GroundedDraft, TonePreset } from '../../types';
import { Button } from '../ui/Button';

interface DraftEditorProps {
  draft: GroundedDraft;
  editedBody: string;
  onChangeBody: (newBody: string) => void;
  currentTone: TonePreset;
  onSelectTone: (tone: TonePreset) => void;
  onApprove: () => void;
  onReject: () => void;
  onEscalate: () => void;
  isSubmitting?: boolean;
}

export const DraftEditor: React.FC<DraftEditorProps> = ({
  draft,
  editedBody,
  onChangeBody,
  currentTone,
  onSelectTone,
  onApprove,
  onReject,
  onEscalate,
  isSubmitting = false,
}) => {
  const isEdited = editedBody !== draft.body;

  return (
    <div className="bg-[#181C22] border border-[#292E36] rounded-xl p-5 sm:p-6 shadow-sm flex flex-col">
      {/* Top Header: Title, Unsaved Changes, and Tone Selector */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3.5 border-b border-[#292E36]/60 mb-4">
        <div className="flex items-center gap-2.5">
          <h3 className="text-sm font-semibold text-[#E8EAED]">
            Response draft
          </h3>
          {isEdited ? (
            <span className="inline-flex items-center gap-1.5 text-[10px] font-mono text-[#8BA7D9] bg-[#1A2230] border border-[#2B3952] px-2 py-0.5 rounded">
              <span className="w-1.5 h-1.5 rounded-full bg-[#8BA7D9]" />
              Modified
            </span>
          ) : (
            <span className="text-[10px] font-mono text-[#9299A5] bg-[#13161B] border border-[#292E36] px-2 py-0.5 rounded">
              AI Grounded Draft
            </span>
          )}
        </div>

        {/* Tone Selector: Restrained Segmented Control */}
        <div className="flex items-center gap-1 p-0.5 rounded-lg bg-[#13161B] border border-[#292E36]">
          {(['empathetic', 'concise', 'formal'] as TonePreset[]).map((t) => {
            const isActive = t === currentTone;
            return (
              <button
                key={t}
                onClick={() => onSelectTone(t)}
                className={`px-3 py-1 rounded-md text-xs font-medium capitalize transition-all cursor-pointer ${
                  isActive
                    ? 'bg-[#292E36] text-[#E8EAED] shadow-xs'
                    : 'text-[#9299A5] hover:text-[#E8EAED]'
                }`}
              >
                {t}
              </button>
            );
          })}
        </div>
      </div>

      {/* Subject Line Field */}
      <div className="mb-4">
        <label className="text-[10px] font-mono uppercase tracking-wider text-[#9299A5] block mb-1">
          Subject
        </label>
        <div className="px-3.5 py-2 rounded-lg bg-[#13161B] border border-[#292E36] text-xs font-medium text-[#E8EAED]">
          {draft.subject}
        </div>
      </div>

      {/* Writing Text Area */}
      <div className="flex flex-col gap-1.5 mb-4">
        <div className="flex items-center justify-between text-[10px] font-mono text-[#9299A5]">
          <span>Response Body (Agent Editable)</span>
          <span>{editedBody.length} characters</span>
        </div>
        <textarea
          rows={12}
          value={editedBody}
          onChange={(e) => onChangeBody(e.target.value)}
          className="w-full p-4 rounded-lg bg-[#13161B] border border-[#292E36] text-xs sm:text-sm text-[#E8EAED] leading-relaxed font-sans focus:outline-none focus:border-[#8BA7D9] focus:ring-1 focus:ring-[#8BA7D9]/20 resize-y transition-colors placeholder-[#9299A5]"
          placeholder="Compose customer response..."
        />
      </div>

      {/* Grounded Clause References */}
      {draft.anchored_clause_ids.length > 0 && (
        <div className="mb-5 pb-3 border-b border-[#292E36]/40 flex flex-wrap items-center gap-2 text-[11px] font-mono text-[#9299A5]">
          <span>Anchored clauses:</span>
          {draft.anchored_clause_ids.map((clauseId, i) => (
            <span
              key={i}
              className="px-2 py-0.5 rounded bg-[#13161B] border border-[#292E36] text-[#E8EAED] text-[10px]"
            >
              {clauseId}
            </span>
          ))}
        </div>
      )}

      {/* Professional Actions Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={onReject}
            icon={<RotateCcw className="w-3.5 h-3.5" />}
          >
            Reset draft
          </Button>

          <Button
            variant="secondary"
            size="sm"
            onClick={onEscalate}
            icon={<AlertTriangle className="w-3.5 h-3.5 text-[#D3A365]" />}
          >
            Escalate to Lead
          </Button>
        </div>

        <Button
          variant="primary"
          size="md"
          onClick={onApprove}
          disabled={isSubmitting}
          icon={<Send className="w-3.5 h-3.5" />}
          className="px-5 font-semibold"
        >
          {isSubmitting ? 'Verifying...' : 'Authorize & Sign Off'}
        </Button>
      </div>
    </div>
  );
};
