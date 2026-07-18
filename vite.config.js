import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// GitHub Pages serves a project site at /<repo>/, so the production build
// needs that base. Local dev/preview stay at "/".
const base = process.env.NODE_ENV === "production" ? "/macro-indicator-dashboard/" : "/";

export default defineConfig({
  base,
  plugins: [react(), tailwindcss()],
});
