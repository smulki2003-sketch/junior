/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["Syne", "sans-serif"],
        body: ["DM Sans", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      colors: {
        base: "#0A0C14",
        surface: "#12151F",
        elevated: "#1C2030",
        primary: "#6C63FF",
        coral: "#FF6584",
        teal: "#00D4AA",
        amber: "#FFB547",
      },
      backdropBlur: { xs: "4px" },
      boxShadow: {
        glow: "0 0 28px rgba(108,99,255,0.45)",
        "glow-teal": "0 0 20px rgba(0,212,170,0.35)",
      },
      animation: {
        "pulse-glow": "pulseGlow 2s ease-in-out infinite",
        shimmer: "shimmer 1.4s infinite linear",
      },
      keyframes: {
        pulseGlow: {
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(108,99,255,0.15)" },
          "50%": { boxShadow: "0 0 0 10px rgba(108,99,255,0)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-400px 0" },
          "100%": { backgroundPosition: "400px 0" },
        },
      },
    },
  },
  plugins: [],
};

