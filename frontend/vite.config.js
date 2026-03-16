import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: "./",
  build: {
    // Streamlit component loader expects: kbo_sim/frontend/dist
    outDir: "../kbo_sim/frontend/dist",
    emptyOutDir: true,
  },
});
