import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test, afterEach } from "node:test";
import ts from "typescript";

async function moduleFrom(relative) {
  const source = await readFile(new URL(relative, import.meta.url), "utf8");
  const { outputText } = ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ES2022 } });
  return import(`data:text/javascript;base64,${Buffer.from(outputText).toString("base64")}`);
}
const { canChooseDate } = await moduleFrom("../lib/calendar.ts");
const { api, ApiError, dateKey, prettyDate, money, today } = await moduleFrom("../lib/api.ts");
const minimum = "2026-10-08";
const blocked = [{ check_in: "2026-11-10", check_out: "2026-11-13" }];
const originalFetch = globalThis.fetch;
afterEach(() => { globalThis.fetch = originalFetch; });

test("calendar permits checkout at occupied check-in and next check-in at checkout", () => {
  assert.equal(canChooseDate("2026-11-10", "2026-11-08", "", blocked, minimum), true);
  assert.equal(canChooseDate("2026-11-10", "", "", blocked, minimum), false);
  assert.equal(canChooseDate("2026-11-13", "", "", blocked, minimum), true);
});
test("calendar rejects crossing reservations and occupied nights", () => {
  for (const end of ["2026-11-11", "2026-11-12", "2026-11-13", "2026-11-14"]) {
    assert.equal(canChooseDate(end, "2026-11-08", "", blocked, minimum), false);
  }
  assert.equal(canChooseDate("2026-11-11", "", "", blocked, minimum), false);
});
test("calendar enforces past dates, 90 nights and 730 day horizon", () => {
  assert.equal(canChooseDate("2026-10-07", "", "", [], minimum), false);
  assert.equal(canChooseDate("2027-01-06", minimum, "", [], minimum), true);
  assert.equal(canChooseDate("2027-01-07", minimum, "", [], minimum), false);
  assert.equal(canChooseDate("2028-10-08", "", "", [], minimum), false);
});
test("date-only formatting does not parse stay dates as UTC timestamps", () => {
  assert.equal(dateKey(new Date(2027, 0, 2)), "2027-01-02");
  assert.equal(prettyDate("2027-01-02"), "2 Jan");
  assert.equal(prettyDate(""), "Add dates");
  assert.equal(today(), new Date(Date.now() + 330 * 60 * 1000).toISOString().slice(0, 10));
  assert.equal(money(19368), "₹19,368");
});
test("API carries selected identity, request payload and retry key", async () => {
  globalThis.fetch = async (url, options) => {
    assert.equal(url, "/api/bookings");
    assert.equal(options.headers["X-Demo-User"], "2");
    assert.equal(options.headers["Idempotency-Key"], "retry-key-123");
    assert.equal(options.cache, "no-store");
    assert.deepEqual(JSON.parse(options.body), { guests: 2 });
    return Response.json({ id: 5 }, { status: 201 });
  };
  assert.deepEqual(await api("/bookings", 2, "POST", { guests: 2 }, { headers: { "Idempotency-Key": "retry-key-123" } }), { id: 5 });
});
test("API exposes backend validation and conflict status", async () => {
  globalThis.fetch = async () => Response.json({ detail: "Dates unavailable" }, { status: 409 });
  await assert.rejects(api("/bookings", 1), (error) => error instanceof ApiError && error.status === 409 && error.message === "Dates unavailable");
  globalThis.fetch = async () => Response.json({ detail: [{ msg: "Invalid guests" }] }, { status: 422 });
  await assert.rejects(api("/bookings", 1), /Invalid guests/);
});
test("API reports offline and non-JSON failures without raw parser exceptions", async () => {
  globalThis.fetch = async () => { throw new TypeError("Failed to fetch"); };
  await assert.rejects(api("/listings", 1), /couldn’t connect/);
  globalThis.fetch = async () => new Response("Bad gateway", { status: 502 });
  await assert.rejects(api("/listings", 1), (error) => error instanceof ApiError && error.status === 502 && /unexpected response/.test(error.message));
});
test("API preserves cancellation so stale requests can be discarded", async () => {
  globalThis.fetch = async () => { throw new DOMException("Aborted", "AbortError"); };
  await assert.rejects(api("/listings", 1), { name: "AbortError" });
});


test("India date boundary rejects yesterday after local midnight", () => {
  const originalNow = Date.now;
  try {
    Date.now = () => Date.parse("2026-10-08T19:00:00Z");
    assert.equal(today(), "2026-10-09");
    assert.equal(canChooseDate("2026-10-08", "", "", [], today()), false);
    assert.equal(canChooseDate("2026-10-09", "", "", [], today()), true);
  } finally { Date.now = originalNow; }
});
