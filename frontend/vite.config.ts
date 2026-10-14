import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Vite loads this file by its default export.
export default defineConfig({
  plugins: [react()],
});
