# Map redesign — 9 October 2026

Replaced the decorative road/river mockup in Explore and listing details with a lazy-loaded Leaflet 1.9.4 map using OpenStreetMap tiles. No paid API is configured.

- Explore uses the current page of filtered listing results and stored approximate demo coordinates. A country selector avoids an unreadable global view.
- Nearby price pins group at low zoom; clicking a group zooms into its homes. A sidebar (horizontal cards on mobile), selected-home photo preview, zoom controls, and reset-to-region control support navigation.
- A preview opens the relevant listing detail. Detail displays its own surrounding area using the same map component.
- Missing coordinates show a text location rather than an invented position. Failed tile loads show retry feedback while listing previews remain available.
- Visible OSM attribution, standard browser caching, viewport-only requests, and no geolocation permission requests. External tiles are best-effort and require internet access.

Verification: lint, TypeScript, frontend unit tests (8 passing), and production export passed. Browser inspected at 1440×1000 and 390×844. Group expansion, Indonesia region switch, preview-to-detail navigation, detail map rendering, and 390px document width were checked. No console errors were captured during these interactions. No backend behavior or stored data was modified.
