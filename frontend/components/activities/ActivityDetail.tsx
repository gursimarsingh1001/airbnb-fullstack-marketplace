"use client";
import { useEffect, useRef, useState } from "react";
import {
  Heart,
  Star,
  Clock,
  Users,
  Globe,
  Share2,
  CheckCircle2,
} from "lucide-react";
import { api, money, today } from "@/lib/api";
import {
  Activity,
  ActivityBooking,
  ActivityQuote,
  kindLabel,
} from "@/lib/activities";
import { Avatar, Empty, Loading, Modal, SafeImage } from "../UI";
export default function ActivityDetail({
  id,
  user,
  kind,
  saved,
  onSave,
  navigate,
  notify,
}: {
  id: number;
  user: number;
  kind: string;
  saved: boolean;
  onSave: (a: Activity) => void;
  navigate: (s: string) => void;
  notify: (s: string) => void;
}) {
  const [item, setItem] = useState<Activity | null>(null),
    [error, setError] = useState(""),
    [reload, setReload] = useState(0);
  const [day, setDay] = useState(""),
    [slot, setSlot] = useState(0),
    [people, setPeople] = useState(1),
    [gallery, setGallery] = useState(false);
  const [quote, setQuote] = useState<ActivityQuote | null>(null),
    [quoteError, setQuoteError] = useState(""),
    [checkout, setCheckout] = useState(false),
    [busy, setBusy] = useState(false),
    [confirmation, setConfirmation] = useState<ActivityBooking | null>(null);
  const submitting = useRef(false);
  useEffect(() => {
    const controller = new AbortController();
    setItem(null);
    setError("");
    api<Activity>(`/activities/${id}`, user, "GET", undefined, {
      signal: controller.signal,
    })
      .then((a) => {
        if (a.kind !== kind)
          throw new Error("This offering is not in this section.");
        setItem(a);
      })
      .catch((e) => {
        if (!controller.signal.aborted) setError(e.message);
      });
    return () => controller.abort();
  }, [id, user, kind, reload]);
  useEffect(() => {
    setQuote(null);
    setQuoteError("");
    if (!slot) return;
    const controller = new AbortController();
    api<ActivityQuote>(
      "/activities/quote",
      user,
      "POST",
      { slot_id: slot, people },
      { signal: controller.signal },
    )
      .then(setQuote)
      .catch((e) => {
        if (!controller.signal.aborted) setQuoteError(e.message);
      });
    return () => controller.abort();
  }, [slot, people, user, reload]);
  async function reserve() {
    if (!quote || submitting.current) return;
    submitting.current = true;
    setBusy(true);
    const body = { slot_id: slot, people, expected_total: quote.total };
    const key = `activity-attempt-${user}-${JSON.stringify(body)}`;
    let token = crypto.randomUUID();
    try {
      token = sessionStorage.getItem(key) || token;
      sessionStorage.setItem(key, token);
    } catch {
      /* in-flight guard remains */
    }
    try {
      const booking = await api<ActivityBooking>(
        "/activities/bookings",
        user,
        "POST",
        body,
        { headers: { "Idempotency-Key": token } },
      );
      try {
        sessionStorage.removeItem(key);
      } catch {
        /* optional */
      }
      setConfirmation(booking);
      setCheckout(false);
      notify("Booking confirmed.");
    } catch (e) {
      setCheckout(false);
      setQuoteError((e as Error).message);
      setReload((n) => n + 1);
      notify((e as Error).message);
    } finally {
      submitting.current = false;
      setBusy(false);
    }
  }
  if (error)
    return (
      <main className="workspace-shell">
        <Empty
          title="This offering couldn’t load"
          text={error}
          action={
            <button className="dark-button" onClick={() => navigate(kind)}>
              Back to {kind}
            </button>
          }
        />
      </main>
    );
  if (!item) return <Loading />;
  const a = item;
  const slots = (a.slots || []).filter((s) => s.day === day);
  const dates = [...new Set((a.slots || []).map((s) => s.day))];
  const breakdown = quote && (
    <div className="price-breakdown">
      <div>
        <span>
          {money(quote.unit_price)} ×{" "}
          {quote.price_type === "person" ? `${people} guests` : "1 group"}
        </span>
        <span>{money(quote.subtotal)}</span>
      </div>
      <div>
        <span>Service fee (10%)</span>
        <span>{money(quote.service_fee)}</span>
      </div>
      <div className="total">
        <strong>Total (INR)</strong>
        <strong>{money(quote.total)}</strong>
      </div>
    </div>
  );
  return (
    <main id="main-content" className="detail-shell activity-detail">
      <button className="text-button" onClick={() => navigate(a.kind)}>
        ← Back to {a.kind}
      </button>
      <div className="activity-title">
        <div>
          <p className="eyebrow">
            {kindLabel(a.kind)} · {a.category}
          </p>
          <h1>{a.title}</h1>
          <p>
            <Star size={15} fill="currentColor" />{" "}
            {a.rating?.toFixed(2) || "New"} · {a.review_count} reviews ·{" "}
            {a.location}, {a.country}
          </p>
        </div>
        <div className="activity-actions">
          <button
            className="text-button"
            aria-pressed={saved}
            onClick={() => onSave(a)}
          >
            <Heart size={18} fill={saved ? "#ff385c" : "none"} />
            {saved ? "Saved" : "Save"}
          </button>
          <button
            className="text-button"
            onClick={() => {
              void navigator.clipboard
                .writeText(window.location.href)
                .then(() => notify("Link copied."))
                .catch(() =>
                  notify("Copy the address from your browser to share."),
                );
            }}
          >
            <Share2 size={18} />
            Share
          </button>
        </div>
      </div>
      <div className="activity-gallery">
        {a.photos.slice(0, 3).map((p, i) => (
          <button
            key={i}
            aria-label={`Open offering photo ${i + 1}`}
            onClick={() => setGallery(true)}
          >
            <SafeImage src={p} alt={`${a.title}, view ${i + 1}`} />
          </button>
        ))}
        <button
          className="activity-gallery-button"
          onClick={() => setGallery(true)}
        >
          Show all photos
        </button>
      </div>
      <div className="activity-detail-columns">
        <section>
          <div className="activity-host">
            <Avatar initials={a.host.avatar} name={a.host.name} large />
            <div>
              <h2>
                {a.kind === "services" ? "Provided" : "Hosted"} by {a.host.name}
              </h2>
              <p>Demo local host · Hosting since {a.host.joined_year}</p>
            </div>
          </div>
          <div className="activity-facts">
            <span>
              <Clock size={19} />
              {a.duration_minutes} minutes
            </span>
            <span>
              <Users size={19} />
              Up to {a.capacity} guests
            </span>
            <span>
              <Globe size={19} />
              {a.language}
            </span>
          </div>
          <p className="activity-description">{a.description}</p>
          <h2>
            {a.kind === "experiences" ? "What you’ll do" : "Your service"}
          </h2>
          <ol className="activity-steps">
            {a.itinerary
              .split("\n")
              .filter(Boolean)
              .map((s, i) => (
                <li key={i}>{s}</li>
              ))}
          </ol>
          <h2>What’s included</h2>
          <ul className="activity-includes">
            {a.included
              .split("\n")
              .filter(Boolean)
              .map((s, i) => (
                <li key={i}>
                  <CheckCircle2 size={18} />
                  {s}
                </li>
              ))}
          </ul>
          <h2>Meet your host</h2>
          <p>
            {a.host.name} welcomes you to {a.location}. Our demo providers share
            thoughtful local experiences and services. Profiles and credentials
            are illustrative, not verified.
          </p>
          <h2>Important information</h2>
          <p>{a.requirements}</p>
          <p>
            {a.setting} · {a.service_location}. All session times use India time
            (IST), including international demo listings.
          </p>
          <h2>Cancellation policy</h2>
          <p>
            Cancel before the session starts for a full mock refund. No real
            payment or appointment is made.
          </p>
        </section>
        <aside className="activity-booking">
          <h2>
            From {money(a.price)}{" "}
            <small>/ {a.price_type === "person" ? "guest" : "group"}</small>
          </h2>
          <label>
            Date
            <select
              aria-label="Session date"
              value={day}
              onChange={(e) => {
                setDay(e.target.value);
                setSlot(0);
              }}
            >
              <option value="">Choose a date</option>
              {dates
                .filter((d) => d >= today())
                .map((d) => (
                  <option key={d}>{d}</option>
                ))}
            </select>
          </label>
          <label>
            Time (IST)
            <select
              aria-label="Session time"
              value={slot}
              onChange={(e) => setSlot(Number(e.target.value))}
              disabled={!day}
            >
              <option value="0">Choose a time</option>
              {slots.map((s) => (
                <option key={s.id} value={s.id} disabled={s.remaining < people}>
                  {s.start_time} ·{" "}
                  {s.remaining >= people
                    ? `${s.remaining} places left`
                    : "Unavailable"}
                </option>
              ))}
            </select>
          </label>
          <label>
            Guests
            <select
              aria-label="Session guests"
              value={people}
              onChange={(e) => setPeople(Number(e.target.value))}
            >
              {Array.from({ length: a.capacity }, (_, i) => (
                <option key={i} value={i + 1}>
                  {i + 1} {i ? "guests" : "guest"}
                </option>
              ))}
            </select>
          </label>
          {quoteError && (
            <p className="form-error" role="alert">
              {quoteError}
            </p>
          )}
          {slot > 0 && !quote && !quoteError && (
            <p role="status">Checking availability…</p>
          )}
          {breakdown}
          <button
            className="primary-button"
            disabled={!quote || busy}
            onClick={() => setCheckout(true)}
          >
            Reserve {kindLabel(a.kind).toLowerCase()}
          </button>
          <p className="muted">Demo reservation · No real charge</p>
          {!dates.length && (
            <p>No dates available yet. Explore another offering.</p>
          )}
        </aside>
      </div>
      <section className="activity-reviews">
        <h2>
          ★ {a.rating?.toFixed(2) || "New"} · {a.review_count} reviews
        </h2>
        <div className="activity-review-grid">
          {a.reviews?.map((r) => (
            <article key={r.id}>
              <div className="activity-host">
                <Avatar initials={r.avatar} name={r.name} />
                <strong>{r.name}</strong>
              </div>
              <p>{"★".repeat(r.rating)}</p>
              <p>{r.comment}</p>
            </article>
          ))}
        </div>
        {!a.review_count && (
          <p>Be part of this host’s first group of guests.</p>
        )}
      </section>
      {gallery && (
        <Modal title={a.title} wide onClose={() => setGallery(false)}>
          <div className="activity-gallery-modal">
            {a.photos.map((p, i) => (
              <SafeImage key={i} src={p} alt={`${a.title}, photo ${i + 1}`} />
            ))}
          </div>
        </Modal>
      )}
      {checkout && quote && (
        <Modal
          title="Confirm your demo reservation"
          onClose={() => {
            if (!busy) setCheckout(false);
          }}
        >
          <h3>{a.title}</h3>
          <p>
            {quote.day} · {quote.start_time}–{quote.end_time} IST · {people}{" "}
            guests
          </p>
          {breakdown}
          <p>
            No payment credentials are collected. This is an educational demo.
          </p>
          <button
            className="primary-button"
            disabled={busy}
            onClick={() => void reserve()}
          >
            {busy ? "Confirming…" : "Confirm demo booking"}
          </button>
        </Modal>
      )}
      {confirmation && (
        <Modal title="You’re booked!" onClose={() => navigate("trips")}>
          <CheckCircle2 size={40} />
          <h3>{a.title}</h3>
          <p>Confirmation #ACT{confirmation.id}</p>
          <p>
            {confirmation.day} · {confirmation.start_time} IST ·{" "}
            {confirmation.people} guests
          </p>
          <p>
            Server-confirmed total: <strong>{money(confirmation.total)}</strong>
          </p>
          <button className="primary-button" onClick={() => navigate("trips")}>
            View My Trips
          </button>
        </Modal>
      )}
    </main>
  );
}
