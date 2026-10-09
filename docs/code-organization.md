# Code organization and refactor verification

## Purpose

This pass separates responsibilities in the existing application without changing its stack, interface, API paths or database schema. It is a maintainable assignment structure, not a claim of production operational readiness.

## Where changes belong

| Responsibility | Location |
| --- | --- |
| App setup, middleware, router registration | `backend/main.py` |
| HTTP endpoints and request transaction orchestration | `backend/routers/` |
| Pydantic request contracts | `backend/schemas/` |
| Availability, serialization, listing/activity operations | `backend/services/` |
| Home pricing and booking date policy | `backend/booking_rules.py` |
| Connection lifecycle and demo identity | `backend/dependencies.py` |
| SQLite initialization, migrations, seeds and durable snapshots | Existing dedicated backend modules |
| Page composition and shared UI state | `frontend/components/Marketplace.tsx` |
| Header and destination inspiration | `frontend/components/layout/` |
| Search bars and filters | `frontend/components/search/` |
| Listing cards and detail/checkout | `frontend/components/listings/` |
| Calendar, guests and Trips | `frontend/components/bookings/` |
| Hosting and map UI | `frontend/components/host/`, `maps/` |
| Modal, image fallback, avatar and status UI | `frontend/components/shared/` |
| Domain contracts and search defaults | `frontend/lib/types.ts`, `search.ts` |
| HTTP transport and formatting | `frontend/lib/api.ts` |

The backend dependency direction is app composition → routers → schemas/services → existing database and booking helpers. Routes keep ownership checks and transaction boundaries visible. Availability checks and writes remain within the existing SQLite transaction; extracting functions must not split that critical section.

Frontend feature components receive data and callbacks from the coordinator. Shared components do not own global routing. Domain types are separate from HTTP transport. `UI.tsx` and `backend/activities.py` remain small compatibility exports so existing imports continue working; they contain no duplicate implementations.

No generic repository framework, ORM conversion, global state library or extra service was introduced. These would add migration risk without improving this assignment's current use cases. `Marketplace.tsx` remains a sizable coordinator, and listing detail still owns its checkout flow. Further extraction should follow a concrete responsibility or change requirement, rather than an arbitrary file-length target.

## Verification of this refactor

Local verification on 9 October 2026:

- `python -m pytest backend/tests -q`: **86 passed**. Existing business-rule, ownership, concurrency and persistence coverage retained.
- New `test_route_contract.py`: all **31 API method/path combinations** remain registered after moving routers.
- `npm test` in `frontend/`: **10 passed**.
- `npm run lint`, `npm run typecheck`, `npm run build`: passed.
- Browser against the production static export served by refactored FastAPI at port 8005: Manali search returned the matching home; listing details and unavailable/past calendar dates rendered; a 28–30 October stay for two guests quoted ₹16,515; mock checkout returned confirmation AB000008; Trips displayed it and retained it after refresh.
- At 390px, the extracted Trips page rendered without horizontal overflow; header, trip card and bottom navigation were visually inspected.
- No warning/error console entries were captured during that booking walkthrough.

Browser writes used the ignored isolated `.devtools/responsive-final.sqlite` database, not the deployed database. Earlier broader responsive and CRUD results are recorded separately in `final-ui-verification.md`; they are historical checks, not a claim that every interaction was repeated after extraction. This refactor has not been pushed or deployed. Cloud credentials, hosting durability and full production traffic behavior were not reverified in this pass.

## Evaluator explanation

“The frontend is organized by product feature, with shared UI primitives and typed API contracts. FastAPI is composed in main.py, endpoints are grouped by resource, request validation lives in schemas, and reusable operations live in services. SQLite owns persisted data and constraints. Booking checks, price snapshots and insertion stay in the existing transaction. A route-contract regression test guards the public API during refactoring.”
