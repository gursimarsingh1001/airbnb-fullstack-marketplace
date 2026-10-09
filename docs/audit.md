# Full-stack implementation and QA audit

Audit date: **9 October 2026**. This is a chronological evidence log; earlier sections describe earlier code states. The final submission verification at the end is the current status. “Verified” is limited to the checks listed and is not a production security certification.

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
- Latest checks after these changes: **68 backend tests passed**, **8 frontend tests passed**, `npm run typecheck`, `npm run lint`, and `npm run build` all passed. Image-storage integration against the live Vercel Blob store was not exercised; automated tests mock the Blob HTTP service to avoid consuming the shared quota.
- Pushed commit `f30235f` to the public repository and deployed it with Vercel CLI. Deployment `dpl_7PUA1f9jwkxF3CHHGm6dEVs9DfA5` reached **READY** and aliased https://airbnb-fullstack-marketplace.vercel.app. Vercel’s Next.js and Python builds passed. After a fresh browser reload, the public Trips page displayed the seeded completed stay with `Leave a review`; opening the modal showed the rating selector and review field. The profile menu showed the dark-mode control. No review was submitted to public data.
- External illustrative image availability and the free hosting quota remain outside source-level guarantees. Serverless whole-file snapshot storage is for the small assignment dataset only.

See [REQUIREMENTS.md](REQUIREMENTS.md) for feature-by-feature status and [README.md](../README.md) for setup, schema, pricing, API, deployment and demonstration instructions.

## Catalogue and discovery expansion (9 October 2026)

- Expanded to 44 fictional stays and 84 seed reviews. The additive `demo_content_versions` marker prevents repeat insertion; existing host edits, removals and reservations are preserved. New homes include photos, amenities, prices, capacity and approximate coordinates.
- Added photo destination shortcuts and a hosting invitation. Added server-side recommended/price/rating sorting with stable ID tie-breakers, applied before pagination and retained in search state.
- Map fetches every matching result page with cancellation/error handling. Local browser displayed 44 matches and 40 Indian homes, including stays outside grid page one.
- Local browser verified ascending prices, map results, and layouts at 390 and 768 pixels without horizontal document overflow. Desktop imagery inspected. Fixed a narrow-layout rule that would hide the new sort control.
- Real deployed cloud upload: POST `/api/host/photos` returned 201, image proxy returned 200, and downloaded bytes matched the original 233,700-byte demo JPEG exactly. One small QA image remains in the existing free Blob store; no listing or booking was modified. Earlier unverified-upload notes are historical.
- Checks: 70 backend tests, 8 frontend tests, lint, TypeScript and production build passed. New regressions cover sort/filter/pagination ordering and safe repeated catalogue upgrades.
- Guest and host remain in one application using explicitly labelled demo profiles. Real password authentication is not required by the assignment and is not implemented.

## 2026-10-09: refresh persistence, India dates and 240-home catalogue

- Added local-storage persistence for search drafts/applied filters, per-user/per-listing stay selections and per-host unfinished listing forms. Successful bookings/listings remain server-persisted. Cancelling a host form discards its draft; browser storage is device-specific and clearing it removes drafts.
- Aligned browser, FastAPI and SQLite validation to Asia/Kolkata calendar dates. Added a migration for existing database triggers and regression tests for the UTC/India midnight boundary. Yesterday cannot be a check-in date.
- Added a one-time, non-destructive expansion to 240 fictional homes (280 seed reviews). It reuses illustrative gallery photos with varied covers, prices and approximate positions. Existing reservations and host edits are retained; existing catalogue removals can make totals differ from a fresh seed.
- Added illustrative portraits for demo profiles, hosts and reviewers, with initials fallback. Added compact sticky homepage search and responsive refinements.
- Local checks: 72 backend tests passed; 9 frontend tests passed; lint, TypeScript and production build passed.
- Browser checks: desktop 1440x900, tablet 768x1024 and mobile 390x844 explore layouts inspected; no horizontal document overflow. Compact search stayed at the top while scrolling. Destination draft restored after refresh. Listing dates 20–23 October and 3 guests restored with a fresh server quote. 8 October disabled when India date was 9 October. Host title/description restored after refresh in a mobile form. Map showed 240 matching homes, regional grouped pins and mobile preview. No console errors captured during these local checks.
- This is targeted verification of the changed flows, not exhaustive testing of every device or browser. Earlier audit sections describe earlier releases and their former UTC policy.

