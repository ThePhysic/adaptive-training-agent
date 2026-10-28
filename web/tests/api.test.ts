import { test } from "node:test";
import assert from "node:assert/strict";
import { BrowserApi, HttpFailure } from "../src/api.js";
import {
  profile,
  response,
  success,
  catalog,
  candidate,
  plan,
} from "./fixtures.js";

const signal = new AbortController().signal;
function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

test("explicit Save uses PUT and optimistic revision; profile/catalog reads never save", async () => {
  const calls: { path: unknown; options: RequestInit | undefined }[] = [];
  const api = new BrowserApi(async (path, options) => {
    calls.push({ path, options });
    return json(
      String(path).includes("cursor=")
        ? []
        : String(path).includes("exercises")
          ? catalog
          : profile,
    );
  });
  assert.equal((await api.profile("synthetic-b", signal))?.revision, 1);
  await api.catalog("synthetic-b", signal);
  await api.save("synthetic-b", profile.preferences, 1, signal);
  assert.equal(calls.at(-1)!.options!.method, "PUT");
  assert.equal(
    JSON.parse(calls.at(-1)!.options!.body as string).expected_revision,
    1,
  );
  assert(calls.slice(0, -1).every((call) => call.options!.method === "GET"));
  assert(
    calls.every(
      (call) =>
        (call.options!.headers as Record<string, string>)[
          "X-Synthetic-Principal"
        ] === "synthetic-b",
    ),
  );
  assert(
    calls.every(
      (call) =>
        call.options!.credentials === "omit" &&
        call.options!.redirect === "error",
    ),
  );
});

test("initial and explicit revision use direct POST without reconnection", async () => {
  const requests: { path: unknown; options: RequestInit | undefined }[] = [];
  const api = new BrowserApi(async (path, options) => {
    requests.push({ path, options });
    return response(success(requests.length === 1 ? 1 : 2));
  });
  await api.generate(
    "synthetic-a",
    { profile_revision: 1, preferences_text: "" },
    signal,
    () => {},
  );
  await api.generate(
    "synthetic-a",
    { profile_revision: 1, preferences_text: "" },
    signal,
    () => {},
    candidate,
  );
  assert.equal(requests[0].path, "/api/v1/drafts/stream");
  assert.equal(
    requests[1].path,
    "/api/v1/drafts/fixture-candidate/revise/stream",
  );
  assert(requests.every((r) => r.options!.method === "POST"));
  assert.deepEqual(
    JSON.parse(requests[1].options!.body as string).candidate,
    candidate,
  );
  assert.equal(requests.length, 2);
});

test("HTTP errors and incomplete EOF make one request and expose only typed failures", async () => {
  let calls = 0;
  const api = new BrowserApi(async () => {
    calls++;
    return json({ code: "stale_profile", retryable: false }, 409);
  });
  await assert.rejects(
    api.generate(
      "synthetic-a",
      { profile_revision: 1, preferences_text: "" },
      signal,
      () => {},
    ),
    HttpFailure,
  );
  assert.equal(calls, 1);
  const incomplete = new BrowserApi(async () => {
    calls++;
    return response("");
  });
  await assert.rejects(
    incomplete.generate(
      "synthetic-a",
      { profile_revision: 1, preferences_text: "" },
      signal,
      () => {},
    ),
  );
  assert.equal(calls, 2);
});

test("bounded JSON, missing profile, and invalid server data", async () => {
  assert.equal(
    await new BrowserApi(async () =>
      json({ code: "not_found", retryable: false }, 404),
    ).profile("synthetic-a", signal),
    null,
  );
  for (const data of [
    { ...profile, owner_id: "synthetic-b" },
    { untrusted: "x".repeat(17000) },
    {},
  ]) {
    await assert.rejects(
      new BrowserApi(async () => json(data)).profile("synthetic-a", signal),
    );
  }
});

test("approval and owned readback/history use exact identities and no automatic retry", async () => {
  const saved = {
    approval: { plan_id: "saved-fixture", candidate },
    plan,
    versions: {
      profile_revision: 1,
      catalog_revision: "catalog-v1",
      validator_revision: "validator-v1",
    },
  };
  const calls: { path: unknown; body: unknown }[] = [];
  const api = new BrowserApi(async (path, options) => {
    calls.push({ path, body: options?.body });
    return json(
      options?.method === "POST"
        ? saved.approval
        : String(path).includes("?")
          ? [saved]
          : saved,
    );
  });
  const bound = { ...candidate, idempotency_key: "fixed-key" };
  assert.deepEqual(
    await api.approve("synthetic-a", bound, signal),
    saved.approval,
  );
  assert.deepEqual(JSON.parse(calls[0].body as string), bound);
  assert.deepEqual(
    await api.plan("synthetic-a", "saved-fixture", signal),
    saved,
  );
  assert.deepEqual(await api.history("synthetic-a", signal), [saved]);
  assert.equal(calls.length, 3);
  const forged = new BrowserApi(async () =>
    json({
      ...saved.approval,
      candidate: { ...candidate, candidate_id: "other" },
    }),
  );
  await assert.rejects(forged.approve("synthetic-a", bound, signal));
});
