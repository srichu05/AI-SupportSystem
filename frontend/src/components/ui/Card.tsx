import React from 'react';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  elevated?: boolean;
  interactive?: boolean;
  className?: string;
}

export const Card: React.FC<CardProps> = ({
  children,
  elevated = false,
  interactive = false,
  className = '',
  ...props
}) => {
  return (
    <div
      className={`rounded-2xl border transition-all duration-200 ${
        elevated ? 'glass-elevated' : 'glass-panel'
      } ${
        interactive
          ? 'hover:border-white/20 hover:shadow-lg hover:shadow-black/40 cursor-pointer'
          : ''
      } ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};
