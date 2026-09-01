/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        night: {
          DEFAULT: "#1a1624",
          deep: "#120f18",
          raised: "#241f32",
          card: "#2c263b",
        },
        cream: {
          DEFAULT: "#f4ead5",
          dim: "#cbbfa6",
        },
        amber: {
          DEFAULT: "#e8a54b",
          deep: "#c4842f",
        },
        excellent: "#8fce9a",
        good: "#8fb8d6",
        fair: "#e0c36c",
        poor: "#d9a08c",
      },
      fontFamily: {
        display: ['"Syne"', "ui-sans-serif", "system-ui", "sans-serif"],
        body: ['"Figtree"', "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 18px 40px rgba(8, 6, 14, 0.35)",
      },
    },
  },
  plugins: [],
};
