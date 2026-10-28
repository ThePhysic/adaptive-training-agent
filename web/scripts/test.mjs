import { build } from "esbuild";
import { readdir } from "node:fs/promises";
import { spawnSync } from "node:child_process";

const files = (await readdir("tests")).filter((name) =>
  /\.test\.tsx?$/.test(name),
);
await build({
  entryPoints: files.map((name) => `tests/${name}`),
  outdir: ".cache/tests",
  bundle: true,
  platform: "node",
  format: "esm",
  external: ["react", "react/*", "react-dom", "react-dom/*", "jsdom"],
  jsx: "automatic",
  target: "node24",
  outExtension: { ".js": ".mjs" },
});
const result = spawnSync(
  process.execPath,
  [
    "--import=./tests/offline.mjs",
    "--test",
    "--test-concurrency=1",
    ...files.map((name) => `.cache/tests/${name.replace(/\.tsx?$/, ".mjs")}`),
  ],
  { stdio: "inherit" },
);
process.exitCode = result.status ?? 1;
