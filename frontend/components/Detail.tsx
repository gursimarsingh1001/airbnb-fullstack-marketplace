"use client";
import { useEffect, useState } from "react";
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
import { api, Listing, Quote, money, prettyDate } from "@/lib/api";
import { Calendar, GuestPicker, Modal, amenityIcons } from "./UI";

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
    [error, setError] = useState(""),
    [start, setStart] = useState(initialStart),
    [end, setEnd] = useState(initialEnd),
    [guests, setGuests] = useState(initialGuests),
    [dates, setDates] = useState(false),
    [gallery, setGallery] = useState(false),
    [quote, setQuote] = useState<Quote | null>(null),
    [checkout, setCheckout] = useState(false),
    [busy, setBusy] = useState(false),
    [confirmation, setConfirmation] = useState<number | null>(null);
  useEffect(() => {
    api<Listing>("/listings/" + id, user)
      .then((h) => {
        setHome(h);
        setGuests((n) => Math.min(n, h.max_guests));
      })
      .catch((e) => setError(e.message));
  }, [id, user]);
  useEffect(() => {
    setQuote(null);
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
        if (active) setQuote(q);
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [id, start, end, guests, user]);
  async function reserve() {
    if (!quote) return;
    setBusy(true);
    try {
      const result = await api<{ id: number }>("/bookings", user, "POST", {
        listing_id: id,
        check_in: start,
        check_out: end,
        guests,
      });
      setConfirmation(result.id);
      setCheckout(false);
      setHome(await api<Listing>("/listings/" + id, user));
    } catch (e) {
      setError((e as Error).message);
      setCheckout(false);
    } finally {
      setBusy(false);
    }
  }
  if (!home)
    return (
      <div className="detail-shell">
        <button className="text-button" onClick={onBack}>
          ← Back to exploring
        </button>
        <div className="empty">{error || "Getting your getaway ready…"}</div>
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
    <main className="detail-shell">
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
      <div className="gallery">
        {h.photos.slice(0, 5).map((p, i) => (
          <button
            key={i}
            onClick={() => setGallery(true)}
            aria-label={`Open photo ${i + 1}`}
          >
            <img src={p} alt={`${h.title}, view ${i + 1}`} />
          </button>
        ))}
        <button className="show-photos" onClick={() => setGallery(true)}>
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
              Every booking includes protection for host cancellations, listing
              inaccuracies, and other issues like trouble checking in.
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
                ? `${quote?.nights || ""} nights in ${h.location.split(",")[0]}`
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
                !!(start && end && !quote && !error) ||
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
            <p className="no-charge">You won’t be charged yet</p>
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
      </section>
      <section className="location-section">
        <h2>Where you’ll be</h2>
        <p>
          {h.location}, {h.country}
        </p>
        <div className="location-illustration">
          <div className="map-road r1" />
          <div className="map-road r2" />
          <div className="map-road r3" />
          <div className="map-lake" />
          <span className="map-home">
            <MapPin size={26} />
          </span>
          <span className="map-label">{h.location.split(",")[0]}</span>
          <small>Illustrative map · Exact address shared after booking</small>
        </div>
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
      {gallery && (
        <Modal title="A closer look" wide onClose={() => setGallery(false)}>
          <div className="gallery-modal">
            {h.photos.map((p, i) => (
              <img key={i} src={p} alt={`${h.title}, photo ${i + 1}`} />
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
              <img src={h.photos[0]} alt={h.title} />
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
            <img src={h.photos[0]} alt={h.title} />
            <h3>{h.title}</h3>
            <p>
              {prettyDate(start)} – {prettyDate(end)} · {guests} guests
            </p>
            <p className="muted">
              Confirmation #AB{String(confirmation).padStart(6, "0")}
            </p>
            <button className="primary-button full" onClick={onBooked}>
              View your trip <ChevronRight size={18} />
            </button>
          </div>
        </Modal>
      )}
    </main>
  );
}
