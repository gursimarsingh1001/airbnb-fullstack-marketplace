"use client";
import { Dispatch, SetStateAction } from "react";
import { amenityNames } from "@/lib/api";
import { defaultFilters, Filters } from "@/lib/search";
import { Modal } from "../shared/Modal";
type Props = {
  draftFilters: Filters;
  setDraftFilters: Dispatch<SetStateAction<Filters>>;
  setFilters: (filters: Filters) => void;
  setPage: (page: number) => void;
  setModal: (modal: string) => void;
  notify: (message: string) => void;
};
export default function FilterModal({
  draftFilters,
  setDraftFilters,
  setFilters,
  setPage,
  setModal,
  notify,
}: Props) {
  return (
    <Modal title="Filters" onClose={() => setModal("")}>
      <div className="modal-body filter-modal">
        <section>
          <h2>Price range</h2>
          <p className="muted">Nightly prices before fees</p>
          <div className="price-histogram">
            {[
              18, 28, 40, 35, 58, 72, 88, 100, 93, 84, 92, 78, 67, 71, 53, 42,
              38, 26, 21, 18, 12, 8,
            ].map((v, i) => (
              <div key={i} style={{ height: v + "%" }} />
            ))}
          </div>
          <div className="form-grid">
            <label>
              Minimum
              <input
                aria-label="Minimum price"
                type="number"
                min={0}
                max={1000000}
                step={1}
                value={draftFilters.min}
                onChange={(e) =>
                  setDraftFilters((f) => ({ ...f, min: +e.target.value }))
                }
              />
            </label>
            <label>
              Maximum
              <input
                aria-label="Maximum price"
                type="number"
                min={draftFilters.min}
                max={1000000}
                step={1}
                value={draftFilters.max}
                onChange={(e) =>
                  setDraftFilters((f) => ({ ...f, max: +e.target.value }))
                }
              />
            </label>
          </div>
        </section>
        <section>
          <h2>Type of place</h2>
          <div className="type-options">
            {["", "Villa", "Cabin", "Cottage", "Apartment", "Tiny home"].map(
              (t) => (
                <button
                  key={t}
                  className={draftFilters.type === t ? "selected" : ""}
                  onClick={() => setDraftFilters((f) => ({ ...f, type: t }))}
                >
                  {t || "Any type"}
                </button>
              ),
            )}
          </div>
        </section>
        <section>
          <h2>Rooms and guest ratings</h2>
          <div className="activity-form-grid">
            {(["bedrooms", "beds", "bathrooms"] as const).map((key) => (
              <label key={key}>
                Minimum {key}
                <select
                  value={draftFilters[key]}
                  onChange={(e) =>
                    setDraftFilters((f) => ({
                      ...f,
                      [key]: Number(e.target.value),
                    }))
                  }
                >
                  {[0, 1, 2, 3, 4, 5].map((n) => (
                    <option key={n} value={n}>
                      {n ? `${n}+` : "Any"}
                    </option>
                  ))}
                </select>
              </label>
            ))}
            <label>
              Minimum rating
              <select
                value={draftFilters.min_rating}
                onChange={(e) =>
                  setDraftFilters((f) => ({
                    ...f,
                    min_rating: Number(e.target.value),
                  }))
                }
              >
                {[0, 3, 4, 4.5, 4.9].map((n) => (
                  <option key={n} value={n}>
                    {n || "Any"}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Maximum rating
              <select
                value={draftFilters.max_rating}
                onChange={(e) =>
                  setDraftFilters((f) => ({
                    ...f,
                    max_rating: Number(e.target.value),
                  }))
                }
              >
                {[3, 4, 4.5, 4.9, 5].map((n) => (
                  <option key={n}>{n}</option>
                ))}
              </select>
            </label>
            <label>
              <input
                type="checkbox"
                checked={draftFilters.superhost}
                onChange={(e) =>
                  setDraftFilters((f) => ({
                    ...f,
                    superhost: e.target.checked,
                  }))
                }
              />
              Superhost homes
            </label>
          </div>
        </section>
        <section>
          <h2>The little essentials</h2>
          <div className="amenity-options">
            {amenityNames.map((a) => (
              <label key={a}>
                <input
                  type="checkbox"
                  checked={draftFilters.amenities.includes(a)}
                  onChange={() =>
                    setDraftFilters((f) => ({
                      ...f,
                      amenities: f.amenities.includes(a)
                        ? f.amenities.filter((x) => x !== a)
                        : [...f.amenities, a],
                    }))
                  }
                />
                {a}
              </label>
            ))}
          </div>
        </section>
        <div className="form-actions">
          <button
            className="text-button"
            onClick={() => setDraftFilters(defaultFilters)}
          >
            Clear all
          </button>
          <button
            className="dark-button"
            onClick={() => {
              if (
                !Number.isInteger(draftFilters.min) ||
                !Number.isInteger(draftFilters.max) ||
                draftFilters.min < 0 ||
                draftFilters.max > 1000000 ||
                draftFilters.min > draftFilters.max ||
                draftFilters.min_rating > draftFilters.max_rating
              ) {
                notify(
                  "Enter whole-rupee prices from ₹0 to ₹10,00,000, with maximum at least minimum.",
                );
                return;
              }
              setFilters(draftFilters);
              setPage(1);
              setModal("");
            }}
          >
            Show homes
          </button>
        </div>
      </div>
    </Modal>
  );
}
