import React, { useState, useMemo, useRef, useEffect } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { useClerk, SignIn } from '@clerk/clerk-react';
import {
  motion,
  AnimatePresence,
  useMotionValue,
  useAnimationFrame,
  useTransform,
  useMotionTemplate,
} from 'framer-motion';
import useMeasure from 'react-use-measure';
import { Fingerprint, ArrowRight, ChevronLeft, Plus, Wallet } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// -------------------------------------------------------------
// Type Definitions
// -------------------------------------------------------------
export interface AuthUser {
  id: string;
  name: string;
  identifier: string;
  method: 'email' | 'phone' | 'passkey' | 'wallet' | 'social';
  avatar?: string;
}

export interface Skiper21Props {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  onSuccess?: (user: AuthUser) => void;
  showTrigger?: boolean;
  triggerClassName?: string;
}

type AuthView = 'signin' | 'email-otp' | 'phone-otp' | 'passkey' | 'wallet';

// -------------------------------------------------------------
// SVG Icons
// -------------------------------------------------------------
const GoogleIcon = () => (
  <svg className="size-5" viewBox="0 0 24 24" fill="none">
    <path
      d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z"
      fill="#4285F4"
    />
    <path
      d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.13C3.26 21.36 7.33 24 12 24z"
      fill="#34A853"
    />
    <path
      d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.6H1.25C.45 8.19 0 10.04 0 12s.45 3.81 1.25 5.4l4.03-3.13z"
      fill="#FBBC05"
    />
    <path
      d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.25 6.6l4.03 3.13c.95-2.83 3.6-4.98 6.72-4.98z"
      fill="#EA4335"
    />
  </svg>
);

const DiscordIcon = () => (
  <svg className="size-5" viewBox="0 0 24 24" fill="#5865F2">
    <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.929 1.793 8.18 1.793 12.061 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.894.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.028zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z" />
  </svg>
);

const GitHubIcon = () => (
  <svg className="size-5" viewBox="0 0 24 24" fill="currentColor">
    <path
      fillRule="evenodd"
      clipRule="evenodd"
      d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
    />
  </svg>
);

const AppleIcon = () => (
  <svg className="size-5" viewBox="0 0 24 24" fill="currentColor">
    <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M15.97 6.42c.67-.82 1.13-1.96.99-3.11-1.01.05-2.24.68-2.94 1.5-.62.73-1.16 1.89-1.02 3 1.13.09 2.29-.57 2.97-1.39z" />
  </svg>
);

const FarcasterIcon = () => (
  <svg className="size-5" viewBox="0 0 1000 1000" fill="#855DCD">
    <path d="M257.778 155.556h484.444v688.888H257.778z" fill="none" />
    <path d="M155.556 257.778c0-56.455 45.767-102.222 102.222-102.222h484.444c56.455 0 102.222 45.767 102.222 102.222v484.444c0 56.455-45.767 102.222-102.222 102.222H257.778c-56.455 0-102.222-45.767-102.222-102.222V257.778z" />
    <path
      d="M694.444 372.222H305.556v72.222h388.888v-72.222zm0 144.445H305.556v72.222h255.555v144.445h72.222v-72.222H694.444v-144.445z"
      fill="#fff"
    />
  </svg>
);

