import React from 'react';
import { IssueCoverageStatus, GuardrailVerdict } from '../../types';

interface BadgeProps {
  children?: React.ReactNode;
  variant?: 'default' | 'outline' | 'success' | 'warning' | 'danger' | 'info' | 'purple' | 'accent';
  status?: IssueCoverageStatus;
  verdict?: GuardrailVerdict;
  size?: 'sm' | 'md';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  status,
  verdict,
  size = 'md',
  className = '',
}) => {
  // Restrained professional palette: #0D0F12 background, #292E36 borders, #8BA7D9 accent
  let styleClasses = 'bg-[#181C22] text-[#9299A5] border-[#292E36]';

  if (verdict === 'PASSED') {
    styleClasses = 'bg-[#162620] text-[#72B095] border-[#234235]';
  } else if (verdict === 'FLAGGED') {
    styleClasses = 'bg-[#261616] text-[#D97373] border-[#4A2525]';
  } else if (status) {
    switch (status) {
      case 'covered':
        styleClasses = 'bg-[#162620] text-[#72B095] border-[#234235]';
        break;
      case 'partially_covered':
        styleClasses = 'bg-[#272016] text-[#D3A365] border-[#483A24]';
        break;
      case 'uncovered':
        styleClasses = 'bg-[#181C22] text-[#9299A5] border-[#292E36]';
        break;
      case 'prohibited':
        styleClasses = 'bg-[#261616] text-[#D97373] border-[#4A2525]';
        break;
      case 'conflict':
        styleClasses = 'bg-[#272016] text-[#D3A365] border-[#483A24]';
        break;
      case 'needs_human_review':
        styleClasses = 'bg-[#1A2230] text-[#8BA7D9] border-[#2B3952]';
        break;
    }
  } else {
    switch (variant) {
      case 'success':
        styleClasses = 'bg-[#162620] text-[#72B095] border-[#234235]';
        break;
      case 'warning':
        styleClasses = 'bg-[#272016] text-[#D3A365] border-[#483A24]';
        break;
      case 'danger':
        styleClasses = 'bg-[#261616] text-[#D97373] border-[#4A2525]';
        break;
      case 'info':
      case 'accent':
      case 'purple':
        styleClasses = 'bg-[#1A2230] text-[#8BA7D9] border-[#2B3952]';
        break;
      case 'outline':
        styleClasses = 'bg-transparent text-[#9299A5] border-[#292E36]';
        break;
      default:
        styleClasses = 'bg-[#181C22] text-[#9299A5] border-[#292E36]';
        break;
    }
  }

  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-0.5 text-xs';

  let label = children;
  if (!label && status) {
    label = status.replace(/_/g, ' ');
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-medium rounded-md border tracking-normal ${sizeClasses} ${styleClasses} ${className}`}
    >
      {label}
    </span>
  );
};
