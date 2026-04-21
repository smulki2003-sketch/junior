/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["Space Grotesk", "sans-serif"],
        body: ["IBM Plex Sans", "sans-serif"],
        mono: ["IBM Plex Mono", "monospace"],
      },
      colors: {
        base: "#07090F",
        surface: "#0E1118",
        elevated: "#161B27",
        hover: "#1E2336",
        blue: "#3B82F6",
        emerald: "#10B981",
        amber: "#F59E0B",
        danger: "#EF4444",
        purple: "#8B5CF6",
        cyan: "#06B6D4",
      },
      fontSize: {
        data: ["13px", { lineHeight: "1.4" }],
      },
    },
  },
  plugins: [],
};

