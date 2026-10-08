"use client";
import { useEffect, useRef, useState } from "react";
import {
  ArrowLeft,
  Heart,
  Share,
  Star,
  ShieldCheck,
  KeyRound,
  MapPin,
  ChevronRight,
  Grid2X2,
  CheckCircle2,
  CalendarDays,
  Flag,
  Medal,
} from "lucide-react";
import { api, ApiError, Listing, Quote, money, prettyDate } from "@/lib/api";
import { Calendar, Modal, SafeImage, amenityIcons } from "./UI";
import dynamic from "next/dynamic";

const StayMap = dynamic(() => import("./StayMap"), { ssr: false, loading: () => <div className="map-unavailable">Loading map…</div> });

export default function Detail({
  id,
  user,
  saved,
  onSave,
  onBack,
  onBooked,
  notify,
  initialStart,
  initialEnd,
  initialGuests,
}: {
  id: number;
  user: number;
  saved: boolean;
  onSave: () => void;
  onBack: () => void;
  onBooked: () => void;
  notify: (s: string) => void;
  initialStart: string;
  initialEnd: string;
  initialGuests: number;
}) {
  const [home, setHome] = useState<Listing | null>(null),
    [loadError, setLoadError] = useState(""),
    [error, setError] = useState(""),
    [start, setStart] = useState(initialStart),
    [end, setEnd] = useState(initialEnd),
    [guests, setGuests] = useState(initialGuests),
    [dates, setDates] = useState(false),
    [gallery, setGallery] = useState<number | null>(null),
    [quoted, setQuoted] = useState<{ key: string; value: Quote } | null>(null),
    [quoteVersion, setQuoteVersion] = useState(0),
    [checkout, setCheckout] = useState(false),
    [busy, setBusy] = useState(false),
    [confirmation, setConfirmation] = useState<({ id: number } & Quote) | null>(null);
  const submitting = useRef(false);
  const quoteKey = `${id}/${user}/${start}/${end}/${guests}/${quoteVersion}`;
  const quote = quoted?.key === quoteKey ? quoted.value : null;
  useEffect(() => {
    const controller = new AbortController();
    setHome(null);
    setLoadError("");
    api<Listing>("/listings/" + id, user, "GET", undefined, { signal: controller.signal })
      .then((h) => {
        if (controller.signal.aborted) return;
        setHome(h);
        setGuests((n) => Math.min(n, h.max_guests));
      })
      .catch((e) => { if (!controller.signal.aborted) setLoadError(e.message); });
    return () => controller.abort();
  }, [id, user]);
  useEffect(() => {
    setError("");
    if (!start || !end) return;
    let active = true;
    api<Quote>("/quote", user, "POST", {
      listing_id: id,
      check_in: start,
      check_out: end,
      guests,
    })
      .then((q) => {
        if (active) setQuoted({ key: quoteKey, value: q });
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [id, start, end, guests, user, quoteKey]);
  useEffect(() => {
    if (gallery !== null) document.getElementById(`gallery-photo-${gallery}`)?.scrollIntoView({ block: "nearest" });
  }, [gallery]);
  async function reserve() {
    if (!quote || submitting.current) return;
    submitting.current = true;
    setBusy(true);
    const request = { listing_id: id, check_in: start, check_out: end, guests, expected_total: quote.total };
    const storageKey = `airbnb-booking-attempt:${user}:${JSON.stringify(request)}`;
    let attempt = crypto.randomUUID();
    try {
      attempt = sessionStorage.getItem(storageKey) || attempt;
      sessionStorage.setItem(storageKey, attempt);
    } catch { /* Storage may be disabled; the in-flight lock still prevents double clicks. */ }
    try {
      const result = await api<{ id: number } & Quote>("/bookings", user, "POST", request, {
        headers: { "Idempotency-Key": attempt },
      });
      setConfirmation(result);
      setCheckout(false);
    } catch (e) {
      setError((e as Error).message);
      if (e instanceof ApiError && e.status < 500) {
        notify((e as Error).message);
        setCheckout(false);
        setQuoted(null);
        setQuoteVersion((v) => v + 1);
        api<Listing>("/listings/" + id, user).then(setHome).catch(() => {});
      }
    } finally {
      submitting.current = false;
      setBusy(false);
    }
  }
  if (!home)
    return (
      <div className="detail-shell">
        <button className="text-button" onClick={onBack}>
          ← Back to exploring
        </button>
        <div className="empty" role={loadError ? "alert" : "status"}>{loadError || "Getting your getaway ready…"}</div>
      </div>
    );
  const h = home;
  const breakdown = quote && (
    <div className="price-breakdown">
      <div>
        <span>
          {money(quote.nightly_price)} × {quote.nights} nights
        </span>
        <span>{money(quote.subtotal)}</span>
      </div>
      <div>
        <span>Cleaning fee</span>
        <span>{money(quote.cleaning_fee)}</span>
      </div>
      <div>
        <span>Airbnb service fee</span>
        <span>{money(quote.service_fee)}</span>
      </div>
      <div className="total">
        <strong>
          Total <small>(INR)</small>
        </strong>
        <strong>{money(quote.total)}</strong>
      </div>
    </div>
  );
  return (
    <main id="main-content" tabIndex={-1} className="detail-shell">
      <button className="back-link" onClick={onBack}>
        <ArrowLeft size={17} /> Back to exploring
      </button>
      <h1>{h.title}</h1>
      <div className="detail-subtitle">
        <span>
          <Star size={14} fill="currentColor" /> {h.rating?.toFixed(2) || "New"}{" "}
          ·{" "}
          <a
            href="#reviews"
            onClick={(e) => {
              e.preventDefault();
              document
                .getElementById("reviews")
                ?.scrollIntoView({ behavior: "smooth" });
            }}
          >
            {h.review_count} reviews
          </a>{" "}
          · {h.location}, {h.country}
        </span>
        <div>
          <button
            className="text-button"
            onClick={() => {
              if (!navigator.clipboard) { notify("Copy the address from your browser to share this home."); return; }
              navigator.clipboard
                .writeText(window.location.href)
                .then(() => notify("Link copied. Share your next getaway."))
                .catch(() =>
                  notify(
                    "Copy the address from your browser to share this home.",
                  ),
                );
            }}
          >
            <Share size={16} /> Share
          </button>
          <button className="text-button" onClick={onSave}>
            <Heart
              size={16}
              fill={saved ? "#ff385c" : "none"}
              color={saved ? "#ff385c" : "currentColor"}
            />{" "}
            {saved ? "Saved" : "Save"}
          </button>
        </div>
      </div>
      <div className={`gallery gallery-count-${Math.min(h.photos.length, 5)}`}>
        {h.photos.slice(0, 5).map((p, i) => (
          <button
            key={i}
            onClick={() => setGallery(i)}
            aria-label={`Open photo ${i + 1}`}
          >
            <SafeImage src={p} alt={`${h.title}, view ${i + 1}`} />
          </button>
        ))}
        <button className="show-photos" onClick={() => setGallery(0)}>
          <Grid2X2 size={15} /> Show all photos
        </button>
      </div>
      <div className="detail-columns">
        <div className="detail-main">
          <section className="home-intro">
            <div>
              <h2>
                Entire {h.property_type.toLowerCase()} in{" "}
                {h.location.split(",")[0]}
              </h2>
              <p>
                {h.max_guests} guests · {h.bedrooms} bedrooms · {h.beds} beds ·{" "}
                {h.bathrooms} bathrooms
              </p>
            </div>
            <span className="avatar large">{h.host.avatar}</span>
          </section>
          {h.superhost > 0 && (
            <div className="favourite-banner">
              <Medal size={30} />
              <strong>
                Guest
                <br />
                favourite
              </strong>
              <span>
                One of the most loved homes on Airbnb, according to guests
              </span>
              <b>
                {h.rating?.toFixed(2)}
                <small>★★★★★</small>
              </b>
            </div>
          )}
          <section className="host-line">
            <span className="avatar">{h.host.avatar}</span>
            <div>
              <strong>Hosted by {h.host.name.split(" ")[0]}</strong>
              <p>
                {h.superhost ? "Superhost · " : ""}Hosting since{" "}
                {h.host.joined_year}
              </p>
            </div>
          </section>
          <section className="highlights">
            <div>
              <KeyRound />
              <span>
                <strong>Self check-in</strong>
                <p>Check yourself in with the lockbox.</p>
              </span>
            </div>
            <div>
              <MapPin />
              <span>
                <strong>A beautiful place to switch off</strong>
                <p>Guests love this home’s peaceful surroundings.</p>
              </span>
            </div>
            <div>
              <CalendarDays />
              <span>
                <strong>Flexible plans</strong>
                <p>Cancel before check-in for a full mock refund.</p>
              </span>
            </div>
          </section>
          <section className="description">
            <div className="aircover">
              <span>air</span>cover
            </div>
            <p>
              This is an educational demo. Reservations and cancellation are
              simulated; no real travel protection or insurance is provided.
            </p>
            <hr />
            <p className="long-description">{h.description}</p>
          </section>
          <section>
            <h2>What this place offers</h2>
            <div className="amenities-grid">
              {h.amenities.map((a) => {
                const Icon = amenityIcons[a] || ShieldCheck;
                return (
                  <div key={a}>
                    <Icon size={23} />
                    <span>{a}</span>
                  </div>
                );
              })}
            </div>
          </section>
          <section className="detail-calendar">
            <h2>
              {start && end
                ? `Your stay in ${h.location.split(",")[0]}`
                : "Make time for a little getaway"}
            </h2>
            <p className="muted">
              {start
                ? `${prettyDate(start)} – ${prettyDate(end)}`
                : "Add your travel dates for exact pricing"}
            </p>
            <Calendar
              start={start}
              end={end}
              onChange={(s, e) => {
                setStart(s);
                setEnd(e);
              }}
              unavailable={h.unavailable}
            />
          </section>
        </div>
        <aside>
          <div className="booking-card">
            <div className="booking-heading">
              <span>
                <strong>{money(h.price)}</strong> night
              </span>
              <span>
                <Star size={13} fill="currentColor" />{" "}
                {h.rating?.toFixed(2) || "New"}
              </span>
            </div>
            <div className="booking-fields">
              <button onClick={() => setDates(true)}>
                <b>CHECK-IN</b>
                <span>{prettyDate(start)}</span>
              </button>
              <button onClick={() => setDates(true)}>
                <b>CHECKOUT</b>
                <span>{prettyDate(end)}</span>
              </button>
              <label>
                <b>GUESTS</b>
                <select
                  aria-label="Booking guests"
                  value={guests}
                  onChange={(e) => setGuests(+e.target.value)}
                >
                  {Array.from({ length: h.max_guests }, (_, i) => (
                    <option value={i + 1} key={i}>
                      {i + 1} guest{i ? "s" : ""}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            {error && (
              <p className="form-error" role="alert">
                {error}
              </p>
            )}
            <button
              className="primary-button full"
              disabled={
                busy ||
                !!(start && end && !quote) ||
                h.host_id === user
              }
              onClick={() => {
                if (!start || !end) setDates(true);
                else if (quote) setCheckout(true);
              }}
            >
              {h.host_id === user
                ? "This is your listing"
                : !start || !end
                  ? "Check availability"
                  : "Reserve"}
            </button>
            <p className="no-charge">Demo reservation · No real charge</p>
            {breakdown}
          </div>
          <div className="rare-find">
            <Medal size={28} />
            <span>
              <strong>This is a rare find.</strong> Great places tend to get
              booked quickly.
            </span>
          </div>
          <div className="report-note">
            <Flag size={14} /> Independent assignment demo
          </div>
        </aside>
      </div>
      <section className="reviews" id="reviews">
        <h2>
          <Star fill="currentColor" size={23} /> {h.rating?.toFixed(2) || "New"}{" "}
          · {h.review_count} reviews
        </h2>
        <div className="reviews-grid">
          {h.reviews?.map((r) => (
            <article key={r.id}>
              <div className="host-line">
                <span className="avatar">{r.avatar}</span>
                <div>
                  <strong>{r.name}</strong>
                  <p>
                    {new Date(r.created_at).toLocaleDateString("en-GB", {
                      month: "long",
                      year: "numeric",
                    })}
                  </p>
                </div>
              </div>
              <div className="review-stars">{"★".repeat(r.rating)}</div>
              <p>{r.comment}</p>
            </article>
          ))}
        </div>
        {!h.review_count && <p className="muted">No reviews yet. Be one of this home’s first guests.</p>}
      </section>
      <section className="location-section">
        <h2>Where you’ll be</h2>
        <p>
          {h.location}, {h.country}
        </p>
        <StayMap homes={[h]} compact />
      </section>
      {dates && (
        <Modal title="Choose your dates" wide onClose={() => setDates(false)}>
          <div className="modal-body">
            <Calendar
              start={start}
              end={end}
              onChange={(s, e) => {
                setStart(s);
                setEnd(e);
              }}
              unavailable={h.unavailable}
            />
            <button
              className="dark-button float-right"
              onClick={() => setDates(false)}
            >
              Done
            </button>
          </div>
        </Modal>
      )}
      {gallery !== null && (
        <Modal title="A closer look" wide onClose={() => setGallery(null)}>
          <div className="gallery-modal">
            {h.photos.map((p, i) => (
              <SafeImage id={`gallery-photo-${i}`} key={i} src={p} alt={`${h.title}, photo ${i + 1}`} />
            ))}
          </div>
        </Modal>
      )}
      {checkout && quote && (
        <Modal
          title="Confirm and pay"
          onClose={() => {
            if (!busy) setCheckout(false);
          }}
        >
          <div className="modal-body checkout">
            <div className="checkout-home">
              <SafeImage src={h.photos[0]} alt={h.title} />
              <div>
                <p className="muted">Entire {h.property_type.toLowerCase()}</p>
                <strong>{h.title}</strong>
                <p>
                  <Star size={12} fill="currentColor" /> {h.rating?.toFixed(2)}{" "}
                  · {h.location}
                </p>
              </div>
            </div>
            <h2>Your trip</h2>
            <div className="summary-row">
              <div>
                <strong>Dates</strong>
                <p>
                  {prettyDate(start)} – {prettyDate(end)}
                </p>
              </div>
              <button
                className="text-button"
                onClick={() => {
                  setCheckout(false);
                  setDates(true);
                }}
              >
                Edit
              </button>
            </div>
            <div className="summary-row">
              <div>
                <strong>Guests</strong>
                <p>
                  {guests} guest{guests > 1 ? "s" : ""}
                </p>
              </div>
            </div>
            <hr />
            <h2>Price details</h2>
            {breakdown}
            <div className="mock-payment">
              <ShieldCheck size={24} />
              <div>
                <strong>Demo checkout</strong>
                <p>No payment details needed. No real charge will be made.</p>
              </div>
            </div>
            <p className="small muted">
              Your reservation will be confirmed immediately. You can cancel any
              time before check-in from Trips.
            </p>
            {error && <p className="form-error" role="alert">{error}</p>}
            <button
              className="primary-button full"
              disabled={busy}
              onClick={reserve}
            >
              {busy
                ? "Confirming your stay…"
                : `Confirm reservation · ${money(quote.total)}`}
            </button>
          </div>
        </Modal>
      )}
      {confirmation && (
        <Modal title="You’re going!" onClose={onBooked}>
          <div className="confirmation">
            <div className="success-icon">
              <CheckCircle2 size={48} />
            </div>
            <h2>Your next chapter starts here.</h2>
            <p>You’re all set for {h.location.split(",")[0]}.</p>
            <SafeImage src={h.photos[0]} alt={h.title} />
            <h3>{h.title}</h3>
            <p>
              {prettyDate(start)} – {prettyDate(end)} · {guests} guests
            </p>
            <p className="muted">
              Confirmation #AB{String(confirmation.id).padStart(6, "0")}
            </p>
            <p>Confirmed total: <strong>{money(confirmation.total)}</strong> · {confirmation.nights} nights</p>
            <button className="primary-button full" onClick={onBooked}>
              View your trip <ChevronRight size={18} />
            </button>
          </div>
        </Modal>
      )}
    </main>
  );
}
