/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Control-tower surfaces, darkest to lightest.
        ink: {
          950: "#0a0e14", // page background
          900: "#12171f", // recessed panels, table stripes
          800: "#1a1f26", // cards and raised surfaces
          700: "#262c38", // hairlines and dividers
        },
        // Single high-visibility accent. `primary` is kept as an alias so any
        // screen still referencing the old scale keeps working.
        accent: {
          DEFAULT: "#ff6a00",
          hover: "#ff8533",
          soft: "rgba(255, 106, 0, 0.12)",
        },
        primary: {
          50: "rgba(255, 106, 0, 0.08)",
          100: "rgba(255, 106, 0, 0.14)",
          600: "#ff6a00",
          700: "#e65f00",
          800: "#cc5400",
        },
        success: "#10b981",
        warning: "#ff6a00",
        error: "#ef4444",
        info: "#38bdf8",
      },
      fontFamily: {
        sans: ["'Plus Jakarta Sans'", "system-ui", "sans-serif"],
        heading: ["Rajdhani", "'Plus Jakarta Sans'", "sans-serif"],
        mono: ["'JetBrains Mono'", "ui-monospace", "monospace"],
      },
      boxShadow: {
        // The design leans on deep, soft drops rather than borders for lift.
        panel: "0 35px 60px -15px rgba(0, 0, 0, 0.7)",
      },
      borderRadius: {
        // The design language is square-edged; nothing should be pill-shaped
        // except deliberate `rounded-full` dots and avatars.
        DEFAULT: "0px",
      },
    },
  },
  plugins: [],
};
