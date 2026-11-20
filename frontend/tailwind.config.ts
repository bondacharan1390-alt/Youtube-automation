import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        studio: {
          50: "#f5f7fa",
          100: "#ebeef3",
          200: "#d2d9e4",
          300: "#a9b8cc",
          400: "#7b91b0",
          500: "#587196",
          600: "#44597a",
          700: "#374762",
          800: "#242f41",
          900: "#131924",
          950: "#0b0f16",
        },
        brand: {
          red: "#FF0000",
          crimson: "#DC2626",
          purple: "#7C3AED",
          indigo: "#4F46E5",
          cyan: "#06B6D4",
          amber: "#F59E0B",
          emerald: "#10B981",
        }
      },
    },
  },
  plugins: [],
};
export default config;
