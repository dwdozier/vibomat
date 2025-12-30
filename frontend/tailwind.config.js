/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        retro: {
          teal: '#50C8C6',
          pink: '#FF9AA2',
          cream: '#FFFDF5',
          chrome: '#E0E0E0',
          dark: '#2D3436',
          yellow: '#FFECB3'
        }
      },
      fontFamily: {
        display: ['Righteous', 'cursive'],
        body: ['Varela Round', 'sans-serif'],
      },
      boxShadow: {
        'retro': '4px 4px 0px 0px rgba(45, 52, 54, 1)',
        'retro-sm': '2px 2px 0px 0px rgba(45, 52, 54, 1)',
      }
    },
  },
  plugins: [],
}
