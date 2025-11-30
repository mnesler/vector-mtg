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
      themes: {
        preset: ["wintry", "modern", "crimson", "seafoam", "vintage"],
        custom: [
          {
            name: "miami",
            properties: {
              // Base colors - Ocean blues to sunset pinks
              "--color-primary-50": "252 231 243",
              "--color-primary-100": "251 207 232",
              "--color-primary-200": "249 168 212",
              "--color-primary-300": "244 114 182",
              "--color-primary-400": "236 72 153",
              "--color-primary-500": "219 39 119",
              "--color-primary-600": "190 24 93",
              "--color-primary-700": "157 23 77",
              "--color-primary-800": "131 24 67",
              "--color-primary-900": "112 26 59",

              // Secondary - Turquoise/Teal ocean colors
              "--color-secondary-50": "240 253 250",
              "--color-secondary-100": "204 251 241",
              "--color-secondary-200": "153 246 228",
              "--color-secondary-300": "94 234 212",
              "--color-secondary-400": "45 212 191",
              "--color-secondary-500": "20 184 166",
              "--color-secondary-600": "13 148 136",
              "--color-secondary-700": "15 118 110",
              "--color-secondary-800": "17 94 89",
              "--color-secondary-900": "19 78 74",

              // Tertiary - Coral/Orange sunset
              "--color-tertiary-50": "255 247 237",
              "--color-tertiary-100": "255 237 213",
              "--color-tertiary-200": "254 215 170",
              "--color-tertiary-300": "253 186 116",
              "--color-tertiary-400": "251 146 60",
              "--color-tertiary-500": "249 115 22",
              "--color-tertiary-600": "234 88 12",
              "--color-tertiary-700": "194 65 12",
              "--color-tertiary-800": "154 52 18",
              "--color-tertiary-900": "124 45 18",

              // Surface colors - Light and airy
              "--color-surface-50": "248 250 252",
              "--color-surface-100": "241 245 249",
              "--color-surface-200": "226 232 240",
              "--color-surface-300": "203 213 225",
              "--color-surface-400": "148 163 184",
              "--color-surface-500": "100 116 139",
              "--color-surface-600": "71 85 105",
              "--color-surface-700": "51 65 85",
              "--color-surface-800": "30 41 59",
              "--color-surface-900": "15 23 42",
            },
          },
        ],
      },
    }),
  ],
  darkMode: "class",
};
export default config;
