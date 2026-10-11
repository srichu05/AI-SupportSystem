import React, { useEffect, useRef, useState } from 'react';
import { ArrowRight } from 'lucide-react';
import { gsap } from 'gsap';

interface FooterProps {
  onLaunchStudio: () => void;
}

interface CrowdCanvasProps {
  src: string;
  rows?: number;
  cols?: number;
  className?: string;
}

interface Peep {
  image: HTMLImageElement;
  rect: number[];
  width: number;
  height: number;
  x: number;
  y: number;
  anchorY: number;
  scaleX: number;
  walk: gsap.core.Timeline | null;
  render: (ctx: CanvasRenderingContext2D) => void;
}

export const CrowdCanvas: React.FC<CrowdCanvasProps> = ({
  src,
  rows = 15,
  cols = 7,
  className = '',
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Respect reduced-motion preferences
    const prefersReducedMotion =
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    let isCleanedUp = false;
    let tickerAdded = false;

    // UTILS
    const randomRange = (min: number, max: number) => min + Math.random() * (max - min);
    const randomIndex = (array: any[]) => Math.floor(randomRange(0, array.length));
    const removeFromArray = (array: any[], i: number) => array.splice(i, 1)[0];
    const removeItemFromArray = (array: any[], item: any) => {
      const idx = array.indexOf(item);
      if (idx !== -1) removeFromArray(array, idx);
    };
    const removeRandomFromArray = (array: any[]) => removeFromArray(array, randomIndex(array));

    // STAGE & PEEPS STATE
    const stage = { width: 0, height: 0 };
    const allPeeps: Peep[] = [];
    const availablePeeps: Peep[] = [];
    const crowd: Peep[] = [];

    // TWEEN FACTORIES
    const resetPeep = ({ peep }: { peep: Peep }) => {
      const direction = Math.random() > 0.5 ? 1 : -1;
      // Staggered Y positioning across the bottom walking plane
      const offsetY = 30 - 150 * gsap.parseEase('power2.in')(Math.random());
      const startY = stage.height - peep.height + offsetY;
      let startX: number;
      let endX: number;

      if (direction === 1) {
        startX = -peep.width - 20;
        endX = stage.width + peep.width + 20;
        peep.scaleX = 1;
      } else {
        startX = stage.width + peep.width + 20;
        endX = -peep.width - 20;
        peep.scaleX = -1;
      }

      peep.x = startX;
      peep.y = startY;
      peep.anchorY = startY;

      return { startX, startY, endX };
    };

    const normalWalk = ({ peep, props }: { peep: Peep; props: any }) => {
      const { startY, endX } = props;
      const xDuration = randomRange(10, 16);
      const yDuration = randomRange(0.24, 0.32);

      const tl = gsap.timeline();
      tl.timeScale(randomRange(0.7, 1.3));
      tl.to(
        peep,
        {
          duration: xDuration,
          x: endX,
          ease: 'none',
        },
        0
      );
      tl.to(
        peep,
        {
          duration: yDuration,
          repeat: Math.floor(xDuration / yDuration),
          yoyo: true,
          y: startY - 8,
          ease: 'power1.inOut',
        },
        0
      );

      return tl;
    };

    const createPeep = ({
      image,
      rect,
    }: {
      image: HTMLImageElement;
      rect: number[];
    }): Peep => {
      // Natural character scaling for elegant, proportional crowd height
      const scale = 0.58;
      const width = rect[2] * scale;
      const height = rect[3] * scale;

      const peep: Peep = {
        image,
        rect,
        width,
        height,
        x: 0,
        y: 0,
        anchorY: 0,
        scaleX: 1,
        walk: null,
        render: (c: CanvasRenderingContext2D) => {
          c.save();
          c.translate(peep.x, peep.y);
          c.scale(peep.scaleX, 1);
          c.drawImage(
            peep.image,
            peep.rect[0],
            peep.rect[1],
            peep.rect[2],
            peep.rect[3],
            0,
            0,
            peep.width,
            peep.height
          );
          c.restore();
        },
      };

      return peep;
    };

    const addPeepToCrowd = () => {
      if (!availablePeeps.length) return null;
      const peep = removeRandomFromArray(availablePeeps);
      const props = resetPeep({ peep });

      if (prefersReducedMotion) {
        // Static positioning if reduced motion is requested
        peep.x = randomRange(20, stage.width - peep.width - 20);
        crowd.push(peep);
        crowd.sort((a, b) => a.anchorY - b.anchorY);
        return peep;
      }

      const walk = normalWalk({ peep, props }).eventCallback('onComplete', () => {
        if (isCleanedUp) return;
        removeItemFromArray(crowd, peep);
        availablePeeps.push(peep);
        addPeepToCrowd();
      });

      peep.walk = walk;
      crowd.push(peep);
      crowd.sort((a, b) => a.anchorY - b.anchorY);

      return peep;
    };

    const initCrowd = () => {
      // Responsive crowd density: ~24 on mobile up to ~55 on large displays
      const targetCrowdSize = Math.min(
        allPeeps.length,
        Math.max(22, Math.floor(stage.width / 26))
      );

      while (crowd.length < targetCrowdSize && availablePeeps.length) {
        const peep = addPeepToCrowd();
        if (peep && peep.walk) {
          peep.walk.progress(Math.random());
        }
      }
    };

    const render = () => {
      if (!canvas || isCleanedUp) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.save();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      ctx.scale(dpr, dpr);

      for (let i = 0; i < crowd.length; i++) {
        crowd[i].render(ctx);
      }

      ctx.restore();
    };

    const resize = () => {
      if (!canvas || isCleanedUp) return;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      stage.width = canvas.clientWidth;
      stage.height = canvas.clientHeight;
      canvas.width = stage.width * dpr;
      canvas.height = stage.height * dpr;

      // Clean active timelines
      crowd.forEach((peep) => {
        if (peep.walk) peep.walk.kill();
      });

      crowd.length = 0;
      availablePeeps.length = 0;
      availablePeeps.push(...allPeeps);

      initCrowd();
      render();
    };

    const img = new Image();
    img.crossOrigin = 'anonymous';

    img.onload = () => {
      if (isCleanedUp) return;
      const total = rows * cols;
      const rectWidth = img.naturalWidth / rows;
      const rectHeight = img.naturalHeight / cols;

      for (let i = 0; i < total; i++) {
        allPeeps.push(
          createPeep({
            image: img,
            rect: [
              (i % rows) * rectWidth,
              Math.floor(i / rows) * rectHeight,
              rectWidth,
              rectHeight,
            ],
          })
        );
      }

      resize();

      if (!prefersReducedMotion) {
        gsap.ticker.add(render);
        tickerAdded = true;
      }
    };

    img.onerror = () => {
      setHasError(true);
    };

    img.src = src;

    const handleResize = () => resize();
    window.addEventListener('resize', handleResize);

    return () => {
      isCleanedUp = true;
      window.removeEventListener('resize', handleResize);
      if (tickerAdded) {
        gsap.ticker.remove(render);
      }
      crowd.forEach((peep) => {
        if (peep.walk) peep.walk.kill();
      });
    };
  }, [src, rows, cols]);

  if (hasError) {
    return null;
  }

  return (
    <canvas
      ref={canvasRef}
      className={`w-full block ${className}`}
      aria-hidden="true"
    />
  );
};

