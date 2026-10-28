import { build } from "esbuild";
import { copyFile, mkdir } from "node:fs/promises";

await mkdir("dist/assets", { recursive: true });
await build({
  entryPoints: ["src/main.tsx"],
  outfile: "dist/assets/app.js",
  bundle: true,
  format: "esm",
  platform: "browser",
  target: "es2024",
  jsx: "automatic",
  define: { "process.env.NODE_ENV": '"production"' },
  minify: true,
  logLevel: "info",
});
await copyFile("index.html", "dist/index.html");
