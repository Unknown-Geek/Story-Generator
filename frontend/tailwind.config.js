module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      animation: {
        'spin-slow': 'spin 3s linear infinite',
        'fadeIn': 'fadeIn 0.3s ease-in',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        }
      },
      colors: {
        'neon-blue': '#00f3ff',
        'neon-purple': '#8000ff',
        'dark-bg': '#0a0a1f',
      },
      boxShadow: {
        'neon': '0 0 20px rgba(0, 243, 255, 0.3)',
        'neon-hover': '0 0 30px rgba(0, 243, 255, 0.5)',
      },
      textShadow: {
        'neon': '0 0 5px rgba(0, 243, 255, 0.3)', // Reduced intensity
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    // Add custom text shadow plugin
    function({ addUtilities }) {
      const newUtilities = {
        '.text-shadow-neon': {
          textShadow: '0 0 5px rgba(0, 243, 255, 0.3)', // Reduced intensity
        },
        '.text-shadow-neon-hover': {
          textShadow: '0 0 8px rgba(0, 243, 255, 0.4)', // Subtle hover effect
        },
      }
      addUtilities(newUtilities)
    },
  ],
}