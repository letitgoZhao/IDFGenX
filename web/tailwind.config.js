/** @type {import('tailwindcss').Config} */

export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,vue}"],
  theme: {
    container: {
      center: true,
    },
    extend: {
      colors: {
        // Night Mode (default dark)
        night: {
          bg: "#0a0a0a",
          panel: "#141414",
          panel2: "#1b1b1b",
          text: "#e8eef6",
          text2: "#a8b3c2",
          hint: "#6c7787",
          border: "rgba(255,255,255,0.08)",
          accent: "#00cfc8", // Electric Blue
          accent2: "#4af2a1", // Tech Green
          error: "#ff4d4f",
          warning: "#faad14",
          success: "#52c41a",
        },
        // Day Mode (light)
        day: {
          bg: "#f5f7fa",
          panel: "#ffffff",
          panel2: "#ffffff",
          text: "#1f2d3d",
          text2: "#52616b",
          hint: "#7b8a97",
          border: "rgba(0,0,0,0.08)",
          accent: "#00a8a3",
          error: "#d9363e",
          warning: "#d48806",
          success: "#389e0d",
        },
      },
      boxShadow: {
        night: "0 4px 12px rgba(0, 207, 200, 0.15)", // Soft glow for accent
        day: "0 2px 8px rgba(0, 0, 0, 0.05)", // Light shadow
      },
    },
  },
  plugins: [],
};
