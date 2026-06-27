import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#111827",
        graphite: "#1f2937",
        ocean: "#0f766e",
        mint: "#10b981",
        cyanline: "#22d3ee",
        amberline: "#f59e0b",
        paper: "#f8fafc",
      },
      boxShadow: {
        panel: "0 18px 50px rgba(15, 23, 42, 0.10)",
        glow: "0 0 0 1px rgba(34, 211, 238, 0.18), 0 18px 40px rgba(14, 116, 144, 0.14)",
      },
    },
  },
  plugins: [],
};

export default config;
