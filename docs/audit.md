# Full-stack implementation and QA audit

Audit date: **8 October 2026**. This is an evidence log for the changes in this working tree. “Verified” is limited to the checks below and is not a production security certification.

## Baseline and preservation

- Initial `git status` was clean. The parent directory is an unrelated project; all implementation occurred under this `airbnb/` repository. No project database was reset.
- Read repository configuration, README, Next routes/components/API types, FastAPI endpoints, SQLite initialization/schema/seed, tests, Docker and Vercel configuration. The required framework/layout was already present.
- Used an isolated browser database at `.devtools/audit.sqlite`; it is ignored by Git. Browser-only sample interactions (one reservation, favorite and host listing create/edit/soft-delete) did not touch the public data. The audit reservation was cancelled before completion.
- Read the accessible public Airbnb homepage and visually compared its photo-forward grid, compact segmented search, category rail, typography, neutral palette, spacing, card ratio and rounded controls with the local app at narrow phone/tablet/desktop views. The reference screenshot was for private inspection only and is excluded from this source submission.

## Changes made

- Centralized UTC date-only booking rules, integer INR quotes, bounded search and server-side availability filtering.
- Added versioned additive SQLite migration for booking idempotency; DB triggers and indexes repeat overlap, capacity, money, date and historical immutability checks. Existing bookings remain intact. Local SQLite enables FKs; atomic writes use `BEGIN IMMEDIATE`.
- Added server-confirmed price matching and idempotent checkout retries; the UI prevents repeated submissions and retains the same key for the same stay. Per-user reservation data remains scoped; ownership applies to host CRUD.
- Hardened host listing input/ownership and capacity edits; photos/amenities replace transactionally; removals are soft-delete and blocked for upcoming confirmed stays.
- Improved search-state persistence, filter/pagination handling, cancellation/loading/error feedback, gallery navigation, broken-image fallback, calendar constraints, and keyboard dialog focus. Added frontend calendar/API tests and backend regression coverage.
- Added a local SVG app icon and updated README/API examples and requirement matrix. `frontend/package-lock.json` was repaired to agree with the manifest via clean `npm ci`.

## Automated checks actually run

From the repository root:

```text
python -m pytest backend/tests -q       62 passed in 3.23s
```

From `frontend/`:

```text
npm run lint                            passed (0 warnings)
npm run typecheck                      passed
npm test                                8 passed, 0 failed
npm run build                           passed (Next.js static production export)
npm audit --omit=dev                    0 known vulnerabilities
```

An earlier attempt to run npm scripts from the repository root failed because `package.json` is correctly located in `frontend/`; commands were rerun in the right directory. No test data was created in the normal backend database by pytest.

Backend regression evidence includes five overlap shapes, two adjacent boundaries, concurrent requests with one idempotency key, replay/change/cancel cases, invalid dates/capacities/prices, direct foreign-key and trigger bypass attempts, current-vs-historical price, identity scope, ownership, relationship replacement, filtered pagination/date exclusion, fresh startup preserving rows, and SQLite FK enforcement.

## Local browser observations

The production static export was served with FastAPI at `http://127.0.0.1:8002/` against `.devtools/audit.sqlite`.

- Explored seeded cards, typed `Himachal`, chose the Cabins category and applied combined type/amenity/price filters. Results/counts were consistent. Location/category remained after refresh.
- Opened a listing, displayed its gallery and availability calendar, and selected October 20–22, 2026; the seeded October 22–25 booking allowed check-out on its arrival boundary. The quote was 2 × ₹6,850 + ₹900 cleaning + ₹1,918 service = **₹16,518**. Mock checkout returned **AB000005** with the same server total. Double-click/retry was covered by API tests. Refresh retained the confirmation/trip; cancellation removed the stay from blocking availability. Backend restart preserved isolated data.
- Saved a home, refreshed, and switched profiles; its saved state remained attached to the original user.
- As Ananya, host dashboard displayed owned homes/bookings. UI form rejected malformed photo URL and invalid nightly price. A valid test home was created, price and amenities edited, then soft-deleted in UI; the toast/dashboard count changed and API record was preserved as removed.
- At approximately 390 px, measured document width did not exceed the visible phone viewport; two-column photo cards, horizontally scrolling categories and compact bottom navigation rendered. At approximately 768 px, no horizontal overflow; cards and dashboard resized cleanly. Desktop layout was inspected at its normal wide viewport. Keyboard testing confirmed modal focus stays inside with Tab/Shift+Tab and returns to the dialog controls. Screenshots retained: [mobile explore](screenshots/mobile-explore.jpg), [mobile checkout](screenshots/mobile-checkout.jpg), and [wide demo preview](live-demo.jpg).
- Invalid image fallback is visible when a URL returns an unusable image. Local server logs show normal API responses and static chunk delivery. An initial browser request to `/favicon.ico` returned 404; explicit `/favicon.svg` metadata and asset were added, then included in the final production build. Browser console was not available for an exhaustive post-fix console audit.

