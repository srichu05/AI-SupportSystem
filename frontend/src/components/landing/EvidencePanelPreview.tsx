import React from 'react';
import { Badge } from '../ui/Badge';
import { IssueCoverageStatus } from '../../types';
import { useInView } from '../../hooks/useInView';

export const EvidencePanelPreview: React.FC = () => {
  const { ref, isInView } = useInView({ threshold: 0.1 });
  const [hovered, setHovered] = React.useState<number | null>(null);

  const coverageStates: { status: IssueCoverageStatus; meaning: string; example: string }[] = [
    {
      status: 'covered',
      meaning: 'Active policy explicitly authorizes the exact resolution requested.',
      example: 'Damaged merchandise reported within 14-day receipt window (Clause 3.2).',
    },
    {
      status: 'partially_covered',
      meaning: 'Policy applies to category, but operational conditions or caps constrain relief.',
      example: 'Carrier delay > 48h credits shipping fee, but does not refund item price.',
    },
    {
      status: 'prohibited',
      meaning: 'Active policy explicitly denies or forbids the requested concession.',
      example: 'Frontline agent granting >$25 gift card or external cash credit (Clause 7.1).',
    },
    {
      status: 'needs_human_review',
      meaning: 'High ambiguity, safety hazard, or legal threat requires supervisory triage.',
      example: 'Thermal appliance defect with report of smoke from rear capacitor (Clause 5.1).',
    },
    {
      status: 'conflict',
      meaning: 'Multiple active enterprise documents yield contradictory directives.',
      example: 'Standard handbook allows 30-day return, but promotional invoice states final sale.',
    },
    {
      status: 'uncovered',
      meaning: 'Active enterprise handbooks contain no documentation covering this scenario.',
      example: 'Customer asks for delivery driver to be reassigned to alternate residential route.',
    },
  ];

  return (
    <section id="architecture" ref={ref} className="py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto bg-transparent">
      {/* Editorial Section Header */}
      <div
        className={`flex flex-col md:flex-row md:items-end justify-between gap-6 pb-8 border-b border-white/[0.08] mb-12 transition-all duration-700 ${
          isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'
        }`}
      >
        <div>
          <span className="text-[10px] font-mono uppercase tracking-widest text-[#a1a1aa] block mb-2">
            AUDITABLE TAXONOMY
          </span>
          <h2
            className="text-3xl sm:text-4xl lg:text-5xl text-white tracking-tight leading-tight font-normal"
            style={{ fontFamily: "'Instrument Serif', serif" }}
          >
            Six deterministic coverage states.
          </h2>
        </div>
        <p className="text-xs sm:text-sm text-[#a1a1aa] max-w-md font-sans font-normal leading-relaxed">
          Missing evidence is never equated with a prohibited request, and similarity scores alone do not establish eligibility. Every identified concern receives an explicit, verifiable state.
        </p>
      </div>

      {/* Focus-Enhanced Editorial Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {coverageStates.map((item, idx) => {
          const isHovered = hovered === idx;
          const isOtherHovered = hovered !== null && hovered !== idx;

          return (
            <div
              key={item.status}
              onMouseEnter={() => setHovered(idx)}
              onMouseLeave={() => setHovered(null)}
              className={`editorial-card p-6 rounded-2xl bg-[#0E1322]/80 backdrop-blur-md border border-white/[0.08] flex flex-col justify-between transition-all duration-300 ease-out cursor-default ${
                isOtherHovered
                  ? 'blur-[2px] scale-[0.98] opacity-50'
                  : isHovered
                  ? 'border-white/25 scale-[1.01] bg-[#12182c]/95 shadow-2xl shadow-purple-500/5'
                  : 'hover:border-white/20'
              } ${isInView ? 'translate-y-0' : 'opacity-0 translate-y-8'}`}
              style={{ transitionDelay: hovered === null ? `${idx * 80}ms` : '0ms' }}
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] sm:text-[11px] font-mono tracking-wider uppercase font-medium bg-white/[0.04] border border-white/10 text-white/90">
                    <span className="w-1.5 h-1.5 rounded-full bg-white/40" />
                    {item.status.replace(/_/g, ' ')}
                  </span>
                  <span className="text-[10px] font-mono text-white/35 uppercase tracking-wider">
                    Taxonomy State
                  </span>
                </div>
                <p className="text-xs sm:text-[13px] text-white/85 font-normal leading-relaxed mb-4">
                  {item.meaning}
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-black/40 border border-white/[0.05] text-[11px] font-mono leading-snug">
                <span className="text-white/30 block text-[10px] tracking-wider mb-1">
                  BENCHMARK SCENARIO:
                </span>
                <span className="text-white/70">{item.example}</span>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};
