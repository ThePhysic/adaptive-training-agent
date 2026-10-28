// Test processes cannot reach real providers, telemetry, DNS or sockets.
import net from "node:net";
import http from "node:http";
import https from "node:https";
import dns from "node:dns";
import dgram from "node:dgram";
const deny = () => {
  throw new Error("External I/O disabled in frontend tests");
};
globalThis.fetch = async () => deny();
net.Socket.prototype.connect = deny;
http.request = http.get = https.request = https.get = deny;
dns.lookup = deny;
dns.promises.lookup = async () => deny();
dgram.Socket.prototype.send = deny;
for (const name of Object.keys(dns).filter(
  (name) =>
    name.startsWith("resolve") ||
    ["lookup", "lookupService", "reverse"].includes(name),
)) {
  dns[name] = deny;
  if (name in dns.promises) dns.promises[name] = async () => deny();
  if (name in dns.Resolver.prototype) dns.Resolver.prototype[name] = deny;
  if (name in dns.promises.Resolver.prototype)
    dns.promises.Resolver.prototype[name] = async () => deny();
}