const MetaMaskIcon = ({ className = 'size-6' }: { className?: string }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="34.14" height="32" viewBox="0 0 256 240" className={className}>
    <path fill="#E17726" d="M250.066 0L140.219 81.279l20.427-47.9z" />
    <path
      fill="#E27625"
      d="m6.191.096l89.181 33.289l19.396 48.528zM205.86 172.858l48.551.924l-16.968 57.642l-59.243-16.311zm-155.721 0l27.557 42.255l-59.143 16.312l-16.865-57.643z"
    />
    <path
      fill="#E27625"
      d="m112.131 69.552l1.984 64.083l-59.371-2.701l16.888-25.478l.214-.245zm31.123-.715l40.9 36.376l.212.244l16.888 25.478l-59.358 2.7zM79.435 173.044l32.418 25.259l-37.658 18.181zm97.136-.004l5.131 43.445l-37.553-18.184z"
    />
    <path fill="#D5BFB2" d="m144.978 195.922l38.107 18.452l-35.447 16.846l.368-11.134zm-33.967.008l-2.909 23.974l.239 11.303l-35.53-16.833z" />
    <path fill="#233447" d="m100.007 141.999l9.958 20.928l-33.903-9.932zm55.985.002l24.058 10.994l-34.014 9.929z" />
    <path
      fill="#CC6228"
      d="m82.026 172.83l-5.48 45.04l-29.373-44.055zm91.95.001l34.854.984l-29.483 44.057zm28.136-44.444l-25.365 25.851l-19.557-8.937l-9.363 19.684l-6.138-33.849zm-148.237 0l60.435 2.749l-6.139 33.849l-9.365-19.681l-19.453 8.935z"
    />
    <path
      fill="#E27525"
      d="m52.166 123.082l28.698 29.121l.994 28.749zm151.697-.052l-29.746 57.973l1.12-28.8zm-90.956 1.826l1.155 7.27l2.854 18.111l-1.835 55.625l-8.675-44.685l-.003-.462zm30.171-.101l6.521 35.96l-.003.462l-8.697 44.797l-.344-11.205l-1.357-44.862z"
    />
    <path fill="#F5841F" d="m177.788 151.046l-.971 24.978l-30.274 23.587l-6.12-4.324l6.86-35.335zm-99.471 0l30.399 8.906l6.86 35.335l-6.12 4.324l-30.275-23.589z" />
    <path fill="#C0AC9D" d="m67.018 208.858l38.732 18.352l-.164-7.837l3.241-2.845h38.334l3.358 2.835l-.248 7.831l38.487-18.29l-18.728 15.476l-22.645 15.553h-38.869l-22.63-15.617z" />
    <path fill="#161616" d="m142.204 193.479l5.476 3.869l3.209 25.604l-4.644-3.921h-36.476l-4.556 4l3.104-25.681l5.478-3.871z" />
    <path
      fill="#763E1A"
      d="M242.814 2.25L256 41.807l-8.235 39.997l5.864 4.523l-7.935 6.054l5.964 4.606l-7.897 7.191l4.848 3.511l-12.866 15.026l-52.77-15.365l-.457-.245l-38.027-32.078zm-229.628 0l98.326 72.777l-38.028 32.078l-.457.245l-52.77 15.365l-12.866-15.026l4.844-3.508l-7.892-7.194l5.952-4.601l-8.054-6.071l6.085-4.526L0 41.809z"
    />
    <path
      fill="#F5841F"
      d="m180.392 103.99l55.913 16.279l18.165 55.986h-47.924l-33.02.416l24.014-46.808zm-104.784 0l-17.151 25.873l24.017 46.808l-33.005-.416H1.631l18.063-55.985zm87.776-70.878l-15.639 42.239l-3.319 57.06l-1.27 17.885l-.101 45.688h-30.111l-.098-45.602l-1.274-17.986l-3.32-57.045l-15.637-42.239z"
    />
  </svg>
);

const CoinbaseIcon = ({ className = 'size-6' }: { className?: string }) => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
    <circle cx="10" cy="10" r="10" fill="#0852FF" />
    <rect rx="27%" width="20" height="20" fill="#0852FF" />
    <path
      fillRule="evenodd"
      clipRule="evenodd"
      d="M10.0001 17C13.8661 17 17.0001 13.866 17.0001 10C17.0001 6.13401 13.8661 3 10.0001 3C6.13413 3 3.00012 6.13401 3.00012 10C3.00012 13.866 6.13413 17 10.0001 17ZM8.25012 7.71429C7.95427 7.71429 7.71441 7.95414 7.71441 8.25V11.75C7.71441 12.0459 7.95427 12.2857 8.25012 12.2857H11.7501C12.046 12.2857 12.2858 12.0459 12.2858 11.75V8.25C12.2858 7.95414 12.046 7.71429 11.7501 7.71429H8.25012Z"
      fill="white"
    />
  </svg>
);

const PhantomIcon = () => (
  <div className="flex size-6 items-center justify-center rounded-full bg-[#AB9EF2]">
    <svg xmlns="http://www.w3.org/2000/svg" width="593" height="493" viewBox="0 0 593 493" fill="none" className="size-4">
      <path
        d="M70.0546 493C145.604 493 202.38 427.297 236.263 375.378C232.142 386.865 229.852 398.351 229.852 409.378C229.852 439.703 247.252 461.297 281.592 461.297C328.753 461.297 379.119 419.946 405.218 375.378C403.386 381.811 402.471 387.784 402.471 393.297C402.471 414.432 414.375 427.757 438.643 427.757C515.108 427.757 592.03 292.216 592.03 173.676C592.03 81.3243 545.327 0 428.112 0C222.069 0 0 251.784 0 414.432C0 478.297 34.3405 493 70.0546 493ZM357.141 163.568C357.141 140.595 369.962 124.514 388.734 124.514C407.049 124.514 419.87 140.595 419.87 163.568C419.87 186.541 407.049 203.081 388.734 203.081C369.962 203.081 357.141 186.541 357.141 163.568ZM455.126 163.568C455.126 140.595 467.947 124.514 486.719 124.514C505.034 124.514 517.855 140.595 517.855 163.568C517.855 186.541 505.034 203.081 486.719 203.081C467.947 203.081 455.126 186.541 455.126 163.568Z"
        fill="#FFFDF8"
      />
    </svg>
  </div>
);

const TrustWalletIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" className="size-6">
    <g fill="none">
      <path fill="#0500FF" d="M3.9 5.6L12 3v18c-5.786-2.4-8.1-7-8.1-9.6z" />
      <path fill="url(#tokenBrandedTrust0)" d="M20.1 5.6L12 3v18c5.786-2.4 8.1-7 8.1-9.6z" />
      <defs>
        <linearGradient id="tokenBrandedTrust0" x1="17.948" x2="11.967" y1="1.74" y2="20.797" gradientUnits="userSpaceOnUse">
          <stop offset=".02" stopColor="#00F" />
          <stop offset=".08" stopColor="#0094FF" />
          <stop offset=".16" stopColor="#48FF91" />
          <stop offset=".42" stopColor="#0094FF" />
          <stop offset=".68" stopColor="#0038FF" />
          <stop offset=".9" stopColor="#0500FF" />
        </linearGradient>
      </defs>
    </g>
  </svg>
);

// -------------------------------------------------------------
// MovingBorder Effect (Skiper21 Signature)
// -------------------------------------------------------------
export const MovingBorder = ({
  children,
  duration = 3000,
  rx,
  ry,
  ...otherProps
}: {
  children: React.ReactNode;
  duration?: number;
  rx?: string;
  ry?: string;
  [key: string]: unknown;
}) => {
  const pathRef = useRef<SVGRectElement>(null);
  const progress = useMotionValue(0);

  useAnimationFrame((time) => {
    const length = pathRef.current?.getTotalLength();
    if (length) {
      progress.set(((length / duration) * time) % length);
    }
  });

  const x = useTransform(progress, (val) => pathRef.current?.getPointAtLength(val).x);
  const y = useTransform(progress, (val) => pathRef.current?.getPointAtLength(val).y);
  const transform = useMotionTemplate`translateX(${x}px) translateY(${y}px) translateX(-50%) translateY(-50%)`;

  return (
    <>
      <svg
        xmlns="http://www.w3.org/2000/svg"
        preserveAspectRatio="none"
        className="absolute h-full w-full"
        width="100%"
        height="100%"
        {...otherProps}
      >
        <rect fill="none" width="100%" height="100%" rx={rx} ry={ry} ref={pathRef} />
      </svg>
      <motion.div style={{ position: 'absolute', top: 0, left: 0, display: 'inline-block', transform }}>
        {children}
      </motion.div>
    </>
  );
};

export function Button({
  borderRadius = '1.75rem',
  children,
  as: Component = 'button',
  containerClassName,
  borderClassName,
  duration = 1500,
  className,
  ...otherProps
}: {
  borderRadius?: string;
  children: React.ReactNode;
  as?: React.ElementType;
  containerClassName?: string;
  borderClassName?: string;
  duration?: number;
  className?: string;
  [key: string]: unknown;
}) {
  return (
    <Component
      className={cn('relative overflow-hidden bg-transparent p-[1px] text-xl', containerClassName)}
      style={{ borderRadius }}
      {...otherProps}
    >
      <div className="absolute inset-0" style={{ borderRadius: `calc(${borderRadius} * 0.96)` }}>
        <MovingBorder duration={duration} rx="30%" ry="30%">
          <div
            className={cn('h-20 w-20 bg-[radial-gradient(#0ea5e9_40%,transparent_60%)] opacity-[0.8]', borderClassName)}
          />
        </MovingBorder>
      </div>
      <div
        className={cn(
          'relative flex h-full w-full items-center justify-center border border-slate-800 bg-slate-900/[0.8] text-sm text-white antialiased backdrop-blur-xl',
          className
        )}
        style={{ borderRadius: `calc(${borderRadius} * 0.96)` }}
      >
        {children}
      </div>
    </Component>
  );
}