Deployment verification: published to https://airbnb-fullstack-marketplace.vercel.app/ and pushed to the public GitHub repository. Live health returned SQLite, booking_today 2026-10-09 and Asia/Kolkata. Live catalogue returned 239 active homes (prior removals preserved). Browser confirmed compact header top=0 and height=77px after scroll, with no captured console errors. No production bookings were created during this check.

## Destination discovery and map follow-up

Added five inspiration themes with searchable destination links. Added 32 fictional destinations through idempotent catalogue-v4, giving 272 homes and 312 reviews on a fresh seed. Coverage now includes central/eastern/northeastern India, Ladakh, Andamans and three additional countries; this is representative demo coverage, not exhaustive real inventory. Existing edits, removals and bookings remain untouched.

Map country selection now has a visible label and per-country counts. Nearby homes use compact count circles, with price pins when zoomed in. Property previews appear only after selection and can be dismissed. Verified destination theme switching and Kathmandu search, country selection to Thailand, mobile India map at 390px with no horizontal overflow, and cluster zoom. No console errors captured in these local checks. Backend: 73 tests passed. Frontend: 9 tests passed; lint and production build including TypeScript passed.

## Animated header follow-up

Header-only refinement in Marketplace.tsx and globals.css: one shared form morphs over 300ms with cubic-bezier(0.2,0,0,1), passive/rAF scroll handling and 70px/40px hysteresis. Width, height, position, padding, separators and labels transition; navigation fades/translates and becomes inert. Reserved flow space keeps content stationary; reduced-motion preference disables transitions. Phone layout retains its existing expanded controls.

Verified locally: initial scrollY=0; slow scrolling (expanded at45, compact at81, stays compact at54); fast and repeated up/down scrolling; return to top restoring850px search; expanded and compact calendar actions; compact destination submission returning Goa stays; desktop1440, tablet768, mobile390 screenshots inspected. Main content document offset stayed288px before/after morph. No console errors captured. Frontend lint, nine tests, and production build/TypeScript passed. No reference recording was attached, so behavior follows the written specification rather than a frame-by-frame comparison.

## Historical evaluator-style audit checkpoint (9 October 2026)

This checkpoint records the 25-category review at commit `d933fd1` plus the focused GET-retry change. It is superseded by the final verification at the end of this file. A green status means the behavior was implemented and exercised by the listed evidence, not that the entire application is certified or production-secure.

