/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "#0D0D11",
        foreground: "hsl(var(--foreground) / <alpha-value>)",
        "muted-foreground": "hsl(var(--muted-foreground) / <alpha-value>)",
        surface: "#14141A",
        "surface-card": "#1A1A23",
        "surface-elevated": "#22222E",
        border: "rgba(255, 255, 255, 0.08)",
        "border-hover": "rgba(255, 255, 255, 0.16)",
        muted: "#888899",
        "muted-dark": "#555566",
        primary: {
          DEFAULT: "#F4F4F6",
          dark: "#0D0D11",
          accent: "#8B5CF6",
        },
        accent: {
          purple: "#A78BFA",
          amber: "#F59E0B",
          emerald: "#10B981",
          rose: "#F43F5E",
          blue: "#3B82F6",
        },
      },
      fontFamily: {
        display: ['var(--font-display)', 'Instrument Serif', 'serif'],
        sans: ['var(--font-body)', 'Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        serif: ['var(--font-display)', 'Instrument Serif', 'Newsreader', 'Playfair Display', 'Georgia', 'serif'],
        mono: ['"Google Sans"', '"Google Sans Text"', 'sans-serif'],
      },
      keyframes: {
        shimmer: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        },
        'pulse-slow': {
          '0%, 100%': { opacity: '0.4' },
          '50%': { opacity: '0.8' },
        },
        'word-reveal': {
          '0%': { transform: 'translateY(115%)', opacity: '0' },
          '100%': { transform: 'translateY(0%)', opacity: '1' },
        },
        'fade-slide-up': {
          '0%': { transform: 'translateY(24px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        'float-left-hand': {
          '0%, 100%': { transform: 'translateY(0px) rotate(0deg)' },
          '50%': { transform: 'translateY(-6px) rotate(-0.5deg)' },
        },
        'float-right-hand': {
          '0%, 100%': { transform: 'translateY(0px) rotate(0deg)' },
          '50%': { transform: 'translateY(6px) rotate(0.5deg)' },
        },
        'fade-rise': {
          'from': { opacity: '0', transform: 'translateY(24px)' },
          'to': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        shimmer: 'shimmer 2.5s infinite',
        'pulse-slow': 'pulse-slow 4s ease-in-out infinite',
        'word-reveal': 'word-reveal 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'fade-slide-up': 'fade-slide-up 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'fade-rise': 'fade-rise 0.8s ease-out both',
        'fade-rise-delay': 'fade-rise 0.8s ease-out 0.2s both',
        'fade-rise-delay-2': 'fade-rise 0.8s ease-out 0.4s both',
        'float-left': 'float-left-hand 6s ease-in-out infinite',
        'float-right': 'float-right-hand 6s ease-in-out infinite',
        'particle': 'particle-travel 3s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