// -------------------------------------------------------------
// 6-Digit OTP Field Component
// -------------------------------------------------------------
function InputOTP({
  value,
  onChange,
  onComplete,
}: {
  value: string;
  onChange: (val: string) => void;
  onComplete?: () => void;
}) {
  const inputsRef = useRef<(HTMLInputElement | null)[]>([]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>, index: number) => {
    const val = e.target.value.replace(/\D/g, '');
    const char = val.slice(-1);
    const newChars = value.padEnd(6, ' ').split('');
    newChars[index] = char || ' ';
    const updated = newChars.join('').trimEnd();
    onChange(updated);

    if (char && index < 5) {
      inputsRef.current[index + 1]?.focus();
    }
    if (updated.replace(/\s/g, '').length === 6) {
      onComplete?.();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>, index: number) => {
    if (e.key === 'Backspace' && !value[index] && index > 0) {
      inputsRef.current[index - 1]?.focus();
    }
    if (e.key === 'Enter') {
      onComplete?.();
    }
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    onChange(pasted);
    if (pasted.length === 6) {
      onComplete?.();
      inputsRef.current[5]?.focus();
    } else {
      inputsRef.current[pasted.length]?.focus();
    }
  };

  return (
    <div className="flex justify-between gap-2.5 sm:gap-3">
      {Array.from({ length: 6 }).map((_, idx) => {
        const char = value[idx] || '';
        return (
          <input
            key={idx}
            ref={(el) => (inputsRef.current[idx] = el)}
            type="text"
            inputMode="numeric"
            maxLength={1}
            value={char}
            onChange={(e) => handleChange(e, idx)}
            onKeyDown={(e) => handleKeyDown(e, idx)}
            onPaste={handlePaste}
            autoFocus={idx === 0}
            className="!bg-[#232328] border-none text-white text-center font-mono font-semibold text-lg h-11 w-full !rounded-xl outline-none focus:ring-2 focus:ring-[#4EAFFF]/50 transition-all select-none"
          />
        );
      })}
    </div>
  );
}

// -------------------------------------------------------------
// Views: Sign In, OTP, Passkey, Wallet
// -------------------------------------------------------------
const SOCIAL_PROVIDERS = [
  { icon: GoogleIcon, label: 'Sign in with Google', id: 'google' },
  { icon: DiscordIcon, label: 'Sign in with Discord', id: 'discord' },
  { icon: GitHubIcon, label: 'Sign in with GitHub', id: 'github' },
  { icon: AppleIcon, label: 'Sign in with Apple', id: 'apple' },
  { icon: FarcasterIcon, label: 'Sign in with Farcaster', id: 'farcaster' },
];

const AUTH_TABS = ['Email', 'Phone', 'Passkey'] as const;

function SignInView({
  setView,
  onAuthenticate,
  targetValue,
  setTargetValue,
}: {
  setView: (v: AuthView) => void;
  onAuthenticate: (user: AuthUser) => void;
  targetValue: string;
  setTargetValue: (val: string) => void;
}) {
  const [selectedTab, setSelectedTab] = useState<'Email' | 'Phone' | 'Passkey'>('Email');

  const config = useMemo(() => {
    switch (selectedTab) {
      case 'Email':
        return {
          type: 'email',
          placeholder: 'yo@gxuri.me',
          pattern: '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$',
        };
      case 'Phone':
        return {
          type: 'tel',
          placeholder: '+1 (555) 123-4567',
          pattern: '^[+]?[0-9\\s\\-\\(\\)]{10,}$',
        };
      case 'Passkey':
        return {
          type: 'text',
          placeholder: 'Login with passkey',
          pattern: '^[a-zA-Z0-9]{6,}$',
        };
    }
  }, [selectedTab]);

  const isValid = useMemo(() => {
    if (selectedTab === 'Passkey') return true;
    if (!targetValue.trim()) return false;
    return new RegExp(config.pattern).test(targetValue.trim());
  }, [selectedTab, targetValue, config.pattern]);

  const handleSubmit = () => {
    if (selectedTab === 'Passkey') {
      setView('passkey');
      return;
    }
    if (!targetValue.trim()) {
      alert('Please enter a value');
      return;
    }
    if (!new RegExp(config.pattern).test(targetValue.trim())) {
      alert(`Please enter a valid ${selectedTab.toLowerCase()}`);
      return;
    }
    if (selectedTab === 'Email') {
      setView('email-otp');
    } else if (selectedTab === 'Phone') {
      setView('phone-otp');
    }
  };

  return (
    <div>
      <div className="flex flex-col space-y-1.5 text-center sm:text-left">
        <h2 className="flex items-center justify-between px-6 py-6 text-center text-xl font-semibold tracking-tight sm:font-medium text-white">
          <span className="select-none">Sign In</span>
        </h2>
      </div>

      <div className="flex flex-col gap-4 pt-2">
        <div className="flex flex-col gap-2 px-6">
          {/* Social Icons Strip */}
          <div className="flex w-full items-center justify-center gap-2">
            {SOCIAL_PROVIDERS.map((item) => (
              <button
                key={item.label}
                aria-label={item.label}
                onClick={() =>
                  onAuthenticate({
                    id: `usr_${item.id}_${Date.now().toString(36)}`,
                    name: `Verified ${item.label.replace('Sign in with ', '')} User`,
                    identifier: `${item.id}_auth@policypulse.ai`,
                    method: 'social',
                  })
                }
                className="bg-[#18181c] hover:bg-[#222228] group flex h-12 w-full items-center justify-center rounded-xl transition-all duration-200 ease-out active:scale-95 text-white/80 hover:text-white cursor-pointer"
              >
                <item.icon />
              </button>
            ))}
          </div>

          {/* Tab Switcher: Email / Phone / Passkey */}
          <div className="bg-[#18181c] flex h-12 w-full items-center rounded-2xl px-1">
            <div className="relative mx-auto flex w-full items-center">
              <ul className="mx-auto flex w-full flex-row justify-center gap-2 list-none p-0 m-0">
                {AUTH_TABS.map((tab) => (
                  <button
                    key={tab}
                    aria-label={`Select ${tab}`}
                    onClick={() => {
                      setSelectedTab(tab);
                      setTargetValue('');
                    }}
                    className={cn(
                      'relative flex h-10 w-full cursor-pointer items-center justify-center px-3 py-1.5 text-center text-base font-semibold transition-colors duration-200 ease-out sm:font-medium',
                      selectedTab === tab ? 'text-white' : 'text-[#8e8e9c]'
                    )}
                  >
                    {selectedTab === tab && (
                      <motion.div
                        layoutId="selected-method"
                        className="bg-white/10 absolute inset-0 rounded-xl"
                        transition={{ type: 'spring', stiffness: 450, damping: 35 }}
                      />
                    )}
                    <span className="relative select-none text-inherit">{tab}</span>
                  </button>
                ))}
              </ul>
            </div>
          </div>

          {/* Input & Submit Button */}
          <div className="bg-[#18181c] flex h-12 w-full items-center justify-start gap-3 overflow-hidden rounded-2xl pl-4 pr-1 text-base">
            <div className="flex w-full items-center justify-start">
              {selectedTab === 'Passkey' ? (
                <div
                  onClick={() => setView('passkey')}
                  className="flex items-center gap-3 cursor-pointer w-full py-2"
                >
                  <Fingerprint className="text-[#8e8e9c] h-6 w-6" />
                  <span className="sm:font-regular w-full text-base font-medium tracking-tight opacity-50 text-white">
                    {config.placeholder}
                  </span>
                </div>
              ) : (
                <input
                  placeholder={config.placeholder}
                  autoFocus
                  className="focus-visible:outline-none sm:font-regular w-full text-base font-medium text-white placeholder-white/30 bg-transparent disabled:cursor-not-allowed disabled:opacity-50"
                  type={config.type}
                  value={targetValue}
                  onChange={(e) => setTargetValue(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleSubmit();
                  }}
                />
              )}
            </div>

            <button
              aria-label="Continue"
              type="submit"
              onClick={handleSubmit}
              disabled={!isValid}
              className={cn(
                'shadow-sm group flex h-10 w-12 shrink-0 items-center justify-center rounded-xl transition-all duration-200 ease-out',
                isValid
                  ? 'cursor-pointer bg-[#4EAFFF] text-white hover:bg-[#4EAFFF]/90 active:scale-95'
                  : 'bg-[#222228] text-[#8e8e9c] cursor-not-allowed'
              )}
            >
              <ArrowRight className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Or Divider & Connect Wallet */}
        <div className="flex flex-col gap-4 px-6 pb-6">
          <div className="relative">
            <div className="absolute inset-0 flex h-10 items-center">
              <span className="w-full rounded-full border-t border-white/10 opacity-30" />
            </div>
            <div className="relative flex h-10 justify-center text-xs uppercase">
              <span className="bg-[#121215] text-[#8e8e9c] flex items-center justify-center px-2 font-medium">
                Or
              </span>
            </div>
          </div>

          <button
            onClick={() => setView('wallet')}
            className="flex h-12 w-full cursor-pointer select-none items-center justify-center gap-2 rounded-full bg-[#4EAFFF] text-base font-semibold text-white transition-all duration-200 ease-out hover:bg-[#4EAFFF]/85 focus:scale-95 active:scale-95 sm:font-medium shadow-md shadow-[#4EAFFF]/20"
          >
            <Wallet className="h-5 w-5" />
            Connect Wallet
          </button>
        </div>
      </div>
    </div>
  );
}

