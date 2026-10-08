"use client";
import { useEffect, useState, FormEvent } from "react";
import {
  Plus,
  Pencil,
  Trash2,
  ArrowUpRight,
  Home,
  CalendarDays,
  IndianRupee,
  ImagePlus,
  Check,
} from "lucide-react";
import {
  api,
  Listing,
  Booking,
  User,
  money,
  prettyDate,
  amenityNames,
  categories,
} from "@/lib/api";
import { Modal, Empty } from "./UI";
type Draft = {
  title: string;
  description: string;
  location: string;
  country: string;
  category: string;
  property_type: string;
  price: number;
  cleaning_fee: number;
  max_guests: number;
  bedrooms: number;
  beds: number;
  bathrooms: number;
  photos: string[];
  amenities: string[];
};
const blank: Draft = {
  title: "",
  description: "",
  location: "",
  country: "India",
  category: "Countryside",
  property_type: "Cottage",
  price: 5000,
  cleaning_fee: 900,
  max_guests: 4,
  bedrooms: 2,
  beds: 2,
  bathrooms: 1,
  photos: [],
  amenities: ["Wifi", "Kitchen"],
};
export default function Host({
  user,
  notify,
  onOpen,
}: {
  user: User;
  notify: (s: string) => void;
  onOpen: (id: number) => void;
}) {
  const [data, setData] = useState<{
      listings: Listing[];
      bookings: Booking[];
    } | null>(null),
    [error, setError] = useState(""),
    [tab, setTab] = useState("listings"),
    [edit, setEdit] = useState<number | null | false>(false),
    [draft, setDraft] = useState<Draft>(blank),
    [photos, setPhotos] = useState(""),
    [saving, setSaving] = useState(false),
    [deleting, setDeleting] = useState<Listing | null>(null),
    [formError, setFormError] = useState("");
  const load = () =>
    api<{ listings: Listing[]; bookings: Booking[] }>(
      "/host/dashboard",
      user.id,
    )
      .then(setData)
      .catch((e) => setError(e.message));
  useEffect(() => {
    load();
  }, [user.id]); // Profile changes reload its owned homes.
  function openEditor(h?: Listing) {
    setDraft(h ? { ...h } : blank);
    setPhotos(h ? h.photos.join("\n") : "");
    setEdit(h?.id ?? null);
    setFormError("");
  }
  async function submit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setFormError("");
    try {
      await api(
        "/host/listings" + (edit ? "/" + edit : ""),
        user.id,
        edit ? "PUT" : "POST",
        {
          ...draft,
          photos: photos
            .split("\n")
            .map((s) => s.trim())
            .filter(Boolean),
        },
      );
      setEdit(false);
      notify(
        edit
          ? "Your listing has been updated."
          : "Your home is now live. Welcome to hosting!",
      );
      await load();
    } catch (e) {
      setFormError((e as Error).message);
    } finally {
      setSaving(false);
    }
  }
  async function remove() {
    if (!deleting) return;
    setSaving(true);
    try {
      await api("/host/listings/" + deleting.id, user.id, "DELETE");
      setDeleting(null);
      notify("Listing deleted.");
      await load();
    } catch (e) {
      setFormError((e as Error).message);
    } finally {
      setSaving(false);
    }
  }
  const field = (key: keyof Draft, value: string | number | string[]) =>
    setDraft((d) => ({ ...d, [key]: value }));
  const active = data?.bookings.filter((b) => b.status === "confirmed") || [];
  return (
    <main className="workspace-shell">
      <div className="page-title-row">
        <div>
          <p className="eyebrow">YOUR HOSTING SPACE</p>
          <h1>Welcome back, {user.name.split(" ")[0]}.</h1>
          <p className="muted">A little hospitality goes a long way.</p>
        </div>
        <button className="dark-button" onClick={() => openEditor()}>
          <Plus size={19} /> Create a listing
        </button>
      </div>
      {error && <p className="form-error">{error}</p>}
      <div className="stats-grid">
        <div>
          <Home size={23} />
          <span>Active listings</span>
          <strong>{data?.listings.length ?? "—"}</strong>
        </div>
        <div>
          <CalendarDays size={23} />
          <span>Confirmed reservations</span>
          <strong>{active.length}</strong>
        </div>
        <div>
          <IndianRupee size={23} />
          <span>Booked revenue · before fees</span>
          <strong>
            {money(
              active.reduce(
                (a, b) =>
                  a +
                  b.nightly_price *
                    Math.round(
                      (Date.parse(b.check_out) - Date.parse(b.check_in)) /
                        86400000,
                    ),
                0,
              ),
            )}
          </strong>
        </div>
      </div>
      <div className="workspace-tabs">
        <button
          className={tab === "listings" ? "active" : ""}
          onClick={() => setTab("listings")}
        >
          Your listings <span>{data?.listings.length || 0}</span>
        </button>
        <button
          className={tab === "bookings" ? "active" : ""}
          onClick={() => setTab("bookings")}
        >
          Reservations <span>{data?.bookings.length || 0}</span>
        </button>
      </div>
      {!data && !error && (
        <div className="empty">Loading your hosting space…</div>
      )}
      {tab === "listings" && (
        <div className="host-grid">
          {data?.listings.map((h) => (
            <article className="host-card" key={h.id}>
              <button className="host-photo" onClick={() => onOpen(h.id)}>
                <img src={h.photos[0]} alt={h.title} />
                <span>
                  <i /> Live
                </span>
              </button>
              <div className="host-card-copy">
                <h3>{h.title}</h3>
                <p className="muted">{h.location}</p>
                <div className="host-card-bottom">
                  <strong>
                    {money(h.price)} <small>/ night</small>
                  </strong>
                  <div>
                    <button
                      className="icon-button"
                      aria-label={`Edit ${h.title}`}
                      onClick={() => openEditor(h)}
                    >
                      <Pencil size={17} />
                    </button>
                    <button
                      className="icon-button"
                      aria-label={`Delete ${h.title}`}
                      onClick={() => {
                        setDeleting(h);
                        setFormError("");
                      }}
                    >
                      <Trash2 size={17} />
                    </button>
                  </div>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
      {tab === "bookings" &&
        (data?.bookings.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Guest & home</th>
                  <th>Dates</th>
                  <th>Guests</th>
                  <th>Total</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {data.bookings.map((b) => (
                  <tr key={b.id}>
                    <td>
                      <strong>{b.guest_name}</strong>
                      <p>{b.listing.title}</p>
                    </td>
                    <td>
                      {prettyDate(b.check_in)} – {prettyDate(b.check_out)}
                    </td>
                    <td>{b.guests}</td>
                    <td>{money(b.total)}</td>
                    <td>
                      <span className={`status ${b.status}`}>{b.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty
            title="Your next guest is out there"
            text="New reservations will appear here as soon as someone books."
          />
        ))}
      {edit !== false && (
        <Modal
          title={edit ? "Edit your listing" : "Make room for something special"}
          wide
          onClose={() => {
            if (!saving) setEdit(false);
          }}
        >
          <form className="modal-body listing-form" onSubmit={submit}>
            <p className="muted">
              Tell guests what makes your place feel like a getaway.
            </p>
            <label>
              Listing title
              <input
                required
                minLength={5}
                maxLength={100}
                value={draft.title}
                onChange={(e) => field("title", e.target.value)}
                placeholder="A quiet cottage in the hills"
              />
            </label>
            <label>
              Description
              <textarea
                required
                minLength={30}
                rows={4}
                value={draft.description}
                onChange={(e) => field("description", e.target.value)}
                placeholder="Share the little details that make your home special…"
              />
            </label>
            <div className="form-grid">
              <label>
                Location
                <input
                  required
                  value={draft.location}
                  onChange={(e) => field("location", e.target.value)}
                  placeholder="Manali, Himachal Pradesh"
                />
              </label>
              <label>
                Country
                <input
                  required
                  value={draft.country}
                  onChange={(e) => field("country", e.target.value)}
                />
              </label>
              <label>
                Property type
                <select
                  value={draft.property_type}
                  onChange={(e) => field("property_type", e.target.value)}
                >
                  {["Villa", "Cabin", "Cottage", "Apartment", "Tiny home"].map(
                    (t) => (
                      <option key={t}>{t}</option>
                    ),
                  )}
                </select>
              </label>
              <label>
                Category
                <select
                  value={draft.category}
                  onChange={(e) => field("category", e.target.value)}
                >
                  {categories.map((t) => (
                    <option key={t}>{t}</option>
                  ))}
                </select>
              </label>
              {(
                [
                  ["price", "Nightly price (₹)", 500, 1000000],
                  ["cleaning_fee", "Cleaning fee (₹)", 0, 100000],
                  ["max_guests", "Maximum guests", 1, 16],
                  ["bedrooms", "Bedrooms", 1, 20],
                  ["beds", "Beds", 1, 30],
                  ["bathrooms", "Bathrooms", 1, 20],
                ] as const
              ).map(([key, label, min, max]) => (
                <label key={key}>
                  {label}
                  <input
                    required
                    type="number"
                    min={min}
                    max={max}
                    value={draft[key]}
                    onChange={(e) => field(key, +e.target.value)}
                  />
                </label>
              ))}
            </div>
            <label>
              <span>
                <ImagePlus size={16} /> Photo URLs
              </span>
              <textarea
                required
                rows={4}
                value={photos}
                onChange={(e) => setPhotos(e.target.value)}
                placeholder="https://images.unsplash.com/…"
              />
              <small className="muted">
                One https:// image URL per line. Add up to 12 photos; the first
                is your cover.
              </small>
            </label>
            <fieldset>
              <legend>What does your place offer?</legend>
              <div className="amenity-options">
                {amenityNames.map((a) => (
                  <label
                    className={draft.amenities.includes(a) ? "checked" : ""}
                    key={a}
                  >
                    <input
                      type="checkbox"
                      checked={draft.amenities.includes(a)}
                      onChange={() =>
                        field(
                          "amenities",
                          draft.amenities.includes(a)
                            ? draft.amenities.filter((n) => n !== a)
                            : [...draft.amenities, a],
                        )
                      }
                    />
                    {a}
                  </label>
                ))}
              </div>
            </fieldset>
            {formError && (
              <p role="alert" className="form-error">
                {formError}
              </p>
            )}
            <div className="form-actions">
              <button
                type="button"
                className="text-button"
                onClick={() => setEdit(false)}
                disabled={saving}
              >
                Cancel
              </button>
              <button className="primary-button" disabled={saving}>
                {saving ? "Saving…" : edit ? "Save changes" : "Publish listing"}
                <ArrowUpRight size={18} />
              </button>
            </div>
          </form>
        </Modal>
      )}
      {deleting && (
        <Modal title="Delete this listing?" onClose={() => setDeleting(null)}>
          <div className="modal-body">
            <h2>{deleting.title}</h2>
            <p>
              This home will be removed from search and your dashboard. Existing
              trip records are preserved.
            </p>
            {formError && (
              <p className="form-error" role="alert">
                {formError}
              </p>
            )}
            <div className="form-actions">
              <button className="text-button" onClick={() => setDeleting(null)}>
                Keep listing
              </button>
              <button
                className="primary-button"
                disabled={saving}
                onClick={remove}
              >
                {saving ? "Deleting…" : "Delete listing"}
              </button>
            </div>
          </div>
        </Modal>
      )}
    </main>
  );
}
