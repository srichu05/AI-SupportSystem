import React, { useState, useEffect } from 'react';
import { motion, LayoutGroup } from 'framer-motion';
import {
  Split,
  BookOpen,
  ShieldAlert,
  CheckCircle2,
  ArrowUpRight,
  ShieldCheck,
  Zap,
  Lock,
  Sparkles,
} from 'lucide-react';
import { useInView } from '../../hooks/useInView';

interface CapabilityItem {
  id: number;
  step: string;
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  shortDescription: string;
  preview: React.ReactNode;
  deepDive: {
    badge: string;
    headline: string;
    overview: string;
    highlights: {
      title: string;
      desc: string;
      icon: React.ComponentType<{ className?: string }>;
    }[];
    metrics: { label: string; value: string }[];
  };
}

export const CoreCapabilities: React.FC = () => {
  const { ref, isInView } = useInView({ threshold: 0.1 });
  const [hoveredIndex, setHoveredIndex] = useState<number>(0);
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);

  const capabilities: CapabilityItem[] = [
    {
      id: 1,
      step: '01 / DECOMPOSITION',
      icon: Split,
      title: 'Multi-Concern Decomposition',
      shortDescription:
        'Inbound tickets frequently bundle multiple grievances into a single emotional statement. Our decomposition engine separates independent issues—such as delivery delays, transit damage, and courier conduct—so no customer concern is neglected.',
      preview: (
        <div className="p-4 rounded-xl bg-black/45 border border-white/[0.06] text-xs font-mono text-white/70">
          <div className="flex items-center justify-between text-[11px] text-white/40 pb-2 mb-2 border-b border-white/[0.05]">
            <span>Sample Grievance Pipeline</span>
            <span className="text-emerald-400">Atomic Issues Isolated</span>
          </div>
          <div className="space-y-1.5 text-[11px]">
            <div className="flex items-center justify-between">
              <span className="text-white/80">Issue A: Damaged Espresso Machine</span>
              <span className="text-emerald-400/90 text-[10px]">COVERED (Clause 3.2)</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-white/80">Issue B: 3-Day Fulfillment Delay</span>
              <span className="text-amber-400/90 text-[10px]">PARTIALLY COVERED (Clause 2.1)</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-white/80">Issue C: $100 Inconvenience Demand</span>
              <span className="text-rose-400/90 text-[10px]">PROHIBITED (Clause 7.1)</span>
            </div>
          </div>
        </div>
      ),
      deepDive: {
        badge: 'PARSING ENGINE',
        headline: 'Granular Multi-Issue Disentanglement',
        overview:
          'Customer complaints rarely fit into a single bucket. When a ticket claims delayed shipping, damaged cargo, and rude driver behavior, standard LLMs often over-compensate or deliver ambiguous blanket rejections. PolicyPulse runs multi-head semantic isolation, segmenting grievances into discrete atomic items with independent evidence queries.',
        highlights: [
          {
            title: 'Autonomous Concern Isolation',
            desc: 'Separates composite sentences into independent claims, eliminating conflation between logistics and product quality.',
            icon: Split,
          },
          {
            title: 'Targeted Evidence Queries',
            desc: 'Each isolated concern dispatches an independent semantic search query into the handbook index.',
            icon: Zap,
          },
          {
            title: 'Zero Claim Contagion',
            desc: 'An unsupportable demand (e.g. $100 cash voucher) never invalidates a customer’s genuine return or warranty right.',
            icon: ShieldCheck,
          },
        ],
        metrics: [
          { label: 'Claim Isolation Rate', value: '100%' },
          { label: 'Segmentation Latency', value: '<120ms' },
          { label: 'Schema Enforcement', value: 'Strict JSON' },
        ],
      },
    },
    {
      id: 2,
      step: '02 / EVIDENCE',
      icon: BookOpen,
      title: 'Clause-Level Policy Grounding',
      shortDescription:
        'Combines dense semantic vectors with full-text keyword indexing through Reciprocal Rank Fusion (k=60). Every drafted sentence is anchored directly to active handbook clauses and section numbers.',
      preview: (
        <div className="p-4 rounded-xl bg-black/45 border border-white/[0.06] text-xs font-mono text-white/70">
          <div className="text-[11px] text-white/40 pb-2 mb-2 border-b border-white/[0.05]">
            <span>CITATION ANCHOR:</span>
          </div>
          <div className="text-[11px] font-semibold text-amber-300 mb-1">
            Clause 3.2 (Transit Damage) • Page 4
          </div>
          <div className="text-[10px] text-white/50">
            Enterprise Return & Refund Policy v2.4
          </div>
        </div>
      ),
      deepDive: {
        badge: 'RRF HYBRID SEARCH',
        headline: 'Dual-Retrieval Vector & Keyword Fusion',
        overview:
          'Pure vector similarity often misses precise terms like SKU numbers or legal definitions, while keyword searches fail to comprehend customer sentiment. Our RRF pipeline merges dense embeddings with BM25 indexing at k=60 rank reciprocal weighting, guaranteeing exact clause citations.',
        highlights: [
          {
            title: 'Reciprocal Rank Fusion (k=60)',
            desc: 'Combines dense semantic similarity with BM25 lexical keyword matching to surface exact clauses.',
            icon: BookOpen,
          },
          {
            title: 'Hierarchical Chunking',
            desc: 'Preserves policy headers, sub-clauses, and appendix exceptions in retrieved context windows.',
            icon: CheckCircle2,
          },
          {
            title: 'Deterministic Citations',
            desc: 'Every sentence references handbook clause IDs and page numbers for compliance auditability.',
            icon: ShieldCheck,
          },
        ],
        metrics: [
          { label: 'Top-3 Recall', value: '99.4%' },
          { label: 'Ranking Formula', value: 'RRF (k=60)' },
          { label: 'Citation Fidelity', value: '100% Verifiable' },
        ],
      },
    },
    {
      id: 3,
      step: '03 / GUARDRAIL',
      icon: ShieldAlert,
      title: 'Unsupported-Commitment Blocker',
      shortDescription:
        'Proactively intercepts unauthorized promises, cash compensation, or warranty waivers. Any proposed remedy that lacks supporting policy authorization is halted before dispatch.',
      preview: (
        <div className="p-4 rounded-xl bg-black/45 border border-white/[0.06] text-xs font-mono text-white/70">
          <div className="flex items-center justify-between text-[11px] text-rose-400 font-bold pb-2 mb-2 border-b border-white/[0.05]">
            <span>VERDICT: FLAGGED</span>
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
          </div>
          <p className="text-[11px] text-white/70 leading-relaxed">
            Unauthorized goodwill demand blocked by Clause 7.1 limits.
          </p>
        </div>
      ),
      deepDive: {
        badge: 'SAFETY ENFORCEMENT',
        headline: 'Deterministic Financial & Legal Safety Checks',
        overview:
          'Hallucinated commitments are the number-one liability of generative customer service models. PolicyPulse implements deterministic guardrails that parse all monetary amounts, credit vows, and contractual promises against strict policy ceilings before any draft reaches an agent.',
        highlights: [
          {
            title: 'Financial Ceiling Interception',
            desc: 'Detects unauthorized cash gestures, replacement commitments, or expedited shipping promises.',
            icon: ShieldAlert,
          },
          {
            title: 'Policy Exception Verification',
            desc: 'Cross-checks discretionary goodwill against customer tier and lifetime transaction history.',
            icon: Lock,
          },
          {
            title: 'Automated Red-Flag Escalation',
            desc: 'Directs ungrounded drafts to senior tier-2 risk officers with flagged rationale.',
            icon: Zap,
          },
        ],
        metrics: [
          { label: 'Commitment Leakage', value: '0.00%' },
          { label: 'Guardrail Enforcement', value: 'Deterministic' },
          { label: 'Check Overhead', value: '<45ms' },
        ],
      },
    },
    {
      id: 4,
      step: '04 / HUMAN SIGN-OFF',
      icon: CheckCircle2,
      title: 'Human-in-the-Loop Agent Studio',
      shortDescription:
        'No communication is ever transmitted automatically to a customer. Support agents inspect retrieved evidence, calibrate tone (Empathetic, Concise, Formal), edit responses inline, and provide certified authorization with an auditable compliance trail.',
      preview: (
        <div className="p-4 rounded-xl bg-black/45 border border-white/[0.06] text-xs font-mono text-white/70">
          <div className="flex items-center justify-between text-[11px] text-white/40 pb-2 mb-2 border-b border-white/[0.05]">
            <span>Mandatory Human Certification</span>
            <span className="text-emerald-400 font-medium">100% Agent Verified</span>
          </div>
          <div className="flex items-center gap-2 text-[11px] text-white/80">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            <span>Cryptographic audit sign-off attached to dispatch ticket</span>
          </div>
        </div>
      ),
      deepDive: {
        badge: 'HUMAN SUPERVISION',
        headline: 'Certified Agent Review & Tone Calibration',
        overview:
          'AI should augment customer support professionals, not replace accountable human judgment. PolicyPulse delivers an interactive review studio where human agents inspect side-by-side evidence, calibrate customer-facing tone, make precision edits, and apply certified sign-off.',
        highlights: [
          {
            title: 'Triple-Tone Calibration',
            desc: 'Adjust response tonality between Empathetic, Concise, and Formal while preserving grounded policy fidelity.',
            icon: Sparkles,
          },
          {
            title: 'Side-by-Side Evidence Inspection',
            desc: 'Human reviewers see the customer complaint, isolated claims, and cited policy clauses simultaneously.',
            icon: CheckCircle2,
          },
          {
            title: 'Auditable Sign-Off Trail',
            desc: 'Cryptographic records document agent identity, timestamp, reviewed clauses, and delivery payload.',
            icon: Lock,
          },
        ],
        metrics: [
          { label: 'Human Verification', value: 'Mandatory' },
          { label: 'Compliance Audit', value: '100% Recorded' },
          { label: 'Review Speedup', value: '4.8x Faster' },
        ],
      },
    },
  ];

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setSelectedIndex(null);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

