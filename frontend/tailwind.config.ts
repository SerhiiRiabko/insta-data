import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Design brief palette — Monte-Shop-Price
        brand: {
          accent: '#0b6e4f',      // Primary green
          deep: '#0f3d2e',        // Deep green (ink)
          cheapest: '#05603a',    // Cheapest text
          cheapestBg: '#d8f3e3',  // Cheapest cell background
          cheapestHeaderBg: '#eafaf1', // Cheapest column header
          mint: '#edf6f1',        // Section background (Var C)
          mintLight: '#f4faf7',   // Split panel (Var B)
          textMuted: '#52736a',   // Normal price text
          textHint: '#94aea3',    // Units, captions
          textSubtle: '#6b8a7d',  // Labels
          textMutedAlt: '#7d9a8d',// Timestamps
          border: '#e3eee8',      // Card border
          hairline: '#eef4f1',    // Row dividers
          hairlineDark: '#d9e7df',// Header dividers
          headerBg: '#f6faf8',    // Table header background
          white: '#ffffff',
          // Store colors
          storeAroma: '#e11d48',
          storeVoli: '#2563eb',
          storeHdl: '#d97706',
          storeIdea: '#0891b2',
        },
        // Gradients (can use with bg-gradient-to-*)
        emerald: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#145231',
        },
      },
      fontFamily: {
        // Design brief typography
        jakarta: ['"Plus Jakarta Sans"', 'sans-serif'],
        space: ['"Space Grotesk"', 'monospace'],
        sans: ['"Plus Jakarta Sans"', 'sans-serif'],
        mono: ['"Space Grotesk"', 'monospace'],
      },
      fontSize: {
        // Design brief typography scale
        xs: '0.75rem',        // 12px
        sm: '0.875rem',       // 14px
        base: '1rem',         // 16px
        lg: '1.125rem',       // 18px
        xl: '1.25rem',        // 20px
        '2xl': '1.5rem',      // 24px (tableTitle)
        '3xl': '2rem',        // 32px
        // Heading sizes
        h1: '3.625rem',       // 58px (Var A)
        'h1-b': '3.125rem',   // 50px (Var B)
        'h1-c': '3.25rem',    // 52px (Var C)
        // Special sizes from design brief
        tagline: '1.25rem',   // 20px
        nav: '0.875rem',      // 14px
        kicker: '0.8125rem',  // 13px
      },
      fontWeight: {
        light: '300',
        normal: '400',
        medium: '500',
        semibold: '600',
        bold: '700',
        extrabold: '800',
      },
      spacing: {
        // Design spacing from brief
        xs: '0.25rem',    // 4px
        sm: '0.5rem',     // 8px
        md: '1rem',       // 16px
        lg: '1.5rem',     // 24px
        xl: '2rem',       // 32px
        '2xl': '3rem',    // 48px
        '3xl': '4rem',    // 64px
        '44px': '44px',
        '56px': '56px',
      },
      borderRadius: {
        none: '0',
        xs: '0.25rem',
        sm: '0.5rem',
        md: '0.75rem',
        lg: '1rem',
        'pill': '999px',
        'card': '18px',
        'button': '12px',
        'badge': '7px',
        full: '9999px',
      },
      boxShadow: {
        none: 'none',
        sm: '0 1px 3px rgba(0,0,0,.08)',
        md: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        matrix: '0 28px 64px -30px rgba(6,78,59,0.4)',
        'search-a': '0 24px 50px -22px rgba(6,40,28,0.55)',
        'search-c': '0 20px 44px -20px rgba(6,40,28,0.5)',
        lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
        xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
      },
      letterSpacing: {
        tighter: '-0.05em',
        tight: '-0.025em',
        normal: '0em',
        wide: '0.025em',
        wider: '0.05em',
        widest: '0.1em',
        'uppercase': '0.08em',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-subtle': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1)',
        'transition-all': 'transition-all 120ms cubic-bezier(0.2,0,0,1)',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
};

export default config;