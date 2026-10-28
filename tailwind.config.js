/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/**/*.html"],
  theme: {
    extend: {
      colors: {
        app: {
          background: "#F3F8FC",
          divider: "#D9E4EF",
          primary: "#1769E0",
          secondary: "#6495ED",
          ternary: "#89CFF0",
          quaternary: "#6082B6",
          quinary: "#B6D0E2",
        },
        text: {
          primary: "#13213A",
        },
      },
      fontFamily: {
        roboto: ["Roboto", "sans-serif"],
      },
    },
  },
  plugins: [],
};
