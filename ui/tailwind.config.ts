import type { Config } from "tailwindcss";
import { skeleton } from "@skeletonlabs/tw-plugin";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [
    skeleton({
      themes: { preset: ["skeleton", "modern", "crimson"] },
    }),
  ],
  darkMode: "class",
};
export default config;
