# Homes, Experiences and Services implementation

Verification date: 9 October 2026. This report distinguishes implementation from observed tests; it does not claim production authentication, real appointments, or pixel-identical Airbnb visuals.

## Scope and architecture

Preserved Next.js/TypeScript, FastAPI, SQLite, existing home workflows, Leaflet map, home uploads, dark mode, and the shared animated header. Added six focused activity components: Browse, Card, Detail, Editor, Host, and Trips. The shared `activities` model uses a `kind` discriminator instead of two almost identical databases/API implementations. Home bookings remain in their existing tables.

The guest selects a session and people count. The frontend requests a quote. FastAPI checks the slot, provider, future IST time, capacity and conflicts; it computes integer-INR pricing. Confirmation supplies that quote's total and an idempotency key. SQLite acquires a write lock before availability is checked again and the immutable price snapshot is inserted. Database triggers repeat critical checks. Both Trips and the owner dashboard read that reservation. On Vercel, the existing private Blob snapshot adapter publishes the committed database conditionally by ETag before returning success.

## Requirement status

| Requirement | Implementation | Verification evidence |
| --- | --- | --- |
| Home browsing, search, categories, filters, pagination | Preserved; added room counts, rating range and Superhost filters | Existing regression suite and combined new API filter test; browser home detail and checkout |
| Home galleries, calendars, prices and reviews | Preserved | Browser calendar disabled yesterday and seeded occupied dates; 3-night checkout matched ₹32,364 server total |
| Home booking, Trips, persistence, overlap rules | Preserved | Browser confirmation AB000006; existing atomic/overlap/idempotency regression tests |
| Home host CRUD and ownership | Preserved | Existing integration suite; home provider UI was not repeated in this expansion pass (earlier audit covers it) |
| Experiences browse/search/filter/pagination | Implemented | API combined-filter and pagination tests; browser browse, detail, reserve and Trips |
| Services browse/search/filter/pagination | Implemented | Browser page 2 → Private chefs reset to page 1; max ₹2,500 reduced two chefs to one |
| Detail galleries, hosts, reviews, booking controls | Implemented for both | Browser gallery opened/closed; date/time/guest controls, quote and confirmation |
| Experience seat capacity | Implemented in API and SQLite | Simultaneous attempts yield one 201 and one 409; over-capacity and direct SQL regression tests |
| Service/provider conflict protection | Implemented in API and SQLite | Concurrent requests, cross-offering provider conflicts and adjacent sessions tested; booked 14:00 slot visibly unavailable |
| Provider CRUD and ownership | Implemented for both | Browser create → edit price/title → view/refresh → remove for experience; create → edit → remove for service; API ownership/soft-delete tests |
| Provider reservations | Implemented | Browser host saw guest ACT3 experience and ACT4 service, including after server restart |
| Unified Upcoming/Past/Cancelled Trips | Implemented | Browser refreshed Trips showed home, experience and service with correct totals; cancellation API regression |
| Unified saved items | Implemented | Refreshed browser wishlist showed saved home, experience and service; uniqueness/scoping API tests |
| Seed content and migrations | Implemented | Fresh database creates 20+20 offerings, reviews and slots; repeated initialization test; provider-removed slot remains removed |
| Responsive layout | Implemented | Inspected 390×844, 768×1024 and 1440×900; no page-width overflow on measured mobile/tablet views |
| Feedback and failure states | Implemented | Existing accessible Modal/toast/image fallback reused; rejected invalid provider submission displayed error; removed/missing offerings show unavailable state |
| Durable deployed data | Existing adapter retained | Snapshot durability/concurrent-write tests included; deployment smoke results to be recorded below |

## Checks run

