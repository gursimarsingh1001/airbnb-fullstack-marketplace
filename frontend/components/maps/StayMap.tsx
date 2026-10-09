"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { ArrowUpRight, LocateFixed, MapPin, Minus, Plus, Star } from "lucide-react";
import type { Map as LeafletMap, Marker } from "leaflet";
import { Listing, money } from "@/lib/api";
import { SafeImage } from "@/components/UI";
import "leaflet/dist/leaflet.css";

const hasPosition = (home: Listing) => Number.isFinite(home.latitude) && Number.isFinite(home.longitude)
  && Math.abs(home.latitude) <= 85 && Math.abs(home.longitude) <= 180
  && !(home.latitude === 0 && home.longitude === 0);

/** The coordinates are approximate demo locations, never a verified street address. */
export default function StayMap({ homes, onOpen, compact = false }: {
  homes: Listing[]; onOpen?: (id: number) => void; compact?: boolean;
}) {
  const located = useMemo(() => homes.filter(hasPosition), [homes]);
  const countries = useMemo(() => [...new Set(located.map((h) => h.country))]
    .sort((a, b) => located.filter((h) => h.country === b).length - located.filter((h) => h.country === a).length), [located]);
  const [country, setCountry] = useState(countries[0] || "");
  const region = countries.includes(country) ? country : countries[0];
  const visible = useMemo(() => located.filter((h) => h.country === region), [located, region]);
  // Stable value prevents quote/profile rerenders from recreating the map.
  const positions = JSON.stringify(visible.map(({ id, latitude, longitude, price, title, location }) => ({ id, latitude, longitude, price, title, location })));
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const selected = visible.find((h) => h.id === selectedId);
  const currentSelection = useRef(selected?.id);
  currentSelection.current = selected?.id;
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<LeafletMap | null>(null);
  const pins = useRef(new Map<number, Marker>());
  const fit = useRef<() => void>(() => {});
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    const entries: Pick<Listing, "id" | "latitude" | "longitude" | "price" | "title" | "location">[] = JSON.parse(positions);
    if (!container.current || !entries.length) return;
    let disposed = false;
    let cleanup = () => {};
    import("leaflet").then((L) => {
      if (disposed || !container.current) return;
      // OSM tiles stop at the Web Mercator world edge. Keep the entire viewport
      // inside it, including when zoomed out or resized to a wider screen.
      const world = L.latLngBounds([[-85.0511287798066, -180], [85.0511287798066, 180]]);
      // Keep the wrapped tile layer larger than the viewport even on wide maps.
      const minimumZoom = () => Math.max(3, Math.ceil(Math.log2(Math.max(container.current?.clientWidth || 256, container.current?.clientHeight || 256) / 256)));
      const instance = L.map(container.current, {
        zoomControl: false, scrollWheelZoom: true, inertia: false, minZoom: minimumZoom(), maxZoom: 18,
        maxBounds: world, maxBoundsViscosity: 1,
      });
      map.current = instance;
      instance.attributionControl.setPrefix(false);
      const tiles = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19, noWrap: true, keepBuffer: 1,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a> contributors',
      }).addTo(instance);
      let loaded = false;
      tiles.on("tileload", () => { loaded = true; if (!disposed) setStatus("ready"); });
      tiles.on("tileerror", () => { if (!disposed && !loaded) setStatus("error"); });
      const timeout = window.setTimeout(() => { if (!disposed && !loaded) setStatus("error"); }, 12000);
      const bounds = L.latLngBounds(entries.map((h) => [h.latitude, h.longitude]));
      fit.current = () => instance.fitBounds(bounds, { padding: [55, 65], maxZoom: compact ? 12 : 10, animate: false });
      fit.current();
      const renderPins = () => {
        pins.current.forEach((pin) => pin.remove());
        pins.current.clear();
        // Group screen-adjacent homes so price labels never pile up at country zoom.
        const groups: (typeof entries)[] = [];
        entries.forEach((home) => {
          const point = instance.latLngToLayerPoint([home.latitude, home.longitude]);
          const group = groups.find((items) => {
            const anchor = instance.latLngToLayerPoint([items[0].latitude, items[0].longitude]);
            return Math.abs(point.x - anchor.x) < 100 && Math.abs(point.y - anchor.y) < 64;
          });
          if (group) group.push(home); else groups.push([home]);
        });
        groups.forEach((items) => {
          const home = items[0], clustered = items.length > 1;
          // Text nodes avoid interpreting a listing's user-provided fields as HTML.
          const label = document.createElement("span");
          label.textContent = clustered ? String(items.length) : money(home.price);
          const width = clustered ? 44 : 80;
          const marker = L.marker([home.latitude, home.longitude], {
            icon: L.divIcon({ className: `stay-price-pin${clustered ? " stay-cluster-pin" : ""}${items.some((h) => h.id === currentSelection.current) ? " selected" : ""}`, html: label, iconSize: [width, clustered ? 44 : 36], iconAnchor: [width / 2, clustered ? 22 : 18] }),
            title: clustered ? `Zoom to ${items.length} homes, from ${money(Math.min(...items.map((h) => h.price)))}` : `${home.location} · ${money(home.price)} per night`,
            alt: clustered ? `Zoom to ${items.length} nearby homes` : `Preview ${home.title}`, keyboard: true,
          }).addTo(instance);
          marker.getElement()?.setAttribute("aria-label", clustered ? `Zoom to ${items.length} nearby homes` : `Preview ${home.title}, ${money(home.price)} per night`);
          marker.on("click", () => {
            if (clustered) instance.fitBounds(L.latLngBounds(items.map((h) => [h.latitude, h.longitude])), { padding: [75, 75], maxZoom: Math.min(17, instance.getZoom() + 3) });
            else setSelectedId(home.id);
          });
          pins.current.set(home.id, marker);
        });
      };
      renderPins();
      instance.on("zoomend", renderPins);
      const observer = new ResizeObserver(() => {
        instance.setMinZoom(minimumZoom());
        instance.invalidateSize({ pan: false });
        instance.panInsideBounds(world, { animate: false });
      });
      observer.observe(container.current);
      cleanup = () => { window.clearTimeout(timeout); observer.disconnect(); pins.current.clear(); instance.remove(); map.current = null; };
    }).catch(() => { if (!disposed) setStatus("error"); });
    return () => { disposed = true; cleanup(); };
  }, [positions, compact, retry]);

  useEffect(() => {
    pins.current.forEach((pin, id) => {
      pin.getElement()?.classList.toggle("selected", id === selected?.id);
      pin.getElement()?.setAttribute("aria-pressed", String(id === selected?.id));
      pin.setZIndexOffset(id === selected?.id ? 1000 : 0);
    });
  }, [selected?.id, status]);

  function choose(home: Listing) {
    setSelectedId(home.id);
    map.current?.flyTo([home.latitude, home.longitude], Math.max(map.current.getZoom(), 9), { duration: 0.6 });
  }

  if (!located.length) return <div className="map-unavailable"><MapPin size={30} /><h3>Location details</h3><p>{homes[0]?.location || "No homes in this search"}</p><span>A map position hasn’t been added for this home yet.</span></div>;

  return <div className={`stay-map ${compact ? "stay-map-compact" : ""}`}>
    {!compact && <div className="stay-map-toolbar">
      <div><strong>Find your place on the map</strong><span>{visible.length} stays in {region} · Zoom in for nightly prices</span></div>
      <label className="map-region"><MapPin size={16} /><span>Country</span>
        <select aria-label="Map country" value={region} onChange={(event) => { setCountry(event.target.value); setSelectedId(null); setStatus("loading"); }}>{countries.map((name) => <option key={name} value={name}>{name} ({located.filter((h) => h.country === name).length})</option>)}</select>
      </label>
    </div>}
    <div className="stay-map-layout">
      {!compact && <div className="map-results" aria-label="Homes on the map">
        <div className="map-results-heading">{visible.length} places to stay in {region}</div>
        {visible.map((home) => <button key={home.id} className={`map-result ${selected?.id === home.id ? "selected" : ""}`} onClick={() => choose(home)} aria-pressed={selected?.id === home.id}>
          <SafeImage src={home.photos[0]} alt={home.title} />
          <span className="map-result-copy"><strong>{home.location.split(",")[0]}</strong><span>{home.title}</span><span className="map-rating"><Star size={11} fill="currentColor" /> {home.rating?.toFixed(2) || "New"} · {home.max_guests} guests</span><span className="map-night"><b>{money(home.price)}</b> / night</span></span>
        </button>)}
        {homes.length > located.length && <p className="map-missing">{homes.length - located.length} homes have no map position. They’re still available in the results grid.</p>}
      </div>}
      <div className="map-stage">
        <div ref={container} className="map-canvas" aria-label="Interactive map of approximate listing locations" />
        <div className="map-caption"><MapPin size={13} /> Approximate locations · Tap a number to zoom</div>
        <div className="map-controls">
          <button aria-label="Zoom in" onClick={() => map.current?.zoomIn()}><Plus size={20} /></button>
          <button aria-label="Zoom out" onClick={() => map.current?.zoomOut()}><Minus size={20} /></button>
          <button aria-label="Fit all homes in this region" onClick={() => fit.current()}><LocateFixed size={19} /></button>
        </div>
        {status === "loading" && <div className="map-status" role="status">Loading map…</div>}
        {status === "error" && <div className="map-status" role="status">The map couldn’t load. You can still explore these homes.<button onClick={() => { setStatus("loading"); setRetry((n) => n + 1); }}>Retry map</button></div>}
        {!compact && selected && <div className="map-preview" aria-live="polite"><button className="map-preview-close" aria-label="Close home preview" onClick={() => setSelectedId(null)}>&times;</button>
          <SafeImage src={selected.photos[0]} alt={selected.title} />
          <div><span className="map-preview-location">{selected.location}</span><strong>{selected.title}</strong><span><b>{money(selected.price)}</b> / night <span className="map-preview-rating">★ {selected.rating?.toFixed(2) || "New"}</span></span><button onClick={() => onOpen?.(selected.id)}>View home <ArrowUpRight size={15} /></button></div>
        </div>}
      </div>
    </div>
  </div>;
}
