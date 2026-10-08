# Verification record

## Automated checks

- `python -m pytest backend/tests -q`: **14 passed**.
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
- Final local backend suite: **14 passed**. Vercel production build passed compilation, TypeScript, and static export.