function EmailOtpView({
  setView,
  email,
  onAuthenticate,
}: {
  setView: (v: AuthView) => void;
  email: string;
  onAuthenticate: (user: AuthUser) => void;
}) {
  const [code, setCode] = useState('');

  const handleVerify = () => {
    onAuthenticate({
      id: `usr_email_${Date.now().toString(36)}`,
      name: 'Agent Marcus Aurelius',
      identifier: email || 'yo@guri.in',
      method: 'email',
    });
  };

  return (
    <div>
      <div className="flex items-center justify-between gap-3 px-6 py-6 text-center text-xl font-semibold tracking-tight sm:font-medium text-white">
        <button
          onClick={() => setView('signin')}
          className="bg-[#2a2a32] text-white flex h-8 w-8 items-center justify-center rounded-full transition-transform focus:scale-95 active:scale-75 cursor-pointer"
        >
          <ChevronLeft className="opacity-70 h-4 w-4" />
        </button>
        <h2 className="select-none">Confirm Email</h2>
        <span className="bg-[#2a2a32] size-8 opacity-0" />
      </div>

      <div className="space-y-6 px-6 text-center">
        <div>
          <p className="text-[#8e8e9c] text-sm">Enter the verification code sent to</p>
          <h1 className="font-medium tracking-tight text-white text-base mt-0.5">{email || 'yo@guri.in'}</h1>
        </div>

        <div className="space-y-4">
          <InputOTP value={code} onChange={setCode} onComplete={handleVerify} />
          <button
            onClick={handleVerify}
            className="mb-6 w-full rounded-full bg-emerald-500 hover:bg-emerald-600 py-3 font-semibold text-white transition-colors cursor-pointer shadow-md shadow-emerald-500/20 active:scale-98"
          >
            Verify Code
          </button>
        </div>
      </div>
    </div>
  );
}

