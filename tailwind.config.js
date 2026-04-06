/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/renderer/src/**/*.{js,ts,jsx,tsx}', './src/renderer/index.html'],
  theme: {
    extend: {
      colors: {
        surface: '#1a1a1a',
        panel: '#242424',
        border: '#333333',
        muted: '#888888',
      },
    },
  },
  plugins: [],
}
