"use client";
import { FormEvent, useState } from "react";
import { api, today } from "@/lib/api";
import { Activity, ActivityKind, activityCategories } from "@/lib/activities";
import { Modal } from "../UI";
type SlotDraft = { day: string; start_time: string; capacity: number };
export default function ActivityEditor({
  kind,
  item,
  user,
  onClose,
  onSaved,
}: {
  kind: ActivityKind;
  item: Activity | null;
  user: number;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [draft, setDraft] = useState({
    kind,
    title: item?.title || "",
    description: item?.description || "",
    location: item?.location || "",
    country: item?.country || "India",
    category: item?.category || activityCategories[kind][0],
    price: item?.price || 2500,
    price_type:
      item?.price_type || (kind === "experiences" ? "person" : "group"),
    duration_minutes: item?.duration_minutes || 60,
    capacity: item?.capacity || 6,
    language: item?.language || "English",
    setting: item?.setting || "Either",
    service_location: item?.service_location || "Either",
    itinerary: item?.itinerary || "",
    included: item?.included || "",
    requirements:
      item?.requirements || "Arrive 10 minutes early. This is a demo offering.",
  });
  const [photos, setPhotos] = useState(item?.photos.join("\n") || "");
  const [slots, setSlots] = useState<SlotDraft[]>(
    (item?.slots || [])
      .filter(
        (s) =>
          `${s.day}T${s.start_time}` >
          new Date(Date.now() + 330 * 60000).toISOString().slice(0, 16),
      )
      .map((s) => ({
        day: s.day,
        start_time: s.start_time,
        capacity: s.capacity,
      })),
  );
  const [slot, setSlot] = useState<SlotDraft>({
    day: "",
    start_time: "09:00",
    capacity: draft.capacity,
  });
  const [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  function addSlot() {
    if (!slot.day || slot.day < today()) {
      setError("Choose today or a future date.");
      return;
    }
    if (
      slots.some((s) => s.day === slot.day && s.start_time === slot.start_time)
    ) {
      setError("This slot already exists.");
      return;
    }
    setSlots([...slots, slot]);
    setError("");
  }
  async function submit(e: FormEvent) {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      await api(
        `/activities/host${item ? `/${item.id}` : ""}`,
        user,
        item ? "PUT" : "POST",
        {
          ...draft,
          photos: photos
            .split("\n")
            .map((s) => s.trim())
            .filter(Boolean),
          slots,
        },
      );
      onSaved();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <Modal
      title={`${item ? "Edit" : "Create"} ${kind === "experiences" ? "experience" : "service"}`}
      wide
      onClose={() => {
        if (!busy) onClose();
      }}
    >
      <form className="activity-editor" onSubmit={submit}>
        <label>
          Title
          <input
            required
            minLength={5}
            maxLength={100}
            value={draft.title}
            onChange={(e) => setDraft({ ...draft, title: e.target.value })}
          />
        </label>
        <label>
          Description
          <textarea
            required
            minLength={30}
            value={draft.description}
            onChange={(e) =>
              setDraft({ ...draft, description: e.target.value })
            }
          />
        </label>
        <div className="activity-form-grid">
          <label>
            Location
            <input
              required
              value={draft.location}
              onChange={(e) => setDraft({ ...draft, location: e.target.value })}
            />
          </label>
          <label>
            Country
            <input
              required
              value={draft.country}
              onChange={(e) => setDraft({ ...draft, country: e.target.value })}
            />
          </label>
          <label>
            Category
            <select
              value={draft.category}
              onChange={(e) => setDraft({ ...draft, category: e.target.value })}
            >
              {activityCategories[kind].map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </label>
          <label>
            Pricing
            <select
              value={draft.price_type}
              onChange={(e) =>
                setDraft({
                  ...draft,
                  price_type: e.target.value as "person" | "group",
                })
              }
            >
              <option value="person">Per person</option>
              {kind === "services" && <option value="group">Per group</option>}
            </select>
          </label>
          <label>
            Price (₹)
            <input
              required
              type="number"
              min="100"
              max="1000000"
              value={draft.price}
              onChange={(e) =>
                setDraft({ ...draft, price: Number(e.target.value) })
              }
            />
          </label>
          <label>
            Duration (minutes)
            <input
              required
              type="number"
              min="30"
              max="480"
              value={draft.duration_minutes}
              onChange={(e) =>
                setDraft({ ...draft, duration_minutes: Number(e.target.value) })
              }
            />
          </label>
          <label>
            Maximum people
            <input
              required
              type="number"
              min="1"
              max="30"
              value={draft.capacity}
              onChange={(e) =>
                setDraft({ ...draft, capacity: Number(e.target.value) })
              }
            />
          </label>
          <label>
            Language
            <select
              value={draft.language}
              onChange={(e) => setDraft({ ...draft, language: e.target.value })}
            >
              {["English", "Hindi", "Italian", "Spanish", "Indonesian"].map(
                (v) => (
                  <option key={v}>{v}</option>
                ),
              )}
            </select>
          </label>
          <label>
            Setting
            <select
              value={draft.setting}
              onChange={(e) => setDraft({ ...draft, setting: e.target.value })}
            >
              {["Indoor", "Outdoor", "Either"].map((v) => (
                <option key={v}>{v}</option>
              ))}
            </select>
          </label>
          <label>
            Service location
            <select
              value={draft.service_location}
              onChange={(e) =>
                setDraft({ ...draft, service_location: e.target.value })
              }
            >
              {["At your stay", "Provider location", "Either"].map((v) => (
                <option key={v}>{v}</option>
              ))}
            </select>
          </label>
        </div>
        <label>
          Photo URLs (one HTTPS URL per line)
          <textarea
            required
            value={photos}
            onChange={(e) => setPhotos(e.target.value)}
            placeholder="https://images.unsplash.com/…"
          />
        </label>
        <label>
          What guests will do (one step per line)
          <textarea
            required
            minLength={10}
            value={draft.itinerary}
            onChange={(e) => setDraft({ ...draft, itinerary: e.target.value })}
          />
        </label>
        <label>
          What’s included (one item per line)
          <textarea
            required
            minLength={5}
            value={draft.included}
            onChange={(e) => setDraft({ ...draft, included: e.target.value })}
          />
        </label>
        <label>
          Requirements
          <textarea
            required
            minLength={5}
            value={draft.requirements}
            onChange={(e) =>
              setDraft({ ...draft, requirements: e.target.value })
            }
          />
        </label>
        <fieldset>
          <legend>Availability · India time (IST)</legend>
          <p>
            Publish at least one future slot. Booked slots cannot be removed or
            reduced below their reservations.
          </p>
          <div className="activity-form-grid">
            <label>
              Available date
              <input
                type="date"
                min={today()}
                value={slot.day}
                onChange={(e) => setSlot({ ...slot, day: e.target.value })}
              />
            </label>
            <label>
              Start time
              <input
                type="time"
                value={slot.start_time}
                onChange={(e) =>
                  setSlot({ ...slot, start_time: e.target.value })
                }
              />
            </label>
            <label>
              Slot capacity
              <input
                type="number"
                min="1"
                max={draft.capacity}
                value={slot.capacity}
                onChange={(e) =>
                  setSlot({ ...slot, capacity: Number(e.target.value) })
                }
              />
            </label>
            <button type="button" className="dark-button" onClick={addSlot}>
              Add time slot
            </button>
          </div>
          <div className="activity-slot-list">
            {slots.map((s, i) => (
              <div key={`${s.day}-${s.start_time}`}>
                <span>
                  {s.day} · {s.start_time} · {s.capacity} places
                </span>
                <button
                  type="button"
                  className="text-button"
                  aria-label={`Remove slot ${s.day} ${s.start_time}`}
                  onClick={() => setSlots(slots.filter((_, n) => n !== i))}
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        </fieldset>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        <div className="activity-actions">
          <button
            type="button"
            className="text-button"
            disabled={busy}
            onClick={onClose}
          >
            Cancel
          </button>
          <button type="submit" className="primary-button" disabled={busy}>
            {busy
              ? "Saving…"
              : item
                ? "Save changes"
                : `Publish ${kind === "experiences" ? "experience" : "service"}`}
          </button>
        </div>
      </form>
    </Modal>
  );
}