function PhoneOtpView({
  setView,
  phone,
  onAuthenticate,
}: {
  setView: (v: AuthView) => void;
  phone: string;
  onAuthenticate: (user: AuthUser) => void;
}) {
  const [code, setCode] = useState('');

  const handleVerify = () => {
    onAuthenticate({
      id: `usr_phone_${Date.now().toString(36)}`,
      name: 'Senior Human Reviewer',
      identifier: phone || '+1 (555) 123-4567',
      method: 'phone',
    });
  };

  return (
    <div>
      <div className="flex items-center justify-between gap-3 px-6 py-6 text-center text-xl font-semibold tracking-tight sm:font-medium text-white">
        <button
          onClick={() => setView('signin')}
          className="bg-[#2a2a32] text-white flex h-8 w-8 items-center justify-center rounded-full transition-transform focus:scale-95 active:scale-75 cursor-pointer"
        >
          <ChevronLeft className="opacity-70 h-4 w-4" />
        </button>
        <h2 className="select-none">Confirm Phone</h2>
        <span className="bg-[#2a2a32] size-8 opacity-0" />
      </div>

      <div className="space-y-6 px-6 text-center">
        <div>
          <p className="text-[#8e8e9c] text-sm">Enter the verification code sent to</p>
          <h1 className="font-medium tracking-tight text-white text-base mt-0.5">{phone || '+1 (555) 123-4567'}</h1>
        </div>

        <div className="space-y-4">
          <InputOTP value={code} onChange={setCode} onComplete={handleVerify} />
          <button
            onClick={handleVerify}
            className="mb-6 w-full rounded-full bg-emerald-500 hover:bg-emerald-600 py-3 font-semibold text-white transition-colors cursor-pointer shadow-md shadow-emerald-500/20 active:scale-98"
          >
            Verify Code
          </button>
        </div>
      </div>
    </div>
  );
}

