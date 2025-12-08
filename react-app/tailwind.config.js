/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          600: '#0052CC',
          700: '#003A99',
          800: '#002E7A',
        },
        secondary: {
          600: '#7C3AED',
          700: '#6D28D9',
        },
        success: '#059669',
        warning: '#D97706',
        error: '#DC2626',
        info: '#0284C7',
      },
    },
  },
  plugins: [],
}
