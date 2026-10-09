# How the application works

## 1. Architecture
There are three layers: the Next.js interface, the FastAPI API, and a SQLite database. The browser sends HTTP requests to Python. Python checks the request, reads or changes SQLite, and returns JSON. React updates the page with that response.

## 2. Frontend structure
`frontend/app/` contains Next.js entry pages. `Marketplace.tsx` coordinates navigation and shared state. Feature folders separate layout, search, listings, bookings, hosting, maps and activities. `listings/ListingDetail.tsx` handles home details and checkout; `host/HostDashboard.tsx` handles hosting. `shared/` contains dialogs, avatars and image fallbacks. `UI.tsx` only re-exports components for existing callers. `lib/api.ts` holds the HTTP client and formatting helpers, `lib/types.ts` contains home contracts, and `lib/search.ts` contains search types/defaults. See [Code organization](code-organization.md).

## 3. Backend structure
`backend/main.py` composes FastAPI, middleware, error handlers and routers. `routers/` groups HTTP endpoints by resource; `schemas/` contains Pydantic request validation; `services/` contains availability, serialization and listing/activity operations. `dependencies.py` supplies database connections and the selected demo user. `booking_rules.py` contains the home pricing and date policy. Database initialization and migrations stay in their existing modules.

## 4. Database schema
A user can host listings, make bookings and save favorites. A listing has photos, amenities, reviews and bookings. `listing_amenities` joins listings to reusable amenity names. Experiences and Services share `activities`, distinguished by `kind`; their bookable times are `activity_slots`. `activity_bookings` stores reservations and price snapshots. Foreign keys connect records; unique keys prevent duplicate favorites and repeated request keys. See the README ER diagram.

## 5. Search
Search inputs update frontend state. The client builds URL query parameters for `/api/listings`. Python combines location, dates, capacity, category, price, type and amenity conditions, counts matching rows, then returns one page. React renders those rows as cards. Activity search also checks session availability when a day/time filter is supplied.

## 6. Home booking
The user selects dates and guests in `listings/ListingDetail.tsx`. The client requests `/api/quote`. Python validates the selection and returns the current price. Mock checkout submits `/api/bookings` with the selection, expected total and an idempotency key. The server validates again, inserts the booking, commits, and returns a confirmation. The client never decides the final price.

## 7. Preventing overlaps
Reservations occupy check-in inclusive to check-out exclusive. Two stays overlap when `existing.check_in < requested.check_out AND existing.check_out > requested.check_in`. A departure and arrival on the same date are allowed. `BEGIN IMMEDIATE` locks SQLite writers before the check and insert. Database triggers provide additional guards. On hosted snapshot storage, an ETag rejects a stale writer rather than overwriting a newer reservation.

## 8. Price calculation
Home subtotal is nightly price times nights. Add the cleaning fee and a rounded 14% service fee. Activities use a per-person or per-group subtotal plus a rounded 10% fee. Money is whole integer INR; fees use integer arithmetic. Bookings store their original prices, so later listing edits do not change trip totals.

## 9. My Trips
`GET /api/bookings` selects home bookings for the current demo user. `GET /api/activities/bookings` selects their activity reservations. The interface separates upcoming, past and cancelled trips. Refresh loads the persisted records again; local storage is not the booking database.

## 10. Wishlist
A heart click calls PUT or DELETE on the relevant favorites endpoint. Python scopes the operation to the current user. A composite primary key prevents duplicate favorites. The client updates the heart after success and reloads saved items when needed.

## 11. Host CRUD
The form sends validated fields and photo URLs to the host API. The backend checks the host role and ownership, then writes the listing and related photos/amenities together. The dashboard reloads after success. Deletion is soft deletion, preserving history; upcoming or ongoing confirmed reservations prevent removal.

## 12. Experiences
The browse page calls `/api/activities?kind=experiences`. Details show available sessions. A booking reserves seats in one session. Confirmed reservations cannot exceed the session or offering capacity. Different offerings from the same provider cannot overlap.

## 13. Services
Services use the same screens and tables with `kind=services`. Their key difference is exclusive provider time: a confirmed service blocks that provider for the interval, even if priced per person. Adjacent appointments remain allowed. All demo appointment times use IST.

## 14. Why SQLite
SQLite is required by the assignment and keeps local setup simple: one file, no separate database server. Transactions, indexes, foreign keys and triggers support the required consistency rules. It is appropriate for this demo, not a claim that this design supports Airbnb-scale traffic.

## 15. Why payments are mocked
Real payments are outside the assignment. Checkout demonstrates confirmation and price handling without collecting card details, making charges or pretending to create a real travel reservation.

## 16. Important validation
The server rejects past dates under the India calendar policy, invalid stay lengths, excess guests, unavailable inventory, self-booking, unauthorized edits, invalid fields and changed quote totals. Idempotency keys and UI submission guards prevent accidental repeats. The frontend's disabled controls improve usability; backend checks enforce the rules.

## 17. Error handling
The API returns understandable status codes/messages. The client displays them through inline errors or toasts, and has loading/empty states. The HTTP helper retries one failed GET network request, never automatically replays writes, and preserves cancellation. Database failures roll back or close uncommitted connections. Optional browser-storage failures do not stop the app.

## 18. Deployment
Local development uses Next.js on port 3001 and FastAPI on 8001. A production build creates `frontend/out`; FastAPI can serve that export and the API on one origin. Docker uses a persistent volume for SQLite. The Vercel demo instead downloads a private SQLite snapshot for each request and conditionally uploads successful mutations through `blob_database.py`. This preserves SQLite but adds whole-file transfer cost and free-tier quota limits. Credentials stay server-side. The current local edits still need publication and deployed verification.

## A short interview answer
“I built a Next.js and TypeScript interface backed by Python FastAPI and SQLite. The browser handles interaction; the backend owns validation and pricing. For booking, I lock SQLite writes, check availability, save a price snapshot and commit atomically. Idempotency handles repeated submissions. Trips and the host dashboard read those same persisted reservations. Payments and identity selection are deliberately mocked.”