const LayoutGroupComponent = LayoutGroup as React.ComponentType<{ id?: string; children?: React.ReactNode }>;

  return (
    <section
      id="capabilities"
      ref={ref}
      className="py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto bg-transparent relative"
    >
      <LayoutGroupComponent id="skiper80-showcase">
        <div
          className={`transition-all duration-700 ${
            isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
          }`}
        >
          {selectedIndex === null ? (
            /* Skiper80 Initial Two-Column State */
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-14 items-center">
              {/* Left Column: Draggable preview card */}
              <div className="lg:col-span-6 flex justify-center lg:justify-start">
                <motion.div
                  drag
                  dragConstraints={{ left: -30, right: 30, top: -30, bottom: 30 }}
                  whileDrag={{ scale: 1.02, cursor: 'grabbing' }}
                  layoutId="active-img"
                  style={{ borderRadius: '25px' }}
                  onClick={() => setSelectedIndex(hoveredIndex)}
                  className="w-full max-w-lg cursor-grab active:cursor-grabbing p-7 sm:p-9 rounded-[25px] bg-[#0E1322] border border-white/10 hover:border-white/20 transition-colors shadow-2xl select-none"
                >
                  {/* Top card metadata */}
                  <div className="flex items-center justify-between text-xs text-white/40 font-mono mb-5">
                    <span className="tracking-wider uppercase text-[11px]">
                      {capabilities[hoveredIndex].step}
                    </span>
                    <div className="flex items-center gap-2">
                      {React.createElement(capabilities[hoveredIndex].icon, {
                        className: 'w-4 h-4 text-white/60',
                      })}
                      <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-white/5 border border-white/10 text-white/50">
                        Drag or Click to Expand
                      </span>
                    </div>
                  </div>

                  {/* Title & short description */}
                  <h3 className="text-2xl sm:text-3xl text-white font-normal mb-3 tracking-tight">
                    {capabilities[hoveredIndex].title}
                  </h3>
                  <p className="text-xs sm:text-sm text-[#a1a1aa] font-light leading-relaxed mb-6">
                    {capabilities[hoveredIndex].shortDescription}
                  </p>

                  {/* Preview simulation box */}
                  <div className="rounded-xl overflow-hidden border border-white/[0.08] bg-black/40">
                    {capabilities[hoveredIndex].preview}
                  </div>

                  {/* Bottom hint */}
                  <div className="mt-5 pt-4 border-t border-white/[0.06] flex items-center justify-between text-[11px] font-mono text-white/40">
                    <span>Click anywhere to view full architecture</span>
                    <span className="text-white/70">Expand →</span>
                  </div>
                </motion.div>
              </div>

              {/* Right Column: Skiper80 Title List */}
              <div className="lg:col-span-6 flex flex-col justify-center">
                <ul className="flex flex-col gap-3">
                  {/* Header: CORE PRINCIPLES ─────── */}
                  <li className="flex w-full items-center gap-3 text-sm uppercase opacity-50 font-mono tracking-widest text-[#a1a1aa] mb-4">
                    <span>CORE PRINCIPLES</span>
                    <span className="bg-white/20 h-px flex-1 max-w-xs" />
                  </li>

                  {/* Interactive items with trailing dot indicator */}
                  {capabilities.map((item, index) => (
                    <motion.li
                      key={item.id}
                      layoutId={`text-header-${index}`}
                      style={{ opacity: hoveredIndex === index ? 1 : 0.5 }}
                      className="relative flex w-fit cursor-pointer items-center text-3xl sm:text-4xl lg:text-[42px] tracking-tight font-normal transition-opacity duration-200 select-none py-1"
                      onMouseEnter={() => setHoveredIndex(index)}
                      onClick={() => setSelectedIndex(index)}
                    >
                      <span className="text-white hover:text-white transition-colors">
                        {item.title}
                      </span>
                      {hoveredIndex === index && (
                        <motion.div
                          initial={{ x: 10, width: '15px', height: '0px' }}
                          animate={{ x: 10, width: '4px', height: '4px' }}
                          transition={{ duration: 0.2 }}
                          className="bg-white absolute left-full rounded-full"
                        />
                      )}
                    </motion.li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            /* Skiper80 Expanded Detail State */
            <div
              onClick={(e) => {
                if (e.target === e.currentTarget) {
                  setSelectedIndex(null);
                }
              }}
              className="w-full py-8 cursor-default"
            >
              <div className="mx-auto flex flex-col items-center justify-center gap-10 max-w-2xl px-4">
                <div className="w-full space-y-8">
                  {/* Title morphing with layoutId */}
                  <div className="relative min-h-[50px] sm:min-h-[70px]">
                    <motion.h1
                      className="text-3xl sm:text-5xl lg:text-6xl font-medium text-white tracking-tight leading-tight"
                      layoutId={`text-header-${selectedIndex}`}
                    >
                      {capabilities[selectedIndex].title}
                    </motion.h1>
                  </div>

                  {/* Card morphing with layoutId="active-img" */}
                  <motion.div
                    layoutId="active-img"
                    style={{ borderRadius: '25px' }}
                    className="w-full bg-[#0E1322] border border-white/15 p-6 sm:p-8 rounded-[25px] shadow-2xl"
                  >
                    <div className="flex items-center justify-between text-xs text-white/40 font-mono mb-4">
                      <span className="tracking-wider uppercase">
                        {capabilities[selectedIndex].step}
                      </span>
                      <span className="text-emerald-400 font-medium">
                        {capabilities[selectedIndex].deepDive.badge}
                      </span>
                    </div>
                    <p className="text-sm text-[#a1a1aa] font-light leading-relaxed mb-6">
                      {capabilities[selectedIndex].shortDescription}
                    </p>
                    <div className="rounded-xl bg-black/60 border border-white/[0.08] p-4">
                      {capabilities[selectedIndex].preview}
                    </div>
                  </motion.div>
                </div>

                {/* Staggered Content with Animated Rule */}
                <motion.div
                  initial="hidden"
                  animate="visible"
                  variants={{
                    hidden: { opacity: 0 },
                    visible: {
                      opacity: 1,
                      transition: { staggerChildren: 0.1, delayChildren: 0.25 },
                    },
                  }}
                  className="w-full"
                >
                  <motion.div
                    variants={{ hidden: { opacity: 0, y: 15 }, visible: { opacity: 1, y: 0 } }}
                    className="mx-auto w-full space-y-6"
                    transition={{ type: 'spring', stiffness: 50, damping: 10 }}
                  >
                    {/* Section title with animated underline like Skiper80 */}
                    <section className="w-full">
                      <div className="flex items-center gap-3">
                        <h2 className="text-white text-xl sm:text-2xl font-semibold tracking-tight">
                          {capabilities[selectedIndex].deepDive.headline}
                        </h2>
                        <motion.div
                          initial={{ scaleX: 0 }}
                          animate={{ scaleX: 1 }}
                          transition={{ delay: 0.35, duration: 0.5 }}
                          className="bg-white/20 h-0.5 flex-1 origin-left rounded-full"
                        />
                      </div>
                    </section>

                    {/* Overview description */}
                    <div className="text-white/60 space-y-3 text-sm sm:text-base leading-relaxed">
                      <p>{capabilities[selectedIndex].deepDive.overview}</p>
                    </div>

                    {/* Architectural highlights */}
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
                      {capabilities[selectedIndex].deepDive.highlights.map((h, idx) => (
                        <div
                          key={idx}
                          className="p-3.5 rounded-xl bg-white/[0.03] border border-white/[0.06]"
                        >
                          <div className="text-xs font-semibold text-white/90 mb-1">
                            {h.title}
                          </div>
                          <div className="text-[11px] text-white/50 leading-normal">
                            {h.desc}
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Performance metrics */}
                    <div className="grid grid-cols-3 gap-3 pt-2">
                      {capabilities[selectedIndex].deepDive.metrics.map((m, idx) => (
                        <div
                          key={idx}
                          className="p-3 rounded-lg bg-black/40 border border-white/[0.04] text-center"
                        >
                          <div className="text-[10px] font-mono uppercase text-white/40">
                            {m.label}
                          </div>
                          <div className="text-base sm:text-lg font-semibold text-white mt-0.5">
                            {m.value}
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Action buttons */}
                    <div className="mt-8 flex items-center gap-3 pt-2">
                      <button
                        type="button"
                        onClick={() => setSelectedIndex(null)}
                        className="bg-white text-black flex h-9 items-center gap-2 rounded-xl px-4 text-sm font-medium hover:bg-white/90 transition-colors cursor-pointer"
                      >
                        ← Back to Principles
                      </button>
                      <a
                        href="#interactive-demo"
                        className="bg-white/10 hover:bg-white/15 text-white flex h-9 items-center gap-2 rounded-xl px-4 text-sm font-medium border border-white/10 transition-colors"
                      >
                        Live Preview <ArrowUpRight className="size-3.5" />
                      </a>
                    </div>
                  </motion.div>
                </motion.div>
              </div>
            </div>
          )}
        </div>
      </LayoutGroupComponent>
    </section>
  );
};
