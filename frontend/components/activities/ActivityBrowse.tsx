"use client";
import { useEffect, useState } from "react";
import { SlidersHorizontal, Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import {
  Activity,
  ActivityKind,
  ActivitySearch,
  activityCategories,
} from "@/lib/activities";
import { Empty, Loading, Modal } from "../UI";
import ActivityCard from "./ActivityCard";
const defaults = {
  min_price: 0,
  max_price: 1000000,
  min_rating: 0,
  duration: 480,
  language: "",
  setting: "",
  service_location: "",
  time_of_day: "",
};
export default function ActivityBrowse({
  kind,
  user,
  search,
  favorites,
  onSave,
  navigate,
}: {
  kind: ActivityKind;
  user: number;
  search: ActivitySearch;
  favorites: number[];
  onSave: (a: Activity) => void;
  navigate: (p: string) => void;
}) {
  const [category, setCategory] = useState("");
  const [filters, setFilters] = useState(defaults),
    [draft, setDraft] = useState(defaults);
  const [sort, setSort] = useState("recommended"),
    [page, setPage] = useState(1),
    [ready, setReady] = useState(false);
  const [result, setResult] = useState<{
      items: Activity[];
      total: number;
      pages: number;
    } | null>(null),
    [error, setError] = useState("");
  const [open, setOpen] = useState(false),
    [retry, setRetry] = useState(0);
  useEffect(() => {
    let restoredCategory = search.category || "";
    try {
      const s = JSON.parse(
        sessionStorage.getItem(`activity-filters-${kind}`) || "null",
      );
      if (s) {
        restoredCategory = s.category || "";
        if (s.searchCategory !== search.category) restoredCategory = search.category || "";
        setFilters({ ...defaults, ...s.filters });
        setSort(s.sort || "recommended");
      }
    } catch {
      /* Optional draft storage. */
    }
    setCategory(restoredCategory);
    setReady(true);
  }, [kind, search.category]);
  useEffect(() => {
    if (ready)
      try {
        sessionStorage.setItem(
          `activity-filters-${kind}`,
          JSON.stringify({ category, filters, sort, searchCategory: search.category }),
        );
      } catch {
        /* optional */
      }
  }, [ready, kind, category, filters, sort, search.category]);
  useEffect(() => {
    if (!ready) return;
    const controller = new AbortController();
    setResult(null);
    setError("");
    const params = new URLSearchParams({
      kind,
      q: search.q,
      people: String(search.people),
      category,
      sort,
      page: String(page),
    });
    if (search.day) params.set("day", search.day);
    Object.entries(filters).forEach(([k, v]) => params.set(k, String(v)));
    api<{ items: Activity[]; total: number; pages: number }>(
      `/activities?${params}`,
      user,
      "GET",
      undefined,
      { signal: controller.signal },
    )
      .then((r) => {
        setResult(r);
        if (page > Math.max(1, r.pages)) setPage(Math.max(1, r.pages));
      })
      .catch((e) => {
        if (!controller.signal.aborted) setError(e.message);
      });
    return () => controller.abort();
  }, [
    kind,
    user,
    search.q,
    search.day,
    search.people,
    category,
    sort,
    page,
    filters,
    retry,
    ready,
  ]);
  const changed = Object.keys(defaults).some(
    (k) =>
      filters[k as keyof typeof filters] !==
      defaults[k as keyof typeof defaults],
  );
  return (
    <main id="main-content" className="explore-shell activity-browse">
      <div className="activity-category-toolbar"><div className="activity-categories">
        <button
          className={!category ? "selected" : ""}
          onClick={() => {
            setCategory("");
            setPage(1);
          }}
        >
          <Sparkles size={18} /> All {kind}
        </button>
        {activityCategories[kind].map((c) => (
          <button
            key={c}
            className={category === c ? "selected" : ""}
            onClick={() => {
              setCategory(c);
              setPage(1);
            }}
          >
            {c}
          </button>
        ))}
        </div><button className="activity-filter-trigger"
          onClick={() => {
            setDraft(filters);
            setOpen(true);
          }}
        >
          <SlidersHorizontal size={17} />
          Filters{changed ? " · On" : ""}
        </button>
      </div>
      <div className="activity-intro">
        <p className="eyebrow">
          {kind === "experiences"
            ? "MAKE A MEMORY, NOT JUST A PLAN"
            : "A LITTLE EXTRA FOR YOUR STAY"}
        </p>
        <h1>
          {search.q
            ? `${kind === "experiences" ? "Experiences" : "Services"} in ${search.q}`
            : kind === "experiences"
              ? "Discover a different side of somewhere."
              : "Make your stay a little more special."}
        </h1>
        <p>
          {kind === "experiences"
            ? "Local hosts. Shared passions. Stories you’ll take home."
            : "Thoughtful services from chefs, photographers, and local experts."}
        </p>
      </div>
      <div className="activity-result-heading">
        <h2>
          {category || (sort === "rating" ? "Top-rated " : "Popular ") + kind}
        </h2>
        <label>
          Sort by{" "}
          <select
            value={sort}
            onChange={(e) => {
              setSort(e.target.value);
              setPage(1);
            }}
          >
            <option value="recommended">Recommended</option>
            <option value="rating">Top rated</option>
            <option value="price_low">Price: low to high</option>
          </select>
        </label>
      </div>
      {changed && (
        <button
          className="text-button"
          onClick={() => {
            setFilters(defaults);
            setPage(1);
          }}
        >
          Clear extra filters
        </button>
      )}
      {error ? (
        <Empty
          title="We couldn’t load these offerings"
          text={error}
          action={
            <button
              className="dark-button"
              onClick={() => setRetry((n) => n + 1)}
            >
              Try again
            </button>
          }
        />
      ) : !result ? (
        <Loading />
      ) : result.items.length ? (
        <>
          <p className="muted">
            {result.total} {kind} · {search.day ? `${search.day} · ` : ""}Times
            shown in India time (IST)
          </p>
          <div className="activity-grid">
            {result.items.map((a) => (
              <ActivityCard
                key={a.id}
                item={a}
                saved={favorites.includes(a.id)}
                onSave={onSave}
                navigate={navigate}
              />
            ))}
          </div>
          <div className="pagination">
            <button
              className="text-button"
              disabled={page === 1}
              onClick={() => setPage((n) => n - 1)}
            >
              Previous
            </button>
            <span>
              Page {page} of {result.pages}
            </span>
            <button
              className="text-button"
              disabled={page === result.pages}
              onClick={() => setPage((n) => n + 1)}
            >
              Next
            </button>
          </div>
        </>
      ) : (
        <Empty
          title="Try a little more flexibility"
          text="No matching offerings. Try another destination, date, or filter."
          action={
            <button
              className="dark-button"
              onClick={() => {
                setCategory("");
                setFilters(defaults);
                setPage(1);
              }}
            >
              Reset categories and filters
            </button>
          }
        />
      )}
      {open && (
        <Modal title={`Filter ${kind}`} onClose={() => setOpen(false)}>
          <form
            className="activity-filter-form"
            onSubmit={(e) => {
              e.preventDefault();
              setFilters(draft);
              setPage(1);
              setOpen(false);
            }}
          >
            <div className="activity-form-grid">
              <label>
                Minimum price (₹)
                <input
                  type="number"
                  min="0"
                  max={draft.max_price}
                  value={draft.min_price}
                  onChange={(e) =>
                    setDraft({ ...draft, min_price: Number(e.target.value) })
                  }
                />
              </label>
              <label>
                Maximum price (₹)
                <input
                  type="number"
                  min={draft.min_price}
                  max="1000000"
                  value={draft.max_price}
                  onChange={(e) =>
                    setDraft({ ...draft, max_price: Number(e.target.value) })
                  }
                />
              </label>
              <label>
                Minimum rating
                <select
                  value={draft.min_rating}
                  onChange={(e) =>
                    setDraft({ ...draft, min_rating: Number(e.target.value) })
                  }
                >
                  <option value="0">Any rating</option>
                  <option value="4">4+</option>
                  <option value="4.5">4.5+</option>
                  <option value="4.9">4.9+</option>
                </select>
              </label>
              <label>
                Maximum duration
                <select
                  value={draft.duration}
                  onChange={(e) =>
                    setDraft({ ...draft, duration: Number(e.target.value) })
                  }
                >
                  <option value="480">Any duration</option>
                  <option value="60">1 hour</option>
                  <option value="120">2 hours</option>
                  <option value="240">4 hours</option>
                </select>
              </label>
              <label>
                Language
                <select
                  value={draft.language}
                  onChange={(e) =>
                    setDraft({ ...draft, language: e.target.value })
                  }
                >
                  {[
                    "",
                    "English",
                    "Hindi",
                    "Italian",
                    "Spanish",
                    "Indonesian",
                  ].map((v) => (
                    <option key={v} value={v}>
                      {v || "Any language"}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Time of day
                <select
                  value={draft.time_of_day}
                  onChange={(e) =>
                    setDraft({ ...draft, time_of_day: e.target.value })
                  }
                >
                  <option value="">Any time</option>
                  <option value="morning">Morning (before noon)</option>
                  <option value="afternoon">Afternoon (12–17)</option>
                  <option value="evening">Evening (after 17)</option>
                </select>
              </label>
              <label>
                Setting
                <select
                  value={draft.setting}
                  onChange={(e) =>
                    setDraft({ ...draft, setting: e.target.value })
                  }
                >
                  {["", "Indoor", "Outdoor", "Either"].map((v) => (
                    <option key={v} value={v}>
                      {v || "Any setting"}
                    </option>
                  ))}
                </select>
              </label>
              {kind === "services" && (
                <label>
                  Service location
                  <select
                    value={draft.service_location}
                    onChange={(e) =>
                      setDraft({ ...draft, service_location: e.target.value })
                    }
                  >
                    {["", "At your stay", "Provider location", "Either"].map(
                      (v) => (
                        <option key={v} value={v}>
                          {v || "Any location"}
                        </option>
                      ),
                    )}
                  </select>
                </label>
              )}
            </div>
            <button className="primary-button" type="submit">
              Show results
            </button>
          </form>
        </Modal>
      )}
    </main>
  );
}