## Deployment readiness

- Existing repository and deployed URL are [public source](https://github.com/gursimarsingh1001/airbnb-fullstack-marketplace) and [Vercel demo](https://airbnb-fullstack-marketplace.vercel.app). Commit `84548fb` was pushed to `main`, then Vercel reported production deployment `4jsgqLvFj7CBUAwSfDYcBiLozGdN` as **READY** and aliased the stable demo URL. Its Next and Python builds passed. The live app rendered the database-backed explore grid; clicking Cabins returned the two seeded Himachal cabins with correct titles, prices, and result count, verifying same-origin backend connectivity through the actual UI. No production records were modified.
- Browser tooling blocked direct navigation to `/api/health` (`ERR_BLOCKED_BY_CLIENT`) and Vercel CLI `curl` did not return before its network wait, so a direct live API status/body check was not completed. The hosted UI's listing fetch and filter response succeeded; the API itself is fully covered by 62 local tests.
- `vercel.json` puts exported Next files and Python FastAPI function on one origin. Vercel serverless SQLite durability depends on private Vercel Blob snapshots with ETag compare-and-swap (`BLOB_READ_WRITE_TOKEN`, `DATABASE_BLOB_ENABLED=1`); ephemeral function disk alone is not durable. This is configured for the existing **free Hobby** demo and uses quotas; no paid Render/persistence plan is requested. Local SQLite/Docker uses a persistent local file/volume.
- Source ignores `.env*`, `.vercel/`, local databases and `.devtools/`; `.vercelignore` excludes local docs/tests from the function deployment. `.env.local` contains deployment-local secrets and is ignored; it was not printed in this audit or staged intentionally.

## Unverified or bounded checks

- A direct public API endpoint check was blocked by browser-tool policy and CLI network timeout; public API behavior is indirectly verified through successful live explore and filter requests. Public live state was not used for destructive testing.
- Responsive layouts were visually exercised at ~390/768 px and wide desktop inspected; a precise 1440 px overflow assertion was not separately recorded. Tablet and desktop screenshots were inspected but only the preexisting wide preview and two phone captures are retained.
- Keyboard dialog behavior was tested. A full screen-reader audit, automated WCAG contrast/axe scan, and exhaustive focus review of every route were not run.
- Browser-level unknown-ID direct URL handling, all date picker gestures at all sizes, and image accessibility/network failure permutations were not exhaustively traversed; relevant API/domain regressions and fallback states are tested.
- At the original 8 October audit snapshot, cloud photo upload and guest-submitted reviews were not yet implemented. Real authentication, payments, identity checks, host messaging and live pricing map remain mocked or out of scope. The public demo identity header can be impersonated; it is suitable only for fictional evaluation data.

## Optional bonus feature follow-up (9 October 2026)

- Added a completed-stay review path from Trips: only the owning guest can review a confirmed reservation after checkout, once. SQLite migration v2 adds the nullable unique booking relationship and a trigger for direct-write enforcement. The browser flow was exercised against the isolated `.devtools/bonus-qa.sqlite`; it showed a success toast and changed the trip to “Review shared.” No public listing or production reservation was changed.
- Added server-side private Vercel Blob photo upload and an authenticated same-origin image proxy. PNG/JPEG/WebP bytes, MIME signatures, 3 MB maximum, host role, generated names, and private Blob request headers are tested. Storage HTTP behavior is mocked in automated tests. A real upload was not attempted, to avoid consuming the shared Blob quota; deployment configuration provides the existing Blob token.
- Added account-menu dark mode with a stored preference. The local browser showed the dark palette and retained it after reload. Existing CSS responsive breakpoints continue to cover mobile/tablet/desktop.
- The interactive approximate-pin map, Superhost badge, rating average/count aggregation, and responsive layouts were already present and verified in the earlier audit. These remain listed in [the requirement matrix](REQUIREMENTS.md).
- Latest checks after these changes: **68 backend tests passed**, **8 frontend tests passed**, `npm run typecheck`, `npm run lint`, and `npm run build` all passed. Image-storage integration against Vercel and a fresh hosted deployment of this bonus update are not yet verified at this point in the audit.
- External illustrative image availability and the free hosting quota remain outside source-level guarantees. Serverless whole-file snapshot storage is for the small assignment dataset only.

See [REQUIREMENTS.md](REQUIREMENTS.md) for feature-by-feature status and [README.md](../README.md) for setup, schema, pricing, API, deployment and demonstration instructions.
