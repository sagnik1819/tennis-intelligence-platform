/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: {
          main: "#0B1220",
          secondary: "#111B2E",
          card: "#172338",
          cardHover: "#1E2D47"
        },
        tennis: {
          green: "#B7F34A",
          greenHover: "#A5E236",
          darkGreen: "#1B3311",
          volt: "#CCFF00"
        },
        cyanAccent: "#43C6AC",
        slateBorder: "#263449",
        textPrimary: "#F8FAFC",
        textSecondary: "#94A3B8",
        textMuted: "#64748B"
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        heading: ['Manrope', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace']
      }
    },
  },
  plugins: [],
}