export const Footer: React.FC<FooterProps> = ({ onLaunchStudio }) => {
  return (
    <footer className="relative w-full bg-[#0D0F12] overflow-hidden pt-24 sm:pt-32 pb-8 border-t border-[#292E36]/40">
      {/* Background Subtle Ambience Glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[720px] h-[340px] bg-[#8BA7D9]/5 blur-[120px] pointer-events-none" />

      {/* Main Section Content Stack */}
      <div className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center flex flex-col items-center">
        {/* Eyebrow */}
        <span className="text-[11px] font-mono uppercase tracking-widest text-[#9299A5] block mb-4">
          TENSOR TITANS · PS-40
        </span>

        {/* Main Heading */}
        <h2
          className="text-3xl sm:text-5xl lg:text-6xl text-[#E8EAED] tracking-tight mb-5 max-w-3xl font-normal leading-[1.12]"
          style={{ fontFamily: "'Instrument Serif', serif" }}
        >
          Every complaint deserves a considered response.
        </h2>

        {/* Supporting Text */}
        <p className="text-xs sm:text-sm text-[#9299A5] max-w-lg mb-8 font-sans font-light leading-relaxed">
          Turn customer complaints into policy-grounded response drafts, backed by relevant evidence and human review.
        </p>

        {/* Primary CTA */}
        <div className="flex flex-col items-center gap-3 mb-14 sm:mb-20">
          <button
            onClick={onLaunchStudio}
            className="inline-flex items-center gap-2 px-6 py-3 rounded-lg text-xs sm:text-sm font-semibold bg-[#8BA7D9] text-[#0D0F12] hover:bg-[#9BB7E9] active:scale-[0.98] transition-all duration-150 cursor-pointer shadow-lg shadow-[#8BA7D9]/15"
          >
            <span>Open Agent Workspace</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>

          {/* Secondary reassurance text */}
          <span className="text-[11px] font-mono text-[#9299A5]/80">
            Evidence-backed. Human-reviewed. Never sent automatically.
          </span>
        </div>
      </div>

      {/* Full-Width Animated Crowd Walking Plane */}
      <div className="relative w-full overflow-hidden h-[260px] sm:h-[320px] lg:h-[360px] pointer-events-none select-none">
        {/* Top Fade Gradient for seamless visual integration */}
        <div className="absolute top-0 left-0 right-0 h-16 bg-gradient-to-b from-[#0D0F12] to-transparent z-10" />

        {/* Live Canvas Crowd */}
        <CrowdCanvas
          src="/images/peeps/all-peeps-dark.png"
          rows={15}
          cols={7}
          className="w-full h-full"
        />

        {/* Bottom Ground Line Accent */}
        <div className="absolute bottom-0 left-0 right-0 h-px bg-[#292E36]/60 z-10" />
      </div>

      {/* Minimal Integrated Footer Attribution Bar */}
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-[11px] font-mono text-[#9299A5]">
        <div className="flex items-center gap-2">
          <span className="text-[#E8EAED] font-medium">PolicyPulse AI</span>
          <span>•</span>
          <span>Human-in-the-Loop Case Management</span>
        </div>

        <div className="flex items-center gap-4 text-[#9299A5]/70">
          <span>TENSOR TITANS · PS-40</span>
          <span>•</span>
          <span>© 2026 PolicyPulse</span>
        </div>
      </div>
    </footer>
  );
};
