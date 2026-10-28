import test from "node:test";
import assert from "node:assert/strict";
import dns from "node:dns";
import dgram from "node:dgram";
import net from "node:net";
import https from "node:https";

test("routine test bootstrap blocks fetch, TCP, UDP, HTTP and alternate DNS paths", async () => {
  const denied = /External I\/O disabled/;
  await assert.rejects(fetch("https://external.invalid"), denied);
  assert.throws(() => net.connect(443, "198.51.100.1"), denied);
  assert.throws(() => https.get("https://external.invalid"), denied);
  assert.throws(() => dns.resolve4("external.invalid", () => {}), denied);
  await assert.rejects(dns.promises.resolve6("external.invalid"), denied);
  assert.throws(() => dns.resolveTxt("external.invalid", () => {}), denied);
  assert.throws(
    () => new dns.Resolver().resolveMx("external.invalid", () => {}),
    denied,
  );
  await assert.rejects(
    new dns.promises.Resolver().resolveSoa("external.invalid"),
    denied,
  );
  const socket = dgram.createSocket("udp4");
  try {
    assert.throws(() => socket.send("synthetic", 443, "198.51.100.1"), denied);
  } finally {
    socket.close();
  }
});
