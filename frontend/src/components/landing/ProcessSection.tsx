import React, { useRef } from 'react';
import { motion, useScroll, useTransform, MotionValue } from 'framer-motion';

interface ProcessStep {
  step: string;
  title: string;
  category: string;
  desc: string;
}

const steps: ProcessStep[] = [
  {
    step: '01',
    title: 'Decompose Complaint',
    category: 'PARSING',
    desc: 'Raw customer messages from email, ticketing, or chat are split into atomic, traceable grievances so no sub-issue is missed.',
  },
  {
    step: '02',
    title: 'Retrieve Exact Clauses',
    category: 'RRF SEARCH',
    desc: 'Dense embeddings and full-text keyword indexing are combined through Reciprocal Rank Fusion (k=60) to pinpoint active clauses.',
  },
  {
    step: '03',
    title: 'Scan Commitments',
    category: 'GUARDRAILS',
    desc: 'Deterministic safety rules scan candidate drafts to catch and flag ungrounded financial promises or prohibited goodwill claims.',
  },
  {
    step: '04',
    title: 'Human Agent Approval',
    category: 'SIGN-OFF',
    desc: 'Support agents inspect evidence citations, adjust tone, edit responses, and formally certify dispatch with an immutable audit trail.',
  },
];

// Desktop Individual Card with Skiper104 Scroll Transforms
const DesktopCardItem: React.FC<{
  item: ProcessStep;
  index: number;
  total: number;
  scrollYProgress: MotionValue<number>;
}> = ({ item, index, total, scrollYProgress }) => {
  const start = index / total;
  const end = (index + 1) / total;

  const yTop = useTransform(scrollYProgress, [start, end], [-35, 0]);
  const yBottom = useTransform(scrollYProgress, [start, end], [35, 0]);
  const scaleDot = useTransform(scrollYProgress, [start, end], [0, 1]);
  const opacity = useTransform(scrollYProgress, [start, end], [0.25, 1]);

  return (
    <div className="editorial-card p-6 sm:p-8 flex flex-col justify-between hover:bg-white/[0.02] transition-colors duration-300 cursor-default min-h-[340px]">
      <div>
        {/* Top: Step Number + Dot + Category */}
        <motion.div
          style={{ y: yTop, opacity }}
          className="flex items-center justify-between text-xs font-mono text-white/40 mb-8"
        >
          <div className="flex items-center gap-2">
            <span
              className="text-2xl text-white/90"
              style={{ fontFamily: "'Instrument Serif', serif" }}
            >
              {item.step}
            </span>
            <motion.span
              style={{ scale: scaleDot }}
              className="w-1.5 h-1.5 rounded-full bg-emerald-400"
            />
          </div>
          <span className="text-[10px] uppercase tracking-wider text-white/50 bg-white/[0.04] px-2 py-0.5 rounded border border-white/[0.06]">
            {item.category}
          </span>
        </motion.div>

        {/* Middle: Title & Description */}
        <motion.div style={{ y: yBottom, opacity }}>
          <h3
            className="text-xl text-white font-normal mb-3"
            style={{ fontFamily: "'Instrument Serif', serif" }}
          >
            {item.title}
          </h3>
          <p className="text-xs text-[#a1a1aa] font-sans font-light leading-relaxed">
            {item.desc}
          </p>
        </motion.div>
      </div>

      {/* Bottom: Phase Status */}
      <motion.div
        style={{ opacity }}
        className="pt-6 mt-6 border-t border-white/[0.05] flex items-center justify-between text-[10px] font-mono text-white/40"
      >
        <span>Phase {index + 1} of 4</span>
        <span className="text-emerald-400/80">Deterministic</span>
      </motion.div>
    </div>
  );
};

