import React from 'react';
import { Layers } from 'lucide-react';
import { DecomposedConcern } from '../../types';
import { Badge } from '../ui/Badge';

interface DecomposedConcernsProps {
  concerns: DecomposedConcern[];
  selectedIndex: number;
  onSelectConcern: (index: number) => void;
}

export const DecomposedConcerns: React.FC<DecomposedConcernsProps> = ({
  concerns,
  selectedIndex,
  onSelectConcern,
}) => {
  return (
    <div className="bg-[#181C22] border border-[#292E36] rounded-xl p-4 mb-5 shadow-xs">
      <div className="flex items-center justify-between pb-3 border-b border-[#292E36]/60 mb-3">
        <div className="flex items-center gap-2">
          <Layers className="w-3.5 h-3.5 text-[#8BA7D9]" />
          <h3 className="text-xs font-semibold text-[#E8EAED]">
            Identified Issues ({concerns.length})
          </h3>
        </div>
        <span className="text-[11px] text-[#9299A5] font-mono">
          Select an issue to inspect evidence
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
        {concerns.map((concern, idx) => {
          const isSelected = idx === selectedIndex;
          return (
            <div
              key={concern.concern_id}
              onClick={() => onSelectConcern(idx)}
              className={`p-3 rounded-lg border transition-all cursor-pointer text-left ${
                isSelected
                  ? 'bg-[#13161B] border-[#8BA7D9] shadow-xs'
                  : 'bg-[#13161B]/50 border-[#292E36] hover:bg-[#13161B] hover:border-[#292E36]/80'
              }`}
            >
              <div className="flex items-center justify-between gap-2 mb-1.5">
                <div className="flex items-center gap-1.5 min-w-0">
                  <span className="w-4 h-4 rounded bg-[#181C22] border border-[#292E36] flex items-center justify-center text-[10px] font-mono text-[#9299A5]">
                    {idx + 1}
                  </span>
                  <span className="text-xs font-medium text-[#E8EAED] truncate">
                    {concern.category}
                  </span>
                </div>
                <Badge status={concern.status} size="sm" />
              </div>

              <p className="text-[11px] text-[#9299A5] line-clamp-2 leading-relaxed">
                {concern.summary}
              </p>

              <div className="mt-2 pt-2 border-t border-[#292E36]/40 flex items-center justify-between text-[10px] font-mono text-[#9299A5]">
                <span>{concern.citations.length} citation(s)</span>
                <span className={isSelected ? 'text-[#8BA7D9]' : 'text-[#9299A5]'}>
                  {isSelected ? 'Viewing' : 'Inspect →'}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
