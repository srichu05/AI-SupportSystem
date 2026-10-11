import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'success';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
  icon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  children,
  icon,
  className = '',
  disabled,
  ...props
}) => {
  const baseStyle =
    'relative inline-flex items-center justify-center font-medium rounded-lg transition-all duration-150 select-none disabled:opacity-40 disabled:cursor-not-allowed';

  let sizeStyle = 'px-3.5 py-1.5 text-xs';
  if (size === 'sm') sizeStyle = 'px-2.5 py-1 text-xs';
  if (size === 'lg') sizeStyle = 'px-5 py-2.5 text-sm';

  let variantStyle = 'bg-[#8BA7D9] text-[#0D0F12] hover:bg-[#9BB7E9] active:scale-[0.99] font-semibold';
  if (variant === 'secondary') {
    variantStyle =
      'bg-[#181C22] text-[#E8EAED] hover:bg-[#20252D] border border-[#292E36] active:scale-[0.99]';
  } else if (variant === 'outline') {
    variantStyle =
      'bg-transparent text-[#9299A5] hover:text-[#E8EAED] border border-[#292E36] hover:bg-[#181C22] active:scale-[0.99]';
  } else if (variant === 'ghost') {
    variantStyle = 'bg-transparent text-[#9299A5] hover:text-[#E8EAED] hover:bg-[#181C22]';
  } else if (variant === 'danger') {
    variantStyle =
      'bg-[#261616] text-[#D97373] hover:bg-[#331C1C] border border-[#4A2525] active:scale-[0.99]';
  } else if (variant === 'success') {
    variantStyle =
      'bg-[#162620] text-[#72B095] hover:bg-[#1F362D] border border-[#234235] active:scale-[0.99]';
  }

  return (
    <button
      className={`${baseStyle} ${sizeStyle} ${variantStyle} ${className}`}
      disabled={disabled}
      {...props}
    >
      {icon && <span className="mr-1.5 inline-flex items-center">{icon}</span>}
      {children}
    </button>
  );
};
