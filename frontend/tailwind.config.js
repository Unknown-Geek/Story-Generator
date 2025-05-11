/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        "neon-blue": "#00f3ff",
        "neon-purple": "#8000ff",
        "dark-bg": "#070715",
      },
      boxShadow: {
        neon: "0 0 20px rgba(0, 243, 255, 0.1)",
        "neon-hover": "0 0 30px rgba(0, 243, 255, 0.2)",
        "neon-strong": "0 0 40px rgba(0, 243, 255, 0.3)",
      },
      animation: {
        fadeIn: "fadeIn 0.5s ease-out",
        pulse: "pulse 2s infinite",
        glow: "glow 2s infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        pulse: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.8" },
        },
        glow: {
          "0%, 100%": {
            boxShadow: "0 0 20px rgba(0, 243, 255, 0.1)",
            textShadow: "0 0 10px rgba(0, 243, 255, 0.3)",
          },
          "50%": {
            boxShadow: "0 0 30px rgba(0, 243, 255, 0.2)",
            textShadow: "0 0 15px rgba(0, 243, 255, 0.5)",
          },
        },
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
      },
      fontFamily: {
        inter: ["Inter", "sans-serif"],
        gilroy: ["Gilroy", "sans-serif"],
        jakarta: ['"Plus Jakarta Sans"', "sans-serif"],
      },
      // Custom scrollbar styling
      scrollbar: {
        width: "4px",
        track: "rgba(0, 243, 255, 0.05)",
        thumb: "rgba(0, 243, 255, 0.3)",
      },
    },
  },
  plugins: [
    require("@tailwindcss/forms"),
    function ({ addUtilities }) {
      addUtilities({
        ".backdrop-blur-sm": {
          "backdrop-filter": "blur(4px)",
        },
        ".backdrop-blur-md": {
          "backdrop-filter": "blur(8px)",
        },
        ".backdrop-blur-lg": {
          "backdrop-filter": "blur(12px)",
        },
        ".text-shadow-neon": {
          "text-shadow": "0 0 10px rgba(0, 243, 255, 0.3)",
        },
        ".scale-y-95": {
          transform: "scaleY(0.95)",
        },
        ".scale-y-100": {
          transform: "scaleY(1)",
        },
      });
    },
  ],
  safelist: [
    "animate-fadeIn",
    "animate-pulse",
    "animate-glow",
    "shadow-neon",
    "shadow-neon-hover",
    "shadow-neon-strong",
    "backdrop-blur-sm",
    "backdrop-blur-md",
    "backdrop-blur-lg",
    "scale-y-95",
    "scale-y-100",
  ],
};