export const ProcessSection: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start start', 'end end'],
  });

  return (
    <section id="how-it-works" className="relative bg-transparent">
      {/* ============================================================== */}
      {/* DESKTOP: Skiper104 Scroll Reveal Grid Cards (h-[240vh] + sticky) */}
      {/* ============================================================== */}
      <div className="hidden lg:block relative" ref={containerRef}>
        <div className="h-[240vh] relative">
          <div className="sticky top-20 min-h-[calc(100vh-5rem)] flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
            {/* Header matching provided image */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-8 border-b border-white/[0.08] mb-10">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-widest text-[#a1a1aa] block mb-2">
                  METHODOLOGY
                </span>
                <h2
                  className="text-3xl sm:text-4xl lg:text-5xl text-white tracking-tight leading-tight font-normal"
                  style={{ fontFamily: "'Instrument Serif', serif" }}
                >
                  The verification pipeline.
                </h2>
              </div>
              <p className="text-xs sm:text-sm text-[#a1a1aa] max-w-md font-sans font-normal leading-relaxed">
                Four disciplined stages that transform raw customer frustration into compliant, verifiable resolution without hallucinated risk.
              </p>
            </div>

            {/* Skiper104 Animated Connector Line & Grid Cards */}
            <div className="relative rounded-2xl overflow-hidden border border-white/[0.08] bg-[#0E1322]/80 backdrop-blur-md shadow-2xl shadow-emerald-950/10">
              {/* Animated Progress Connector Line across top */}
              <div className="absolute top-0 left-0 right-0 h-[2px] bg-white/[0.05] overflow-hidden z-10">
                <motion.div
                  style={{ scaleX: scrollYProgress }}
                  className="h-full w-full bg-gradient-to-r from-emerald-400 via-white to-amber-300 origin-left"
                />
              </div>

              {/* 4 Cards Grid with Skiper104 transforms */}
              <div className="grid grid-cols-4 gap-0 divide-x divide-white/[0.08]">
                {steps.map((s, idx) => (
                  <DesktopCardItem
                    key={s.step}
                    item={s}
                    index={idx}
                    total={steps.length}
                    scrollYProgress={scrollYProgress}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ============================================================== */}
      {/* MOBILE / TABLET: Skiper104 Responsive Vertical Timeline        */}
      {/* ============================================================== */}
      <div className="lg:hidden py-20 px-4 sm:px-6 max-w-3xl mx-auto">
        {/* Header */}
        <div className="flex flex-col gap-4 pb-8 border-b border-white/[0.08] mb-10">
          <span className="text-[10px] font-mono uppercase tracking-widest text-[#a1a1aa] block">
            METHODOLOGY
          </span>
          <h2
            className="text-3xl sm:text-4xl text-white tracking-tight leading-tight font-normal"
            style={{ fontFamily: "'Instrument Serif', serif" }}
          >
            The verification pipeline.
          </h2>
          <p className="text-xs sm:text-sm text-[#a1a1aa] font-sans font-normal leading-relaxed">
            Four disciplined stages that transform raw customer frustration into compliant, verifiable resolution without hallucinated risk.
          </p>
        </div>

        {/* Mobile Vertical Cards with Left Progress Accent Line */}
        <div className="relative pl-6 space-y-6">
          <div className="absolute left-1.5 top-2 bottom-2 w-[2px] bg-gradient-to-b from-emerald-400 via-white to-amber-300 opacity-60 rounded-full" />
          {steps.map((s, idx) => (
            <div
              key={s.step}
              className="editorial-card p-6 rounded-2xl border border-white/[0.08] bg-[#0E1322]/85 backdrop-blur-md relative"
            >
              <div className="flex items-center justify-between text-xs font-mono text-white/40 mb-4">
                <div className="flex items-center gap-2">
                  <span
                    className="text-xl text-white/90"
                    style={{ fontFamily: "'Instrument Serif', serif" }}
                  >
                    {s.step}
                  </span>
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                </div>
                <span className="text-[10px] uppercase tracking-wider text-white/50 bg-white/[0.04] px-2 py-0.5 rounded border border-white/[0.06]">
                  {s.category}
                </span>
              </div>
              <h3
                className="text-lg text-white font-normal mb-2"
                style={{ fontFamily: "'Instrument Serif', serif" }}
              >
                {s.title}
              </h3>
              <p className="text-xs text-[#a1a1aa] font-sans font-light leading-relaxed mb-4">
                {s.desc}
              </p>
              <div className="pt-4 border-t border-white/[0.05] flex items-center justify-between text-[10px] font-mono text-white/40">
                <span>Phase {idx + 1} of 4</span>
                <span className="text-emerald-400/80">Deterministic</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
