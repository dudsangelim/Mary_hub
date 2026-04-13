import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: "#f8fafc",
        ink: "#0f172a",
        accent: "#14532d",
        warm: "#f59e0b",
        danger: "#dc2626"
      }
    }
  },
  plugins: []
};

export default config;
