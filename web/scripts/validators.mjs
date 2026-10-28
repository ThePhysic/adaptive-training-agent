import { readFile, writeFile } from "node:fs/promises";
import { Ajv2020 } from "ajv/dist/2020.js";
import standalone from "ajv/dist/standalone/index.js";
import assert from "node:assert/strict";

const contract = JSON.parse(
  await readFile("../contracts/openapi.json", "utf8"),
);
const ajv = new Ajv2020({
  strict: false,
  strictNumbers: true,
  ownProperties: true,
  validateFormats: false,
  code: { source: true, esm: true },
});
ajv.addSchema({ components: contract.components }, "contract");
const exports = {
  validateEvent: "StreamEvent",
  validateProfile: "SavedProfile",
  validateExercise: "CatalogRecord",
  validateError: "ApiError",
  validateApproval: "ApprovalResult",
  validateSavedPlan: "SavedPlan",
  validateSessionRecord: "SessionRecord",
  validateSubmission: "SessionSubmission",
  validateSubmissionError: "SubmissionError",
};
const limits = contract.paths["/api/v1/drafts/stream"].post["x-sse-limits"];
assert.deepEqual(
  limits,
  contract.paths["/api/v1/drafts/{candidate_id}/revise/stream"].post[
    "x-sse-limits"
  ],
);
const constants = {
  MAX_FRAME_BYTES: limits.maxFrameBytes,
  MAX_EVENTS: limits.maxEvents,
};
assert(
  Object.values(constants).every(
    (value) => Number.isSafeInteger(value) && value > 0,
  ),
);
const code =
  "// Generated from contracts/openapi.json. Do not edit.\n" +
  standalone(
    ajv,
    Object.fromEntries(
      Object.entries(exports).map(([key, value]) => [
        key,
        `contract#/components/schemas/${value}`,
      ]),
    ),
  ) +
  "\n" +
  Object.entries(constants)
    .map(([key, value]) => `export const ${key}=${value};`)
    .join("\n") +
  "\n";
const types =
  '// Generated from contracts/openapi.json. Do not edit.\nimport type { components } from "./api.generated.js";\n' +
  Object.entries(exports)
    .map(
      ([key, value]) =>
        `export function ${key}(data: unknown): data is components["schemas"]["${value}"];`,
    )
    .join("\n") +
  "\n" +
  Object.keys(constants)
    .map((key) => `export const ${key}: number;`)
    .join("\n") +
  "\n";
for (const [path, value] of [
  ["src/validators.generated.js", code],
  ["src/validators.generated.d.ts", types],
]) {
  if (process.argv.includes("--check")) {
    if ((await readFile(path, "utf8")) !== value)
      throw Error("Generated validators stale: " + path);
  } else await writeFile(path, value);
}
