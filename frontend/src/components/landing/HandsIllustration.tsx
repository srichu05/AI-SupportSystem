import React from 'react';

export const HandsIllustration: React.FC = () => {
  return (
    <div className="relative w-full max-w-4xl mx-auto my-8 sm:my-12 px-4 select-none pointer-events-none">
      <svg
        viewBox="0 0 900 360"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-auto overflow-visible"
      >
        <defs>
          {/* Halftone dot patterns */}
          <pattern id="stipple-dense" width="6" height="6" patternUnits="userSpaceOnUse">
            <circle cx="3" cy="3" r="1.1" fill="#1A1A1A" fillOpacity="0.85" />
          </pattern>
          <pattern id="stipple-medium" width="8" height="8" patternUnits="userSpaceOnUse">
            <circle cx="4" cy="4" r="1.2" fill="#222222" fillOpacity="0.65" />
          </pattern>
          <pattern id="stipple-light" width="12" height="12" patternUnits="userSpaceOnUse">
            <circle cx="6" cy="6" r="1.2" fill="#333333" fillOpacity="0.45" />
          </pattern>
          <pattern id="stipple-sparse" width="16" height="16" patternUnits="userSpaceOnUse">
            <circle cx="8" cy="8" r="1.3" fill="#444444" fillOpacity="0.3" />
          </pattern>

          {/* Gradients for stipple fade */}
          <linearGradient id="fade-left" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#000" stopOpacity="0.1" />
            <stop offset="60%" stopColor="#000" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#000" stopOpacity="1" />
          </linearGradient>

          <linearGradient id="fade-right" x1="100%" y1="0%" x2="0%" y2="0%">
            <stop offset="0%" stopColor="#000" stopOpacity="0.1" />
            <stop offset="60%" stopColor="#000" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#000" stopOpacity="1" />
          </linearGradient>

          {/* Dynamic Shimmer Flow Gradient */}
          <linearGradient id="shimmer-flow" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#111111" stopOpacity="0.0">
              <animate attributeName="offset" values="-0.5; 1.5" dur="4.5s" repeatCount="indefinite" />
            </stop>
            <stop offset="50%" stopColor="#444444" stopOpacity="0.35">
              <animate attributeName="offset" values="0.0; 2.0" dur="4.5s" repeatCount="indefinite" />
            </stop>
            <stop offset="100%" stopColor="#111111" stopOpacity="0.0">
              <animate attributeName="offset" values="0.5; 2.5" dur="4.5s" repeatCount="indefinite" />
            </stop>
          </linearGradient>

          <mask id="mask-hand-left">
            <path
              d="M40 320 C90 280, 160 230, 240 180 C270 160, 310 140, 360 135 C385 132, 410 145, 418 160 C425 175, 400 195, 365 205 C335 212, 290 230, 240 260 C190 290, 120 330, 60 350 Z"
              fill="url(#fade-left)"
            />
          </mask>

          <mask id="mask-hand-right">
            <path
              d="M860 60 C810 100, 740 150, 660 195 C630 215, 590 235, 540 240 C515 242, 490 228, 482 212 C475 197, 500 177, 535 167 C565 160, 610 142, 660 112 C710 82, 780 45, 840 25 Z"
              fill="url(#fade-right)"
            />
          </mask>
        </defs>

        {/* Ambient subtle connection field dots between fingertips with pulsing aura */}
        <g opacity="0.55" className="animate-pulse-slow">
          <circle cx="435" cy="182" r="1.5" fill="#111" />
          <circle cx="448" cy="180" r="1.8" fill="#111" />
          <circle cx="462" cy="183" r="1.5" fill="#111" />
          <circle cx="475" cy="186" r="1.2" fill="#111" />
          <circle cx="450" cy="168" r="1.2" fill="#111" />
          <circle cx="458" cy="195" r="1.2" fill="#111" />
          <circle cx="442" cy="192" r="1.0" fill="#111" />
          <circle cx="466" cy="174" r="1.0" fill="#111" />
        </g>

        {/* Animated Particles travelling between human & AI fingertips */}
        <g id="traveling-particles">
          {/* Particle 1: Left to right (Human judgment -> AI reasoning) */}
          <circle r="1.8" fill="#111111">
            <animateMotion path="M 422 142 Q 450 160 478 218" dur="3s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="0; 0.9; 0.9; 0" dur="3s" repeatCount="indefinite" />
          </circle>

          {/* Particle 2: Right to left (AI policy evidence -> Human agent) */}
          <circle r="1.6" fill="#1A1A1A">
            <animateMotion path="M 478 218 Q 455 195 425 158" dur="3.4s" begin="0.8s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="0; 0.85; 0.85; 0" dur="3.4s" begin="0.8s" repeatCount="indefinite" />
          </circle>

          {/* Particle 3: Upper arc */}
          <circle r="1.4" fill="#333333">
            <animateMotion path="M 432 165 Q 452 175 468 195" dur="2.6s" begin="1.4s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="0; 0.8; 0.8; 0" dur="2.6s" begin="1.4s" repeatCount="indefinite" />
          </circle>

          {/* Particle 4: Lower arc */}
          <circle r="1.3" fill="#444444">
            <animateMotion path="M 468 195 Q 450 185 412 188" dur="3.2s" begin="2.1s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="0; 0.75; 0.75; 0" dur="3.2s" begin="2.1s" repeatCount="indefinite" />
          </circle>
        </g>

        {/* ============================================================ */}
        {/* LEFT HAND (Human Support Agent Judgment)                     */}
        {/* Floating gently with animate-float-left                     */}
        {/* ============================================================ */}
        <g id="human-left-hand" className="animate-float-left">
          {/* Halftone stipple fills with subtle reveal animation */}
          <path
            d="M30 330 C100 270, 180 210, 270 160 C320 132, 370 125, 415 145 C425 150, 428 165, 415 178 C390 200, 330 220, 275 255 C210 295, 120 345, 50 360 Z"
            fill="url(#stipple-light)"
            className="animate-stipple"
          />
          <path
            d="M60 320 C130 265, 200 215, 280 170 C325 145, 365 140, 405 155 C410 160, 408 170, 395 180 C365 202, 320 220, 270 250 C210 285, 130 330, 80 345 Z"
            fill="url(#stipple-medium)"
            className="animate-stipple"
          />
          <path
            d="M100 300 C160 255, 225 210, 290 175 C330 152, 360 150, 390 162 C395 166, 390 174, 380 182 C350 202, 310 218, 265 244 C215 275, 150 310, 115 325 Z"
            fill="url(#stipple-dense)"
            className="animate-stipple"
          />

          {/* Forearm & Wrist base contours */}
          <path
            d="M20 350 C80 300, 150 250, 220 205 C260 180, 295 160, 330 148"
            stroke="#111111"
            strokeWidth="1.2"
            strokeLinecap="round"
            strokeDasharray="4 2"
            className="animate-draw-path"
          />
          <path
            d="M50 360 C110 320, 175 275, 240 235 C275 215, 310 198, 345 188"
            stroke="#111111"
            strokeWidth="1.0"
            strokeOpacity="0.7"
            className="animate-draw-path"
          />

          {/* Thumb contour */}
          <path
            d="M255 175 C275 145, 305 120, 335 110 C345 106, 355 112, 350 124 C342 140, 325 160, 300 178"
            stroke="#111111"
            strokeWidth="1.3"
            strokeLinecap="round"
            className="animate-draw-path"
          />
          {/* Index Finger (reaching to center) */}
          <path
            d="M320 150 C350 135, 385 130, 422 142 C430 145, 432 152, 424 158 C400 172, 370 180, 340 188"
            stroke="#111111"
            strokeWidth="1.4"
            strokeLinecap="round"
            className="animate-draw-path"
          />
          {/* Middle Finger */}
          <path
            d="M335 165 C365 152, 400 150, 432 165 C438 168, 438 175, 428 180 C405 192, 375 198, 345 204"
            stroke="#111111"
            strokeWidth="1.2"
            strokeLinecap="round"
            className="animate-draw-path"
          />
          {/* Ring Finger */}
          <path
            d="M325 185 C355 175, 385 175, 412 188 C418 191, 416 197, 408 202 C385 212, 358 218, 330 220"
            stroke="#111111"
            strokeWidth="1.1"
            strokeLinecap="round"
            className="animate-draw-path"
          />
          {/* Pinky Finger */}
          <path
            d="M305 205 C330 198, 358 200, 380 212 C385 215, 383 220, 375 224 C352 232, 330 235, 305 236"
            stroke="#111111"
            strokeWidth="1.0"
            strokeLinecap="round"
            className="animate-draw-path"
          />

          {/* Palm Creases & Anatomical Stipple Dots */}
          <path
            d="M260 215 C285 205, 315 202, 340 205"
            stroke="#222"
            strokeWidth="0.8"
            strokeDasharray="2 3"
          />
          <path
            d="M275 235 C295 228, 320 225, 345 228"
            stroke="#222"
            strokeWidth="0.8"
            strokeDasharray="1 3"
          />

          {/* Crosshatch stipple accents on palm */}
          <circle cx="280" cy="190" r="1.0" fill="#111" />
          <circle cx="288" cy="186" r="1.1" fill="#111" />
          <circle cx="296" cy="182" r="1.2" fill="#111" />
          <circle cx="304" cy="180" r="1.0" fill="#111" />
          <circle cx="312" cy="178" r="1.2" fill="#111" />
          <circle cx="320" cy="175" r="1.1" fill="#111" />
          <circle cx="330" cy="172" r="1.3" fill="#111" />
          <circle cx="340" cy="170" r="1.0" fill="#111" />
          <circle cx="350" cy="166" r="1.2" fill="#111" />
          <circle cx="360" cy="162" r="1.1" fill="#111" />
          <circle cx="370" cy="158" r="1.2" fill="#111" />
          <circle cx="380" cy="154" r="1.0" fill="#111" />
          <circle cx="390" cy="150" r="1.2" fill="#111" />
          <circle cx="400" cy="148" r="1.1" fill="#111" />
          <circle cx="410" cy="146" r="1.3" fill="#111" />
        </g>

        {/* ============================================================ */}
        {/* RIGHT HAND (AI Policy Intelligence Grounding)               */}
        {/* Floating gently with animate-float-right                    */}
        {/* ============================================================ */}
        <g id="ai-right-hand" className="animate-float-right">
          {/* Halftone stipple fills with subtle reveal animation */}
          <path
            d="M870 30 C800 90, 720 150, 630 200 C580 228, 530 235, 485 215 C475 210, 472 195, 485 182 C510 160, 570 140, 625 105 C690 65, 780 15, 850 0 Z"
            fill="url(#stipple-light)"
            className="animate-stipple"
          />
          <path
            d="M840 40 C770 95, 700 145, 620 190 C575 215, 535 220, 495 205 C490 200, 492 190, 505 180 C535 158, 580 140, 630 110 C690 75, 770 30, 820 15 Z"
            fill="url(#stipple-medium)"
            className="animate-stipple"
          />
          <path
            d="M800 60 C740 105, 675 150, 610 185 C570 208, 540 210, 510 198 C505 194, 510 186, 520 178 C550 158, 590 142, 635 116 C685 85, 750 50, 785 35 Z"
            fill="url(#stipple-dense)"
            className="animate-stipple"
          />

          {/* Forearm & Wrist base contours */}
          <path
            d="M880 10 C820 60, 750 110, 680 155 C640 180, 605 200, 570 212"
            stroke="#111111"
            strokeWidth="1.2"
            strokeLinecap="round"
            strokeDasharray="4 2"
            className="animate-draw-path"
          />
          <path
            d="M850 0 C790 40, 725 85, 660 125 C625 145, 590 162, 555 172"
            stroke="#111111"
            strokeWidth="1.0"
            strokeOpacity="0.7"
            className="animate-draw-path"
          />

          {/* Thumb contour */}
          <path
            d="M645 185 C625 215, 595 240, 565 250 C555 254, 545 248, 550 236 C558 220, 575 200, 600 182"
            stroke="#111111"
            strokeWidth="1.3"
            strokeLinecap="round"
            className="animate-draw-path"
          />
          {/* Index Finger (reaching to center) */}
          <path
            d="M580 210 C550 225, 515 230, 478 218 C470 215, 468 208, 476 202 C500 188, 530 180, 560 172"
            stroke="#111111"
            strokeWidth="1.4"
            strokeLinecap="round"
            className="animate-draw-path"
          />
          {/* Middle Finger */}
          <path
            d="M565 195 C535 208, 500 210, 468 195 C462 192, 462 185, 472 180 C495 168, 525 162, 555 156"
            stroke="#111111"
            strokeWidth="1.2"
            strokeLinecap="round"
            className="animate-draw-path"
          />
          {/* Ring Finger */}
          <path
            d="M575 175 C545 185, 515 185, 488 172 C482 169, 484 163, 492 158 C515 148, 542 142, 570 140"
            stroke="#111111"
            strokeWidth="1.1"
            strokeLinecap="round"
            className="animate-draw-path"
          />
          {/* Pinky Finger */}
          <path
            d="M595 155 C570 162, 542 160, 520 148 C515 145, 517 140, 525 136 C548 128, 570 125, 595 124"
            stroke="#111111"
            strokeWidth="1.0"
            strokeLinecap="round"
            className="animate-draw-path"
          />

          {/* Precision AI Halftone Grid Node Lines on Right Hand */}
          <g stroke="#111" strokeWidth="0.6" strokeDasharray="1 3" opacity="0.7">
            <line x1="560" y1="180" x2="620" y2="140" />
            <line x1="575" y1="195" x2="635" y2="155" />
            <line x1="550" y1="210" x2="610" y2="170" />
            <line x1="535" y1="225" x2="595" y2="185" />
          </g>

          {/* Discrete digital/stipple alignment points */}
          <circle cx="620" cy="170" r="1.0" fill="#111" />
          <circle cx="612" cy="174" r="1.1" fill="#111" />
          <circle cx="604" cy="178" r="1.2" fill="#111" />
          <circle cx="596" cy="180" r="1.0" fill="#111" />
          <circle cx="588" cy="182" r="1.2" fill="#111" />
          <circle cx="580" cy="185" r="1.1" fill="#111" />
          <circle cx="570" cy="188" r="1.3" fill="#111" />
          <circle cx="560" cy="190" r="1.0" fill="#111" />
          <circle cx="550" cy="194" r="1.2" fill="#111" />
          <circle cx="540" cy="198" r="1.1" fill="#111" />
          <circle cx="530" cy="202" r="1.2" fill="#111" />
          <circle cx="520" cy="206" r="1.0" fill="#111" />
          <circle cx="510" cy="210" r="1.2" fill="#111" />
          <circle cx="500" cy="212" r="1.1" fill="#111" />
          <circle cx="490" cy="214" r="1.3" fill="#111" />
        </g>

        {/* Subtle moving light shimmer across hands */}
        <rect
          x="0"
          y="0"
          width="900"
          height="360"
          fill="url(#shimmer-flow)"
          opacity="0.6"
          pointerEvents="none"
        />
      </svg>
    </div>
  );
};
