/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/**/*.html"],
  theme: {
    extend: {
      // Hex values from design-doc/design-document.md's colour palette (AA contrast checked there).
      colors: {
        brand: {
          DEFAULT: "#0047AB",
          mid: "#6082B6",
          light: "#B6D0E2",
          accent: "#6495ED",
          pale: "#89CFF0",
        },
      },
      fontFamily: {
        sans: ["Roboto", "sans-serif"],
      },
    },
  },
  plugins: [],
};
