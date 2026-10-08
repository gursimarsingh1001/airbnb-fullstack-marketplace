# Verification record

## Automated checks

- `python -m pytest backend/tests -q`: **68 passed** (9 October 2026, bonus feature update).
- `npm test`: **8 passed**.
- `npm run typecheck`: passed.
- `npm run lint`: passed with zero warnings.
- `npm run build`: Next.js production compilation, TypeScript validation, and static export passed.
- Dependency installation: 0 known vulnerabilities reported by npm at installation time.

## Browser flow

Using the actual production export served by FastAPI:

1. Explore loads 20 database-backed homes, 15 on the first page, with photos and prices.
2. Opened listing 4, selected 10–13 November 2026, and selected two guests.
3. API quote returned ₹16,200 subtotal + ₹900 cleaning + ₹2,268 service = **₹19,368**.
4. Mock checkout returned persisted reservation **AB000005** and displayed the confirmation dialog.

The automatic test database is isolated in a temporary directory. Browser verification uses the local demonstration database and can leave sample reservations in Trips; it never processes real payment.

## Additional browser checks

- Trips retained the confirmed reservation after refreshing the production export.
- Created a host listing, changed its nightly rate, refreshed, and deleted it through the host dashboard.
- Destination search for Goa returned the two matching homes.
- Mobile date and guest controls were made directly accessible under the compact search bar.

## Cloud persistence

- Initialized the private cloud SQLite snapshot and read back 20 seeded homes.
- Opened two independent snapshots, committed a wishlist change from one, and confirmed that the second writer received a conflict. Removed the test-only wishlist entries afterwards.
- Vercel account plan verified as **Hobby**, with no paid plan or trial.

## Public deployment verification (8 October 2026)

- Public homepage and API respond without Vercel sign-in at https://airbnb-fullstack-marketplace.vercel.app.
- Browser checkout for listing 4, 10–13 November, two guests returned confirmation **AB000005**, total **₹19,368**. Trips retained it after reload.
- A second API request for the same dates returned **409 Conflict**.
- Live host API creation, price update, a fresh read, and soft-delete passed. The test listing was removed; the 20 seed homes remain.
- Mobile layout showed no horizontal document overflow. Desktop preview is saved in `live-demo.jpg`.
- Final local backend suite: **62 passed**. Vercel production build passed compilation, TypeScript, and static export.

## Optional bonus features (9 October 2026)

- Review flow: on the isolated local database, opened Trips, submitted a review for the seeded completed stay, and saw “Review shared” plus a success toast. The 68-test backend suite checks completed-stay eligibility, guest ownership, one review per booking, rating aggregation, concurrent duplicate submissions, and a database-level guard.
- Dark mode: toggled from the account menu and reloaded; the dark palette remained active. The feature stores only the appearance preference in browser local storage.
- Cloud photo uploads: implementation uses the existing private Vercel Blob store and 3 MB JPEG/PNG/WebP limits. Mocked storage tests verify generated private paths, upload/fetch requests, validation, and proxy behavior. A real cloud upload was intentionally not sent during QA because it would consume the shared demo Blob quota.
- Interactive map, Superhost labels/rating aggregation, and responsive layouts existed before this update and remain implemented; see [the requirement matrix](REQUIREMENTS.md) and [audit](audit.md) for the earlier browser evidence.
- Published commit `f30235f` to the public repository. Vercel deployment `dpl_7PUA1f9jwkxF3CHHGm6dEVs9DfA5` reached **READY** and updated the stable demo URL. The live Trips page displayed the seeded completed stay and `Leave a review`; opening the review form showed the rating/comment inputs. The account menu exposed the dark-mode toggle. No review was submitted to public data.

## Map pan regression check (9 October 2026)

- Reproduced the gray map edge after a rapid side-to-side drag on the deployed site. Leaflet's inertial glide carried the map beyond the OpenStreetMap tile world.
- Disabled map inertia, constrained panning to the Web Mercator world, and set a viewport-aware minimum zoom (at least zoom 3).
- Repeated rapid sideways drags on the live demo; all visible tiles loaded. Zooming out stopped at zoom 3 with all visible tiles loaded.
- Pushed as commit `e64934e`; Vercel deployment `dpl_42rZUix7A3ynMdXRL6c7QY2S5mk1` reached `READY` at the existing public demo URL.
