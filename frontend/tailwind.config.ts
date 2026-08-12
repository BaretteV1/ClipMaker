import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        reel: {
          bg: "#14120f",
          panel: "#1c1a16",
          line: "#332f28",
          text: "#eee8dc",
          dim: "#9a9284",
          amber: "#e8a33d",
          amberDim: "#8a6423",
          rec: "#d1453a",
        },
      },
      fontFamily: {
        display: ["'Space Grotesk'", "sans-serif"],
        mono: ["'IBM Plex Mono'", "monospace"],
      },
    },
  },
  plugins: [],
};
export default config;