- `python -m pytest backend/tests -q`: **82 passed** after new SQL guard and restart regression tests.
- `npm test`: **9 passed** (frontend domain/calendar/API tests).
- `npm run lint`: passed during implementation; rerun for final build.
- `npm run typecheck`: passed during implementation; production build also type-checks.
- `npm run build`: passed with static root, Experiences, Services and not-found pages.
- Real local browser: experience ACT3, 20 October at 09:00, 2 guests, ₹3,960; service ACT4, 21 October at 14:00, 2 guests, group price ₹1,980. Both survived refresh and appeared in the correct provider dashboard.
- Stopped and restarted the isolated backend; ACT4 and its host reservation remained present. Existing user databases were not reset. Browser-created provider QA items were soft-removed.
- Home regression booking AB000006: 12–15 November, ₹9,200 × 3 + ₹900 cleaning + ₹3,864 fee = ₹32,364.
- Browser console error query returned no errors at the unified wishlist checkpoint. HTTP checks found one 404 Unsplash seed URL; replacement and all other unique activity seed assets returned 200.
- Browser screenshots inspected at phone, tablet and desktop dimensions. Native date input automation needed the browser's native value setter; normal keyboard/select/gallery controls were exercised. This was not a comprehensive assistive-technology audit.

## Files

New backend files: `activities.py`, `activity_schema.py`, `activity_seed.py`, `dependencies.py`, `tests/test_activities.py`.

New frontend files: `app/experiences/page.tsx`, `app/services/page.tsx`, `lib/activities.ts`, and `components/activities/{ActivityBrowse,ActivityCard,ActivityDetail,ActivityEditor,ActivityHost,ActivityTrips}.tsx`.

Modified existing files: database initialization and main router, migration test expectation, Marketplace integration, shared CSS, Next configuration, README. No additional application dependencies are needed.

## Provider API example

Use a future date when trying this example. Send `X-Demo-User: 2` to `POST /api/activities/host`:

```json
{
  "kind": "experiences",
  "title": "A local cooking workshop",
  "description": "Prepare a seasonal meal together with a friendly local host.",
  "location": "Goa", "country": "India", "category": "Food & drink",
  "price": 2500, "price_type": "person", "duration_minutes": 60,
  "capacity": 6, "language": "English", "setting": "Indoor",
  "service_location": "Provider location",
  "itinerary": "Meet your host.\nPrepare and share a meal.",
  "included": "Ingredients and equipment",
  "requirements": "Arrive ten minutes early.",
  "photos": ["https://images.unsplash.com/photo-1556911220-bff31c812dba"],
  "slots": [{"day":"2027-01-20","start_time":"10:00","capacity":6}]
}
```

For a service use `kind:services`, a service category such as `Private chefs`, and `price_type:group` or `person`. `PUT /api/activities/host/{id}` replaces editable content/photos and future availability atomically. It cannot remove booked upcoming slots or reduce capacity below confirmed people. DELETE soft-removes and preserves history; upcoming reservations block removal.

## Demo walkthrough

1. Use Alex's guest profile. Browse Homes, open a home, select future nights and reserve without payment details.
2. Open Experiences, select a category/destination, choose a date/time and guests; confirm the server quote.
3. Open Services, choose a chef or photographer, then reserve a future session. Group pricing remains one group price regardless of selected people within capacity.
4. Open Trips: show all three types and the Upcoming/Past/Cancelled tabs. Open Wishlists to show saved items after refresh.
5. Switch to Ananya's host profile. Open Hosting dashboard → Experiences/Services. Show reservations, then create an offering with an HTTPS photo and future availability; edit or remove it.
6. Explain why two guests cannot overbook a session: writer lock, recheck, SQL guard, persisted snapshot; serverless publication adds an ETag check.

## Limits to explain in evaluation

- Demo identity is openly selectable (`X-Demo-User`), not secure login. Ownership is enforced relative to that selected identity.
- Activities use IST globally, whole INR, a 10% fee, and read-only seeded reviews. Home stays retain date-only India policy and their existing 14% fee.
- Payments, identity checks and messages are mocked. Providers, availability, photos and reviews are fictional; photos may be reused across illustrative galleries.
- Activity editors accept image URLs; the existing home editor supports Blob uploads. External images/map tiles need internet access.
- Private Blob stores complete SQLite snapshots for a small, free demo; quotas, latency and the 10 MB snapshot cap remain limitations. No paid hosting was introduced.
- Browser checks sampled the workflows and three breakpoints. Full keyboard/screen-reader coverage, every possible filter combination, and a new pixel-by-pixel Airbnb comparison have not been claimed.