function PasskeyView({
  setView,
  onAuthenticate,
}: {
  setView: (v: AuthView) => void;
  onAuthenticate: (user: AuthUser) => void;
}) {
  const handlePasskeyAuth = () => {
    onAuthenticate({
      id: `usr_pk_${Date.now().toString(36)}`,
      name: 'Agent Marcus Aurelius',
      identifier: 'FIDO2-Secured Passkey',
      method: 'passkey',
    });
  };

  return (
    <div>
      <div className="flex items-center justify-between gap-3 px-6 py-6 text-center text-xl font-semibold tracking-tight sm:font-medium text-white">
        <button
          onClick={() => setView('signin')}
          className="bg-[#2a2a32] text-white flex h-8 w-8 items-center justify-center rounded-full transition-transform focus:scale-95 active:scale-75 cursor-pointer"
        >
          <ChevronLeft className="opacity-70 h-4 w-4" />
        </button>
        <h2 className="select-none">Passkey</h2>
        <span className="bg-[#2a2a32] size-8 opacity-0" />
      </div>

      <div className="flex flex-col items-center justify-center space-y-6 px-6 text-center">
        <Button
          duration={1500}
          borderRadius="30px"
          containerClassName="p-[6px]"
          className="border-[#2a2a32] outline-3 text-white outline-[#121215] bg-[#18181c] border-2 flex size-20 items-center justify-center !rounded-[24px]"
        >
          <Fingerprint className="size-8 opacity-75 text-[#4EAFFF]" />
        </Button>

        <div>
          <h1 className="text-xl font-medium tracking-tight text-white">Waiting for passkey</h1>
          <p className="text-[#8e8e9c] max-w-[240px] mt-1 text-sm">Please follow prompts to verify your passkey.</p>
        </div>

        <button
          onClick={handlePasskeyAuth}
          className="mb-6 w-full rounded-full bg-[#4EAFFF] hover:bg-[#4EAFFF]/90 py-3 font-semibold text-white transition-colors cursor-pointer shadow-md shadow-[#4EAFFF]/25 active:scale-98"
        >
          Continue
        </button>
      </div>
    </div>
  );
}

function WalletView({
  setView,
  onAuthenticate,
}: {
  setView: (v: AuthView) => void;
  onAuthenticate: (user: AuthUser) => void;
}) {
  const handleSelectWallet = (walletName: string) => {
    onAuthenticate({
      id: `usr_w3_${Date.now().toString(36)}`,
      name: `${walletName} Signer`,
      identifier: '0x71C...49A2',
      method: 'wallet',
    });
  };

  return (
    <div>
      <div className="flex items-center justify-between gap-3 px-6 py-6 text-center text-xl font-semibold tracking-tight sm:font-medium text-white">
        <button
          onClick={() => setView('signin')}
          className="bg-[#2a2a32] text-white flex h-8 w-8 items-center justify-center rounded-full transition-transform focus:scale-95 active:scale-75 cursor-pointer"
        >
          <ChevronLeft className="opacity-70 h-4 w-4" />
        </button>
        <h2 className="select-none">Connect Wallet</h2>
        <span className="bg-[#2a2a32] size-8 opacity-0" />
      </div>

      <div className="space-y-2 px-6 pb-6 text-center">
        <div
          onClick={() => handleSelectWallet('Metamask')}
          className="bg-[#18181c] hover:bg-[#222228] h-14 flex cursor-pointer items-center justify-between rounded-2xl px-4 transition-colors"
        >
          <h1 className="text-base font-medium tracking-tight text-white">Metamask</h1>
          <MetaMaskIcon className="size-6" />
        </div>

        <div
          onClick={() => handleSelectWallet('Coinbase')}
          className="bg-[#18181c] hover:bg-[#222228] h-14 flex cursor-pointer items-center justify-between rounded-2xl px-4 transition-colors"
        >
          <h1 className="text-base font-medium tracking-tight text-white">Coinbase</h1>
          <CoinbaseIcon className="size-6" />
        </div>

        <div
          onClick={() => handleSelectWallet('Phantom')}
          className="bg-[#18181c] hover:bg-[#222228] h-14 flex cursor-pointer items-center justify-between rounded-2xl px-4 transition-colors"
        >
          <h1 className="text-base font-medium tracking-tight text-white">Phantom</h1>
          <PhantomIcon />
        </div>

        <div
          onClick={() => handleSelectWallet('Trust Wallet')}
          className="bg-[#18181c] hover:bg-[#222228] h-14 flex cursor-pointer items-center justify-between rounded-2xl px-4 transition-colors"
        >
          <h1 className="text-base font-medium tracking-tight text-white">Trust Wallet</h1>
          <TrustWalletIcon />
        </div>

        <div
          onClick={() => handleSelectWallet('Other Wallet')}
          className="bg-[#18181c] hover:bg-[#222228] h-14 flex cursor-pointer items-center justify-between rounded-2xl px-4 transition-colors"
        >
          <div className="flex items-center justify-start gap-3">
            <span className="text-center text-base font-medium text-white">Other Wallets</span>
            <div className="border-white/10 text-white/50 bg-[#121215] flex select-none items-center justify-center rounded-full border px-2 py-0.5 text-xs font-semibold sm:font-medium">
              350+
            </div>
          </div>
          <div className="border-white/10 text-white/50 bg-[#121215] flex size-8 select-none items-center justify-center rounded-lg border text-xs font-semibold sm:font-medium">
            <Wallet className="size-4 opacity-70" />
          </div>
        </div>

        <button
          onClick={() => setView('signin')}
          className="hover:text-white text-[#8e8e9c] flex w-full items-center justify-center gap-2 pb-2 pt-5 font-semibold sm:font-medium text-sm cursor-pointer transition-colors"
        >
          <Wallet className="size-4" />
          I Don't Have a Wallet
        </button>
      </div>
    </div>
  );
}

