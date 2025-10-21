/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        text_main: "#FFFFFF",
        text_secondary: "#ADADAD",
        accent: "#D4AF37",
        background: "#232323",
        borderColor: "#4a4b4a",
      },
      fontFamily: {
        french: ["Inter", "ui-sans-serif", "system-ui"],
        arabic: ["Cairo", "sans-serif"],
      },
    },
  },
};
