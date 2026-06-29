/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        signal: {
          red: "#dc2626",
          yellow: "#ca8a04",
          green: "#16a34a",
        },
      },
    },
  },
  plugins: [],
};
