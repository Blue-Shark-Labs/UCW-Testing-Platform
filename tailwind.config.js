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
