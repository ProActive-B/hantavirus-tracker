/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,ts,tsx,md,mdx}'],
  theme: {
    extend: {
      colors: {
        // tiered-confidence palette
        confirmed: '#b91c1c',
        probable:  '#d97706',
        signal:    '#475569',
        // brand
        ink:    '#0b1220',
        paper:  '#fafaf7',
        accent: '#0f766e',
      },
      fontFamily: {
        sans: ['ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'Inter', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
    },
  },
};
