/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Warm Sanctuary palette
        canvas: '#F6F1E7',     // warm cream page background
        surface: '#FFFFFF',    // cards
        warmth: '#FBF7F0',     // subtly tinted section background
        ink: '#2C2A24',        // primary text (warm near-black)
        'ink-soft': '#6E6658', // secondary text
        'ink-faint': '#9A917F',// tertiary / muted
        line: '#E9E1D3',       // borders
        sage: {
          DEFAULT: '#4F7355',  // primary (growth & life)
          dark: '#3E5D44',
          light: '#7E9D80',
          soft: '#E9F0E8',
        },
        gold: {
          DEFAULT: '#C39A4A',  // accent (warm, sacred)
          soft: '#F4ECD7',
        },
        clay: {
          DEFAULT: '#BE6E47',  // gentle "needs attention" tone (not alarming red)
          soft: '#F6E5DA',
        },
      },
      fontFamily: {
        serif: ['Fraunces', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        soft: '0 1px 2px rgba(44,42,36,0.04), 0 8px 24px rgba(44,42,36,0.06)',
        lift: '0 2px 4px rgba(44,42,36,0.05), 0 16px 40px rgba(44,42,36,0.10)',
      },
      borderRadius: {
        '2xl': '1.1rem',
        '3xl': '1.5rem',
      },
    },
  },
  plugins: [],
}
