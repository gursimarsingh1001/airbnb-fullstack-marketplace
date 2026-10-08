# Assignment requirement checklist

Audit date: **9 October 2026**. “Implemented” describes source behavior; the verification column says what was actually exercised. Evidence references the local production export served by FastAPI unless it explicitly says otherwise.

| Requirement | Status | Verification evidence |
| --- | --- | --- |
| Required Next.js/TypeScript + FastAPI + SQLite stack and `frontend/`, `backend/` layout | Implemented and verified | Configuration/source inspected; frontend production export and FastAPI API run locally |
| Explore cards show photos, names, locations, nightly price, rating | Implemented and verified | Local browser rendered seeded listings; fallback works for invalid image URL |
| Search by location, dates, guests | Implemented and verified | Himachal search browser check; backend validates guest/date and excludes stays across all overlap shapes |
| Categories, price, type, amenities and combined filters | Implemented and verified | Mobile UI combined Cabin + ₹10,000 + Mountain view; API combined search test |
| Pagination after filtering | Implemented and verified | API tests confirm filtered 2-page result and date-availability updates; browser filter showed accurate 1–2 count |
| Loading, empty, error states and notifications | Implemented and verified | Source reviewed; UI showed host create/edit/delete notifications; API client regression tests cover offline/non-JSON errors |
| Search state survives navigation/reload | Implemented and verified | Location/category state restored after reloading local production app |
| Persistent profile-scoped favorites | Implemented and verified | UI favorite persisted after reload and switched away with profile; backend prevents duplicates/scopes users |
| Listing detail, direct links, removed/unknown IDs | Implemented; partially verified | Detail opened via UI; API regressions cover deleted/missing ID; browser direct refresh/nonexistent URL not separately exercised |
| Gallery, photo fallback, description, host, amenities, reviews | Implemented and verified | Gallery opened with six rendered images; bad host photo showed fallback; detail content inspected in browser |
| Calendar and unavailable dates | Implemented and verified | Browser confirmed blocked nights and free checkout boundary; 3 frontend calendar tests cover boundaries and policy |
| Quote/checkout/confirmation price consistency | Implemented and verified | Local two-night booking total ₹16,518 matched confirmed API/UI breakdown; quote changes reject stale checkout |
| Past/invalid dates, listing capacity, missing listing, host self-booking | Implemented and verified | Backend parametrized validation/ownership tests; policy uses UTC date-only “today” |
| Overlap shapes, containing/contained stays, back-to-back | Implemented and verified | Five interval-shape API cases reject; both adjacent boundaries pass; SQLite trigger repeats overlap check |
| Concurrent bookings and duplicate submissions | Implemented and verified | `BEGIN IMMEDIATE`, unique idempotency key, database trigger; concurrent same-key test returns one ID; changed-key payload rejected |
| Booking scope, guest Trips, host reservations, cancellation | Implemented and verified | Browser confirmation survived refresh; cancellation succeeded; API tests scope guest/host records and preserve history |
| Persistence after server initialization/restart | Implemented and verified in isolated tests | Fresh ASGI lifespan retains created listing, booking, favorite and seed; actual local process was restarted during audit and DB data remained |
| Host create/view/edit/remove and form validation | Implemented and verified | Actual browser created, refreshed edited fields/price, and soft-deleted an isolated test listing; invalid URL rejected |
| Backend listing ownership | Implemented and verified | Direct API tests reject another host editing/removing; actual dashboard used host profile |
| Removal with reservation history | Implemented and verified | Soft-delete retains record; active future stays prevent removal; test covers removed listing inaccessible to new bookings |
| SQLite foreign keys/constraints/indexes/relationships | Implemented and verified | `PRAGMA foreign_keys=1` and raw invalid insert tests; overlap/price/history triggers tested |
| Integer-INR money and historical price snapshot | Implemented and verified | Regression edits current price after booking and asserts old booking amount remains fixed |
| Seeded varied homes/hosts/reviews/bookings, rerunnable without reset | Implemented and verified | Seed code inspected; tests assert 20 homes, six users, 60 reviews retained on repeat lifespan |
| Clear current demo user and guest/host behavior | Implemented; mock-auth limitation | UI provides guest and host personas; API scopes by `X-Demo-User` ownership, but identities are intentionally public and spoofable |
| Clearly mocked checkout; no card collection | Implemented and verified | Checkout marked demo, no credential inputs; browser completed mock reservation |
| Desktop/tablet/mobile responsive layout | Implemented and partially verified | Screenshots at 390 px and 768 px inspected; desktop screenshot reviewed; no overflow measured at phone/tablet. 1440px numeric overflow audit remains unverified |
| Interactive map with listing pins | Implemented and verified | Leaflet map shows approximate listing pins and home previews; production drag/zoom checks after the map-bounds fix showed tiles remain in view |
| Review after a completed stay | Implemented and verified | Guest submitted the seeded completed-trip review through Trips in the local browser; UI changed to “Review shared”; API tests verify ownership, one-review rule, rating aggregation, and trigger enforcement |
| Superhost badges and rating aggregation | Implemented and verified | Seeded Superhost labels display on cards/details; listing responses aggregate review average/count, and the review regression test confirms the aggregate changes after a new review |
| Image upload to cloud storage | Implemented; integration partially verified | Host photo upload validates image bytes/types and stores privately through Vercel Blob; API/storage tests mock the Blob service and verify upload/fetch paths. A real upload was not sent to the shared production store |
| Persistent dark mode | Implemented and verified | Toggled dark mode in the local browser, saw the dark palette, then refreshed and confirmed the preference remained active |
| Responsive mobile/tablet/desktop layouts | Implemented and partially verified | Prior browser audit inspected 390 px, 768 px, and wide desktop views; this bonus pass confirmed the dark palette on the local explore page |
| Keyboard labels, visible focus, modal focus | Partially verified | Modal Escape/focus trap keyboard test performed; labels and buttons reviewed in accessibility tree; no screen reader or automated WCAG/contrast audit |
| Lint, TypeScript, frontend/backend tests, production build | Implemented and verified | ESLint pass; `tsc --noEmit` pass; 8 frontend tests pass; 68 backend tests pass; Next production static build pass |
| README/setup/schema/API/config/deployment documentation | Implemented and reviewed | Commands match package/workflow; isolated env example and versioned schema, quote/book examples, ER diagram, pricing/race/deploy policies included |
| Reference comparison and original UI | Implemented and visually reviewed | Accessible Airbnb public homepage viewed; local 768 and 390 layouts reviewed against photo grid, compact search, category scroller, card proportions, typography, palette, roundness, spacing |
| Free public repo/deployment | Implemented and verified | Bonus update commit `f30235f` is pushed to the existing public GitHub repository; Vercel deployment `dpl_7PUA1f9jwkxF3CHHGm6dEVs9DfA5` reached `READY` and aliased the existing public URL. The live Trips page shows the completed review action, and the profile menu exposes dark mode. |

### Permitted or optional exclusions

Real payments, messaging, identity verification, live pricing pins, and social authentication remain mocked or unimplemented as permitted. The map uses approximate seeded coordinates and OpenStreetMap tiles; cloud photo storage uses the connected Vercel Blob quota.
