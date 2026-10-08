# Verification record

## Automated checks

- `python -m pytest backend/tests -q`: **12 passed**.
- `npm run build`: Next.js production compilation, TypeScript validation, and static export passed.
- Dependency installation: 0 known vulnerabilities reported by npm at installation time.

## Browser flow

Using the actual production export served by FastAPI:

1. Explore loads 20 database-backed homes, 15 on the first page, with photos and prices.
2. Opened listing 4, selected 10–13 November 2026, and selected two guests.
3. API quote returned ₹16,200 subtotal + ₹900 cleaning + ₹2,268 service = **₹19,368**.
4. Mock checkout returned persisted reservation **AB000005** and displayed the confirmation dialog.

The automatic test database is isolated in a temporary directory. Browser verification uses the local demonstration database and can leave sample reservations in Trips; it never processes real payment.

## Deployment boundary

The Docker/Render configuration uses one FastAPI service with a persistent SQLite volume. A hosted demo is only complete after the provider has built the image, attached the disk, returned a public URL, and passed `/api/health`. Authentication and plan approval are required before paid hosting resources can be created.