// -------------------------------------------------------------
// Primary Skiper21 Component
// -------------------------------------------------------------
export const Skiper21: React.FC<Skiper21Props> = ({
  open: controlledOpen,
  onOpenChange: setControlledOpen,
  onSuccess: _onSuccess,
  showTrigger = false,
  triggerClassName,
}) => {
  const [uncontrolledOpen, setUncontrolledOpen] = useState(false);
  const isControlled = controlledOpen !== undefined;
  const isOpen = isControlled ? controlledOpen : uncontrolledOpen;
  const setIsOpen = isControlled ? setControlledOpen! : setUncontrolledOpen;

  const [currentView, _setCurrentView] = useState<AuthView>('signin');
  const [measureRef, bounds] = useMeasure();
  const clerk = useClerk();

  // Forward immediately to official Clerk modal
  useEffect(() => {
    if (isOpen && clerk?.openSignIn) {
      clerk.openSignIn();
      setIsOpen(false);
    }
  }, [isOpen, clerk, setIsOpen]);

  const renderedView = useMemo(() => {
    return (
      <div className="p-4 flex justify-center bg-[#121215]">
        <SignIn routing="hash" />
      </div>
    );
  }, []);

  return (
    <>
      {/* Optional Standalone Trigger as in Skiper UI Demo */}
      {showTrigger && (
        <div className={cn('h-full w-full select-none', triggerClassName)}>
          <div className="bg-[#121215] flex h-full w-full flex-col items-center justify-center p-8">
            <div className="mb-20 grid content-start justify-items-center gap-6 text-center">
              <span className="after:to-white relative max-w-[12ch] text-xs uppercase leading-tight opacity-40 after:absolute after:left-1/2 after:top-full after:h-16 after:w-px after:bg-gradient-to-b after:from-transparent after:content-['']">
                Click to open sign in
              </span>
            </div>
            <button
              onClick={() => setIsOpen(true)}
              className="bg-[#2a2a32] text-white hover:bg-[#34343e] rounded-full px-5 py-2.5 text-sm font-medium transition-all shadow-lg active:scale-95 cursor-pointer"
            >
              Sign In
            </button>
          </div>
        </div>
      )}

      {/* Skiper21 Radix Dialog + Motion Bottom Sheet */}
      <Dialog.Root open={isOpen} onOpenChange={setIsOpen}>
        <Dialog.Portal>
          <Dialog.Overlay
            className="fixed inset-0 z-50 bg-black/65 backdrop-blur-sm transition-opacity"
            onClick={() => setIsOpen(false)}
          />
          <Dialog.Content
            className="fixed inset-x-4 bottom-4 mx-auto max-w-[361px] overflow-hidden rounded-[36px] bg-[#121215] border border-white/10 outline-none z-50 md:mx-auto md:w-full shadow-2xl"
            style={{
              fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            }}
          >
            <Dialog.Title className="sr-only">Sign In</Dialog.Title>
            <Dialog.Description className="sr-only">
              Skiper UI authentication drawer with multi-method login options.
            </Dialog.Description>

            <motion.div
              animate={{
                height: bounds.height > 0 ? bounds.height : 'auto',
                transition: { duration: 0.27, ease: [0.25, 1, 0.5, 1] },
              }}
            >
              <Dialog.Close asChild>
                <button
                  className="bg-[#2a2a32] text-white absolute right-6 top-5 z-10 flex h-8 w-8 items-center justify-center rounded-full transition-transform focus:scale-95 active:scale-75 hover:bg-[#383842] cursor-pointer"
                  aria-label="Close"
                >
                  <Plus className="rotate-45 opacity-60 h-4 w-4" />
                </button>
              </Dialog.Close>

              <div ref={measureRef} className="bg-[#121215]">
                <AnimatePresence initial={false} mode="popLayout" custom={currentView}>
                  <motion.div
                    key={currentView}
                    initial={{ opacity: 0, scale: 0.96 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.96 }}
                    transition={{ duration: 0.27, ease: [0.26, 0.08, 0.25, 1] }}
                  >
                    {renderedView}
                  </motion.div>
                </AnimatePresence>
              </div>
            </motion.div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </>
  );
};

export default Skiper21;