| # | Area | Status | Evidence and limits |
|---:|---|:---:|---|
| 1 | Home/search | ✅ | The latest isolated QA seed returned 49 active homes (48 curated plus the preserved review-demo home). The browser showed photo/title/location/price/rating cards, segmented destination/date/guest search, category rail and pagination. |
| 2 | Filters | ✅ | Category and combined category/location search were exercised in the browser; clearing filters restored the catalogue. Source and backend regressions cover price, type, amenities, guest/date, and pagination combinations. |
| 3 | Listing detail | ✅ | Direct local detail route displayed the gallery, description, location, host, amenities, rating/reviews, calendar and quote controls. The deployed `#listing/1` page also loaded its gallery, review panel, host details, availability and map in a read-only smoke check. |
| 4 | Availability | ✅ | Local calendar marked past and booked nights unavailable; selected check-in/check-out and guest count survived refresh. Backend tests cover overlap boundaries and availability filtering. |
| 5 | Booking validation | ✅ | 82 backend tests passed at this checkpoint, including invalid/past dates, capacity, missing or removed homes, overlap shapes, back-to-back stays, concurrent attempts, ownership, quote changes and idempotency. |
| 6 | Mock checkout | ✅ | Completed a local two-night home reservation for ₹13,212 (₹5,400 × 2 + ₹900 cleaning + ₹1,512 service); the confirmed summary matched. UI states that checkout is a demo and collects no payment credentials. |
| 7 | My Trips | ✅ | The home booking plus experience and service confirmations appeared under the guest profile, survived a browser refresh, and stayed scoped from the host profile. One transient first-read connection failure was observed during a profile change; retry loaded the records. The API client now safely retries one failed GET once; a frontend API regression test verifies this behavior without replaying writes. Profile switching was rechecked after the fix. |
| 8 | Database persistence | ✅ | The test browser used isolated `.devtools/evaluator-20261009.sqlite`; seeded rows, bookings, favorite and soft-deleted test listing were retained. Existing backend regressions verify persistence across app initialization/restart. The public database was not modified. |
| 9 | Host CRUD | ✅ | In the isolated local database, created a listing through the host form, edited its price and details, then soft-deleted it through the UI. Host ownership and invalid input cases are covered by direct API tests. |
| 10 | Host dashboard | ✅ | The host home dashboard showed owned listings and reservations; experience and service provider tabs showed their seeded and test bookings. The temporary home was removed through soft delete and did not orphan reservation history. |
| 11 | Wishlist | ✅ | A listing was saved as the guest, remained saved after refresh, and was absent after switching to a different profile. API tests enforce per-user scope and prevent duplicate rows. |
| 12 | Experiences | ✅ | Local browse rendered seeded offers, category/search controls, pagination and details; the booking detail exposed available session times and capacity. |
| 13 | Experience booking | ✅ | Completed a local experience booking; confirmation `ACT3` and its ₹1,980 server total appeared in Trips and the host’s reservations. |
| 14 | Services | ✅ | Local service browse, category/filter controls, detail page and host service dashboard were exercised. |
| 15 | Service booking | ✅ | Completed a local service booking; confirmation `ACT4` and ₹1,980 total appeared in Trips and the host dashboard. An already occupied host time was unavailable. |
| 16 | Responsive design | ⚠️ | Responsive breakpoints and phone/tablet/desktop layouts are implemented; earlier browser passes inspected 390×844, 768×1024 and 1440×900. I attempted fresh 1440, 768 and 390 viewport overrides, but the browser remained at 1280px each time, so this pass could not re-check those exact widths. |
| 17 | Airbnb visual similarity | ⚠️ | Local UI has Airbnb-style segmented search, category rail, photo-forward cards, rounded controls, review details and modal patterns. Compared at a high level with the public [Airbnb India house-rental page](https://www.airbnb.co.in/india/stays/houses); it is an original assignment UI, not a pixel-perfect copy, and no side-by-side pixel measurement was performed. |
| 18 | API architecture | ✅ | FastAPI routers separate home and activity workflows; Pydantic validation, status handling, user scoping, server quotes, idempotency and ownership are exercised by the backend suite. Local UI requests returned successfully on the tested flows. |
| 19 | Database architecture | ✅ | SQLite schema uses foreign keys on connections, relationships, constraints, indexes, integer INR amounts, historical booking snapshots, overlap enforcement and soft deletion. Regression tests exercise foreign-key and trigger enforcement. |
| 20 | README | ✅ | Reviewed `README.md` setup, environment, seed/init, schema/ER diagram, API examples, booking rules, tests, deployment/persistence and demo identity explanation against the package scripts and backend layout. |
| 21 | Error handling | ✅ | UI has loading, empty, retry and validation states; malformed images have a fallback. `api()` maps network, HTTP and malformed-response errors. Added a single delayed retry for failed GETs only; writes are never replayed. |
| 22 | Loading states | ✅ | Listing, host and activity components expose loading states before rendering data, with empty/error states after completion. Tested Trips transition and retry in the browser. |
| 23 | TypeScript errors | ✅ | `npm run typecheck` and production Next build both passed after the change; 10 frontend tests also passed. |
| 24 | Console errors | ✅ | Browser DevTools log query returned no warnings/errors on the local paths inspected after the fix; this was a targeted sample, not every route or browser. |
| 25 | Backend errors | ✅ | `python -m pytest backend/tests -q`: 82 passed at this checkpoint. Targeted local UI actions completed and server logs showed successful API responses; no 5xx was observed in those actions. This is not a claim that every possible production request is error-free. |

### Findings and focused correction

- No required feature was missing and no persistent broken workflow remained at the end of this pass. The only reproduced user-visible rough edge was a transient failed Trips read on a demo-profile transition. A one-time retry was added for network-failed `GET` requests; POST/PUT/DELETE operations are not retried. The new frontend regression test verifies both retry behavior and the no-write-replay rule.
- Running the dev server regenerated `frontend/next-env.d.ts` with development-only type paths. The initial Git tree was clean, so those generated-only edits were restored to the committed references.
- No seed or public data was reset. Host CRUD and bookings were tested against the isolated `.devtools/evaluator-20261009.sqlite` database. The deployed site was only read; no public booking, review, listing edit or upload was made.

### Checks run in this pass

```text
python -m pytest backend/tests -q    82 passed
cd frontend && npm test              10 passed
cd frontend && npm run lint           passed (0 warnings)
cd frontend && npm run typecheck      passed
cd frontend && npm run build          passed (Next.js 16.4 static export)
```

Local browser work exercised home search/filtering, listing detail/calendar, the mock home checkout, guest Trips and favorites, host CRUD/dashboard, experience/service bookings, and post-fix demo-profile switching. The live URL was smoke-tested on the existing listing-detail page only; remote API failure paths and remote write flows were not tested. The local browser console sample was empty. Exact responsive sizes and an exhaustive accessibility/console pass were not repeated in this evaluator run.

### Remaining limits

- Demo profiles and `X-Demo-User` are intentionally public and spoofable; this is not real authentication or production authorization.
- Images and map pins are illustrative; geolocation is approximate and map tiles/photo hosts depend on third parties.
- The UI resembles Airbnb’s marketplace patterns but is not pixel-identical. The 390/768/1440 responsive evidence is from the previous recorded browser pass.
- Cloud Blob upload was implemented and previously verified against the deployed service, but was not re-run here to avoid consuming free shared storage quota.
- No exhaustive accessibility audit, all-browser viewport matrix, remote booking/API test, or payment integration was performed.

## Curated seed and compact activity-date refresh (9 October 2026)

- Replaced the repeated template-like demo catalogue with 48 curated homes, 24 Experiences and 20 Services. All 92 curated offers now have distinct host identities and primary image URLs; the preserved completed-stay demo home retains its separate host and cover. Gallery photos, amenities, ratings, reviews, and rolling future availability remain in the existing schema.
- Added `curated-marketplace-v3` as an additive marker. Existing seeded offers have their primary cover and host updated in place; old booking/review rows and user-created content are retained. Fresh and previously migrated databases converge on 49 active homes, 24 Experiences, 20 Services, 93 active host identities, and 93 unique cover images.
- Compact Experiences/Services search now summarizes a selected date as `12 Oct` (or `Any week`) and opens the native calendar when its compact summary is clicked. The raw date input is reduced to a 1×1 transparent control on desktop compact mode, preventing its browser-formatted value from colliding with neighboring sections; mobile keeps the normal date control.
- Browser verification on local Services confirmed 20 cards, all 12 currently rendered photos loaded, no broken visible images, no horizontal overflow at the 1280 px viewport, `Any week` in the compact bar, and the compact date button opened the calendar. On Experiences, selecting 12 October displayed `12 Oct`; clicking the compact summary opened the calendar. No console warnings or errors were captured.
- Isolated migration query verified counts, 93 distinct active host names, 93 distinct primary cover URLs, and seed versions through v3. Restart/idempotence and booking-preservation regression test passed. The focused regression suite now asserts offer titles, primary photos, host identities, and per-section content uniqueness.
- Checks recorded at this historical checkpoint: 83 backend tests, 10 frontend tests, TypeScript, ESLint and the Next production build passed. At that point the changes were local and unpublished; the final submission verification below records the later publication state.
- Remaining limits for this refresh: third-party Unsplash/RandomUser availability is not guaranteed by the database; full remote production verification and fresh 390/768 viewport tests were not repeated in this focused pass.

## Final submission verification (9 October 2026)

- The audited application code is commit `86d9c42714fb807106645c51d583ead973925b50` on `main`. It was pushed to the public repository [gursimarsingh1001/airbnb-fullstack-marketplace](https://github.com/gursimarsingh1001/airbnb-fullstack-marketplace); the repository and production deployment were verified at that code revision before this documentation-only correction.
- Re-ran checks against that application code: `python -m pytest backend/tests -q` — **86 passed**; `npm test` — **10 passed**; `npm run lint`, `npm run typecheck`, and `npm run build` — **passed**. The build generated the Next.js 16.4 static export successfully.
- The GitHub Actions `Application checks` workflow passed on the published application revision: [run 37919375432](https://github.com/gursimarsingh1001/airbnb-fullstack-marketplace/actions/runs/37919375432). The live demo URL is [airbnb-fullstack-marketplace.vercel.app](https://airbnb-fullstack-marketplace.vercel.app/); the deployed health endpoint reported SQLite and the Asia/Kolkata date policy.
- No application source or behavior changed in this final documentation correction. The results above are concrete verification, not a guarantee of literal perfection: real authentication/payments remain mocked, third-party image/tile availability is external, and exhaustive accessibility/browser/device testing was not performed.
