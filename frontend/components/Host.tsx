"use client";
import { useCallback, useEffect, useRef, useState, FormEvent } from "react";
import {
  Plus,
  Pencil,
  Trash2,
  ArrowUpRight,
  Home,
  CalendarDays,
  IndianRupee,
  ImagePlus,
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
import { Modal, Empty, SafeImage } from "./UI";
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
  onChanged,
}: {
  user: User;
  notify: (s: string) => void;
  onOpen: (id: number) => void;
  onChanged: () => void;
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
    [uploading, setUploading] = useState(false),
    [saving, setSaving] = useState(false),
    [deleting, setDeleting] = useState<Listing | null>(null),
    [formError, setFormError] = useState("");
  const inFlight = useRef(false);
  const uploadInFlight = useRef(false);
  const loadVersion = useRef(0);
  const load = useCallback(async (signal?: AbortSignal) => {
    const version = ++loadVersion.current;
    setError("");
    try {
      const result = await api<{ listings: Listing[]; bookings: Booking[] }>(
      "/host/dashboard",
      user.id,
      "GET", undefined, { signal },
      );
      if (!signal?.aborted && version === loadVersion.current) setData(result);
    } catch (e) {
      if (!signal?.aborted && version === loadVersion.current) setError((e as Error).message);
    }
  }, [user.id]);
  useEffect(() => {
    const controller = new AbortController();
    setData(null);
    void load(controller.signal);
    return () => { controller.abort(); };
  }, [load]);
  function openEditor(h?: Listing) {
    setDraft(h ? Object.fromEntries(Object.keys(blank).map((key) => [key, h[key as keyof Listing]])) as Draft : blank);
    setPhotos(h ? h.photos.join("\n") : "");
    setEdit(h?.id ?? null);
    setFormError("");
  }
  async function uploadPhotos(files: FileList | null) {
    if (!files?.length || uploadInFlight.current) return;
    const selected = Array.from(files);
    const current = photos.split(/\r?\n/).map((value) => value.trim()).filter(Boolean);
    if (current.length + selected.length > 12) {
      setFormError("A listing can have up to 12 photos.");
      return;
    }
    if (selected.some((file) => !["image/jpeg", "image/png", "image/webp"].includes(file.type) || file.size < 1 || file.size > 3 * 1024 * 1024)) {
      setFormError("Choose JPEG, PNG, or WebP images that are each 3 MB or smaller.");
      return;
    }
    uploadInFlight.current = true;
    setUploading(true);
    setFormError("");
    try {
      for (const file of selected) {
        const dataUrl = await new Promise<string>((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => typeof reader.result === "string" ? resolve(reader.result) : reject(new Error("Could not read this image."));
          reader.onerror = () => reject(new Error("Could not read this image."));
          reader.readAsDataURL(file);
        });
        const contentBase64 = dataUrl.slice(dataUrl.indexOf(",") + 1);
        const result = await api<{ url: string }>("/host/photos", user.id, "POST", {
          content_type: file.type,
          content_base64: contentBase64,
        });
        setPhotos((previous) => [previous.trim(), result.url].filter(Boolean).join("\n"));
      }
      notify(`${selected.length} photo${selected.length === 1 ? "" : "s"} uploaded to your demo storage.`);
    } catch (e) {
      setFormError((e as Error).message);
    } finally {
      uploadInFlight.current = false;
      setUploading(false);
    }
  }
  async function submit(e: FormEvent) {
    e.preventDefault();
    if (inFlight.current || uploading) return;
    const photoUrls = photos.split("\n").map((s) => s.trim()).filter(Boolean);
    if (!photoUrls.length || photoUrls.length > 12 || photoUrls.some((value) => {
      try {
        const url = new URL(value);
        const localUploadedPhoto = url.protocol === "http:" &&
          ["localhost", "127.0.0.1"].includes(url.hostname) &&
          /^\/api\/photos\/[a-f0-9]{32}\.(jpg|png|webp)$/.test(url.pathname);
        return (url.protocol !== "https:" && !localUploadedPhoto) || !!url.username || !!url.password;
      } catch { return true; }
    })) { setFormError("Add 1–12 valid HTTPS image URLs, one per line, without usernames or passwords."); return; }
    if (draft.title.trim().length < 5 || draft.description.trim().length < 30 || draft.location.trim().length < 2 || draft.country.trim().length < 2) {
      setFormError("Enter a title of at least 5 characters, description of at least 30, and a valid location and country."); return;
    }
    inFlight.current = true;
    setSaving(true);
    setFormError("");
    try {
      await api(
        "/host/listings" + (edit ? "/" + edit : ""),
        user.id,
        edit ? "PUT" : "POST",
        {
          ...draft,
          photos: photoUrls,
        },
      );
      setEdit(false);
      onChanged();
      notify(
        edit
          ? "Your listing has been updated."
          : "Your home is now live. Welcome to hosting!",
      );
      await load();
    } catch (e) {
      setFormError((e as Error).message);
    } finally {
      inFlight.current = false;
      setSaving(false);
    }
  }
  async function remove() {
    if (!deleting || inFlight.current) return;
    inFlight.current = true;
    setSaving(true);
    try {
      await api("/host/listings/" + deleting.id, user.id, "DELETE");
      setDeleting(null);
      onChanged();
      notify("Listing deleted.");
      await load();
    } catch (e) {
      setFormError((e as Error).message);
    } finally {
      inFlight.current = false;
      setSaving(false);
    }
  }
  const field = (key: keyof Draft, value: string | number | string[]) =>
    setDraft((d) => ({ ...d, [key]: value }));
  const active = data?.bookings.filter((b) => b.status === "confirmed") || [];
  return (
    <main id="main-content" tabIndex={-1} className="workspace-shell">
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
      {error && <div role="alert"><p className="form-error">{error}</p><button className="text-button" onClick={() => void load()}>Try again</button></div>}
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
                <SafeImage src={h.photos[0]} alt={h.title} />
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
      {tab === "listings" && data?.listings.length === 0 && <Empty title="Your hosting journey starts here" text="Create your first listing to welcome guests." action={<button className="dark-button" onClick={() => openEditor()}>Create a listing</button>} />}
      {tab === "bookings" && data &&
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
                maxLength={5000}
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
                  minLength={2}
                  maxLength={100}
                  value={draft.location}
                  onChange={(e) => field("location", e.target.value)}
                  placeholder="Manali, Himachal Pradesh"
                />
              </label>
              <label>
                Country
                <input
                  required
                  minLength={2}
                  maxLength={80}
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
                    step={1}
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
            <label className="photo-upload-control">
              <span><ImagePlus size={16} /> Or upload photos</span>
              <input
                type="file"
                accept="image/jpeg,image/png,image/webp"
                multiple
                disabled={uploading || saving}
                onChange={(event) => {
                  void uploadPhotos(event.target.files);
                  event.target.value = "";
                }}
              />
              <small className="muted">JPEG, PNG, or WebP · up to 3 MB each. Stored in the connected Vercel Blob store; URL photos still work without cloud storage.</small>
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
                disabled={saving || uploading}
              >
                Cancel
              </button>
              <button className="primary-button" disabled={saving || uploading}>
                {uploading ? "Uploading photos…" : saving ? "Saving…" : edit ? "Save changes" : "Publish listing"}
                <ArrowUpRight size={18} />
              </button>
            </div>
          </form>
        </Modal>
      )}
      {deleting && (
        <Modal title="Remove this listing?" onClose={() => { if (!saving) setDeleting(null); }}>
          <div className="modal-body">
            <h2>{deleting.title}</h2>
            <p>
              This home will be removed from search and your dashboard. Existing
              trip records are preserved. Listings with an upcoming or ongoing
              confirmed stay cannot be removed.
            </p>
            {formError && (
              <p className="form-error" role="alert">
                {formError}
              </p>
            )}
            <div className="form-actions">
              <button className="text-button" disabled={saving} onClick={() => setDeleting(null)}>
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
