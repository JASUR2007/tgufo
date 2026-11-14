/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        yt: {
          red: '#ff0000',
          dark: '#0f0f0f',
          paper: '#212121',
          hover: '#272727',
          border: '#3f3f3f',
          text: '#f1f1f1',
          subtext: '#aaaaaa'
        }
      }
    },
  },
  plugins: [],
}
