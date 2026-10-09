"use client";
import MarketplaceHeader from "./layout/MarketplaceHeader";
import FilterModal from "./search/FilterModal";
import HomeSearchBar from "./search/HomeSearchBar";
import ActivitySearchBar from "./search/ActivitySearchBar";
import Inspiration from "./layout/Inspiration";
import ActivityBrowse from "./activities/ActivityBrowse";
import ActivityDetail from "./activities/ActivityDetail";
import ActivityCard from "./activities/ActivityCard";
import ActivityHost from "./activities/ActivityHost";
import { TripTab } from "./activities/ActivityTrips";
import TripsPage from "./bookings/TripsPage";
import {
  Activity,
  ActivityKind,
  ActivitySearch,
  activityCategories,
} from "@/lib/activities";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  Search,
  Globe,
  UserRound,
  ChevronRight,
  ArrowUpRight,
  Heart,
  Map,
  BriefcaseBusiness,
  Sparkles,
  SlidersHorizontal,
  X,
  Check,
  ArrowLeft,
} from "lucide-react";
import {
  api,
  Listing,
  Booking,
  User,
  money,
  prettyDate,
  categories,
  amenityNames,
  today,
} from "@/lib/api";
import {
  Avatar,
  Modal,
  Calendar,
  GuestPicker,
  ListingCard,
  categoryIcons,
  Empty,
  Loading,
  SafeImage,
} from "./UI";
import Detail from "./listings/ListingDetail";
import Host from "./host/HostDashboard";
import dynamic from "next/dynamic";

const StayMap = dynamic(() => import("./maps/StayMap"), {
  ssr: false,
  loading: () => <Loading />,
});

const guest: User = {
  id: 1,
  name: "Alex Morgan",
  role: "guest",
  avatar: "AM",
  joined_year: 2024,
};
import {
  defaultFilters,
  Filters,
  SearchState,
  searchStorageKey,
  emptySearch,
  validDate,
} from "@/lib/search";
const themeStorageKey = "airbnb-theme-v1";

export default function Marketplace() {
  const [user, setUser] = useState<User>(guest),
    [ready, setReady] = useState(false),
    [users, setUsers] = useState<User[]>([]),
    [route, setRoute] = useState("explore"),
    [theme, setTheme] = useState<"light" | "dark">("light"),
    [compactSearch, setCompactSearch] = useState(false),
    [menu, setMenu] = useState(false),
    [modal, setModal] = useState(""),
    [toast, setToast] = useState(""),
    [q, setQ] = useState(""),
    [start, setStart] = useState(""),
    [end, setEnd] = useState(""),
    [guests, setGuests] = useState(1),
    [search, setSearch] = useState<SearchState>({
      q: "",
      start: "",
      end: "",
      guests: 1,
    }),
    [category, setCategory] = useState(""),
    [filters, setFilters] = useState<Filters>(defaultFilters),
    [draftFilters, setDraftFilters] = useState<Filters>(defaultFilters),
    [page, setPage] = useState(1),
    [sort, setSort] = useState("recommended"),
    [mapHomes, setMapHomes] = useState<Listing[]>([]),
    [mapLoading, setMapLoading] = useState(false),
    [mapError, setMapError] = useState(""),
    [homes, setHomes] = useState<Listing[]>([]),
    [total, setTotal] = useState(0),
    [pages, setPages] = useState(1),
    [loading, setLoading] = useState(true),
    [error, setError] = useState(""),
    [wishlist, setWishlist] = useState<Listing[]>([]),
    [wishlistLoading, setWishlistLoading] = useState(true),
    [wishlistError, setWishlistError] = useState(""),
    [trips, setTrips] = useState<Booking[]>([]),
    [tripsLoading, setTripsLoading] = useState(true),
    [tripsError, setTripsError] = useState(""),
    [reviewing, setReviewing] = useState<Booking | null>(null),
    [reviewRating, setReviewRating] = useState(5),
    [reviewComment, setReviewComment] = useState(""),
    [reviewBusy, setReviewBusy] = useState(false),
    [cancel, setCancel] = useState<Booking | null>(null),
    [busy, setBusy] = useState(false),
    [refresh, setRefresh] = useState(0),
    [mapView, setMapView] = useState(false);
  const [activityFavorites, setActivityFavorites] = useState<Activity[]>([]);
  const [footerVisible, setFooterVisible] = useState(false);
  const footerBottom = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const footer = footerBottom.current;
    if (!footer) return;
    const observer = new IntersectionObserver(([entry]) =>
      setFooterVisible(entry.isIntersecting),
    );
    observer.observe(footer);
    return () => observer.disconnect();
  }, []);
  const [activitySavedReady, setActivitySavedReady] = useState(false);
  const [tripTab, setTripTab] = useState<TripTab>("Upcoming");
  const [activitySearch, setActivitySearch] = useState<ActivitySearch>({
    q: "",
    day: "",
    people: 1,
  });
  const [activityQ, setActivityQ] = useState(""),
    [activityDay, setActivityDay] = useState(""),
    [activityPeople, setActivityPeople] = useState(1);
  const [activityCategory, setActivityCategory] = useState("");
  const activityKind: ActivityKind | null = /^(experiences)(\/[1-9]\d*)?$/.test(
    route,
  )
    ? "experiences"
    : /^(services)(\/[1-9]\d*)?$/.test(route)
      ? "services"
      : null;
  const activityId = /^(experiences|services)\/[1-9]\d*$/.test(route)
    ? Number(route.split("/")[1])
    : null;
  const activityBrowse = route === "experiences" || route === "services";
  const headerSearch = route === "explore" || activityBrowse;
  useEffect(() => {
    let frame = 0;
    const update = () => {
      frame = 0;
      setCompactSearch((current) => {
        if (window.innerWidth <= 640 || window.scrollY < 40) return false;
        if (window.scrollY > 70) return true;
        return current;
      });
    };
    const onScroll = () => {
      if (!frame) frame = window.requestAnimationFrame(update);
    };
    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      window.cancelAnimationFrame(frame);
    };
  }, []);
  const currentUser = useRef(user.id);
  const pendingSaves = useRef(new Set<string>());
  const cancelling = useRef(false);
  const reviewInFlight = useRef(false);
  const notify = useCallback((s: string) => setToast(s), []);
  useEffect(() => {
    let saved: "light" | "dark" = "light";
    try {
      const value = localStorage.getItem(themeStorageKey);
      if (value === "light" || value === "dark") saved = value;
    } catch {
      /* The theme toggle still works for this visit. */
    }
    setTheme(saved);
    document.documentElement.dataset.theme = saved;
  }, []);
  const navigate = (target: string) => {
    const path = /^(experiences|services)(\/|$)/.test(target)
      ? `/${target}`
      : `/#${target}`;
    window.history.pushState(null, "", path);
    setRoute(target);
    setMapView(false);
    setMenu(false);
    setModal("");
    window.scrollTo({ top: 0, behavior: "instant" });
  };
  useEffect(() => {
    const controller = new AbortController();
    try {
      const stored = JSON.parse(
        localStorage.getItem(searchStorageKey) ||
          sessionStorage.getItem(searchStorageKey) ||
          "null",
      );
      if (stored) {
        const applied = stored.search || {};
        const datesValid =
          validDate(applied.start) &&
          validDate(applied.end) &&
          applied.start >= today() &&
          applied.end > applied.start;
        const restored: SearchState = {
          q: typeof applied.q === "string" ? applied.q.slice(0, 100) : "",
          start: datesValid ? applied.start : "",
          end: datesValid ? applied.end : "",
          guests:
            Number.isInteger(applied.guests) &&
            applied.guests >= 1 &&
            applied.guests <= 16
              ? applied.guests
              : 1,
        };
        setSearch(restored);
        setQ(restored.q);
        setStart(restored.start);
        setEnd(restored.end);
        setGuests(restored.guests);
        if (categories.includes(stored.category)) setCategory(stored.category);
        if (
          stored.filters &&
          Number.isInteger(stored.filters.min) &&
          Number.isInteger(stored.filters.max) &&
          stored.filters.min >= 0 &&
          stored.filters.max >= stored.filters.min &&
          stored.filters.max <= 1000000
        ) {
          setFilters({
            ...defaultFilters,
            min: stored.filters.min,
            max: stored.filters.max,
            bedrooms:
              Number.isInteger(stored.filters.bedrooms) &&
              stored.filters.bedrooms >= 0 &&
              stored.filters.bedrooms <= 20
                ? stored.filters.bedrooms
                : 0,
            beds:
              Number.isInteger(stored.filters.beds) &&
              stored.filters.beds >= 0 &&
              stored.filters.beds <= 30
                ? stored.filters.beds
                : 0,
            bathrooms:
              Number.isInteger(stored.filters.bathrooms) &&
              stored.filters.bathrooms >= 0 &&
              stored.filters.bathrooms <= 20
                ? stored.filters.bathrooms
                : 0,
            min_rating:
              typeof stored.filters.min_rating === "number" &&
              stored.filters.min_rating >= 0 &&
              stored.filters.min_rating <= 5
                ? stored.filters.min_rating
                : 0,
            max_rating:
              typeof stored.filters.max_rating === "number" &&
              stored.filters.max_rating >= 0 &&
              stored.filters.max_rating <= 5
                ? stored.filters.max_rating
                : 5,
            superhost: stored.filters.superhost === true,
            type: [
              "Villa",
              "Cabin",
              "Cottage",
              "Apartment",
              "Tiny home",
            ].includes(stored.filters.type)
              ? stored.filters.type
              : "",
            amenities: Array.isArray(stored.filters.amenities)
              ? stored.filters.amenities.filter((a: string) =>
                  amenityNames.includes(a),
                )
              : [],
          });
        }
        if (stored.draft) {
          const d = stored.draft;
          if (typeof d.q === "string") setQ(d.q.slice(0, 100));
          if (validDate(d.start) && d.start >= today()) {
            setStart(d.start);
            if (validDate(d.end) && d.end > d.start) setEnd(d.end);
          }
          if (Number.isInteger(d.guests) && d.guests >= 1 && d.guests <= 16)
            setGuests(d.guests);
        }
        if (Number.isInteger(stored.page) && stored.page > 0)
          setPage(stored.page);
        if (
          ["recommended", "price_low", "price_high", "rating"].includes(
            stored.sort,
          )
        )
          setSort(stored.sort);
      }
    } catch {
      /* Browsing still works when session storage is unavailable. */
    }
    try {
      const saved = JSON.parse(
        localStorage.getItem("airbnb-activity-search-v1") || "null",
      );
      if (saved) {
        const restored: ActivitySearch = {
          q: typeof saved.q === "string" ? saved.q.slice(0, 100) : "",
          day: validDate(saved.day) && saved.day >= today() ? saved.day : "",
          people:
            Number.isInteger(saved.people) &&
            saved.people > 0 &&
            saved.people <= 16
              ? saved.people
              : 1,
          category: activityCategories.services.includes(saved.category)
            ? saved.category
            : undefined,
        };
        setActivitySearch(restored);
        setActivityQ(restored.q);
        setActivityDay(restored.day);
        setActivityPeople(restored.people);
        setActivityCategory(restored.category || "");
      }
    } catch {
      /* Search remains usable without browser storage. */
    }
    const change = () => {
      setRoute(
        window.location.hash.slice(1) ||
          window.location.pathname.replace(/^\/|\/$/g, "") ||
          "explore",
      );
      setMapView(false);
    };
    change();
    window.addEventListener("hashchange", change);
    window.addEventListener("popstate", change);
    api<User[]>("/users", 1, "GET", undefined, { signal: controller.signal })
      .then((list) => {
        if (controller.signal.aborted) return;
        setUsers(list);
        let id = 1;
        try {
          id = Number(localStorage.getItem("airbnb-demo-user"));
        } catch {
          /* Fall back to the guest profile. */
        }
        const profile = list.find((u) => u.id === id) || guest;
        currentUser.current = profile.id;
        setUser(profile);
      })
      .catch((e) => {
        if (!controller.signal.aborted) notify(e.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setReady(true);
      });
    return () => {
      controller.abort();
      window.removeEventListener("hashchange", change);
      window.removeEventListener("popstate", change);
    };
  }, [notify]);
  useEffect(() => {
    if (!ready) return;
    try {
      localStorage.setItem(
        searchStorageKey,
        JSON.stringify({
          search,
          category,
          filters,
          page,
          sort,
          draft: { q, start, end, guests },
        }),
      );
    } catch {
      /* Search works without browser storage. */
    }
  }, [ready, search, category, filters, page, sort, q, start, end, guests]);
  useEffect(() => {
    if (ready)
      try {
        localStorage.setItem(
          "airbnb-activity-search-v1",
          JSON.stringify(activitySearch),
        );
      } catch {
        /* optional */
      }
  }, [ready, activitySearch]);
  useEffect(() => {
    if (!ready) return;
    const c = new AbortController();
    setActivitySavedReady(false);
    api<Activity[]>("/activities/favorites", user.id, "GET", undefined, {
      signal: c.signal,
    })
      .then((items) => {
        setActivityFavorites(items);
        setActivitySavedReady(true);
      })
      .catch((e) => {
        if (!c.signal.aborted) notify(e.message);
      });
    return () => c.abort();
  }, [ready, user.id, refresh, notify]);
  async function toggleActivitySave(a: Activity) {
    if (!activitySavedReady) {
      notify("Favorites are still loading. Please try again.");
      return;
    }
    const key = `activity/${user.id}/${a.id}`;
    if (pendingSaves.current.has(key)) return;
    pendingSaves.current.add(key);
    const saved = activityFavorites.some((v) => v.id === a.id);
    try {
      await api(
        `/activities/favorites/${a.id}`,
        user.id,
        saved ? "DELETE" : "PUT",
      );
      if (currentUser.current !== user.id) return;
      setActivityFavorites((list) =>
        saved ? list.filter((v) => v.id !== a.id) : [...list, a],
      );
      notify(saved ? "Removed from wishlist." : "Saved to wishlist.");
    } catch (e) {
      notify((e as Error).message);
    } finally {
      pendingSaves.current.delete(key);
    }
  }
  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(""), 4200);
    return () => clearTimeout(t);
  }, [toast]);
  useEffect(() => {
    if (!ready) return;
    let active = true;
    setLoading(true);
    setError("");
    const params = new URLSearchParams({
      q: search.q,
      category,
      guests: String(search.guests),
      min_price: String(filters.min),
      max_price: String(filters.max),
      property_type: filters.type,
      amenities: filters.amenities.join(","),
      bedrooms: String(filters.bedrooms),
      beds: String(filters.beds),
      bathrooms: String(filters.bathrooms),
      min_rating: String(filters.min_rating),
      max_rating: String(filters.max_rating),
      superhost: String(filters.superhost),
      page: String(page),
      limit: "15",
      sort,
    });
    if (search.start && search.end) {
      params.set("check_in", search.start);
      params.set("check_out", search.end);
    }
    api<{ items: Listing[]; total: number; pages: number }>(
      "/listings?" + params,
      user.id,
    )
      .then((r) => {
        if (active) {
          setHomes(r.items);
          setTotal(r.total);
          setPages(r.pages);
          if (page > Math.max(1, r.pages)) setPage(Math.max(1, r.pages));
        }
      })
      .catch((e) => {
        if (active) setError(e.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [ready, user.id, search, category, filters, page, refresh, sort]);
  useEffect(() => {
    if (!mapView) return;
    const controller = new AbortController();
    setMapLoading(true);
    setMapError("");
    setMapHomes([]);
    const params = new URLSearchParams({
      q: search.q,
      category,
      guests: String(search.guests),
      min_price: String(filters.min),
      max_price: String(filters.max),
      property_type: filters.type,
      amenities: filters.amenities.join(","),
      bedrooms: String(filters.bedrooms),
      beds: String(filters.beds),
      bathrooms: String(filters.bathrooms),
      min_rating: String(filters.min_rating),
      max_rating: String(filters.max_rating),
      superhost: String(filters.superhost),
      limit: "50",
      sort,
    });
    if (search.start && search.end) {
      params.set("check_in", search.start);
      params.set("check_out", search.end);
    }
    async function loadMap() {
      const collected: Listing[] = [];
      let count = 1;
      for (let p = 1; p <= count; p++) {
        params.set("page", String(p));
        const result = await api<{ items: Listing[]; pages: number }>(
          "/listings?" + params,
          user.id,
          "GET",
          undefined,
          { signal: controller.signal },
        );
        count = result.pages;
        collected.push(...result.items);
      }
      if (!controller.signal.aborted) setMapHomes(collected);
    }
    void loadMap()
      .catch((e) => {
        if (!controller.signal.aborted) setMapError(e.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setMapLoading(false);
      });
    return () => controller.abort();
  }, [mapView, search, category, filters, sort, user.id, refresh]);
  useEffect(() => {
    if (!ready) return;
    let active = true;
    setWishlistLoading(true);
    setWishlistError("");
    api<Listing[]>("/wishlists", user.id)
      .then((r) => {
        if (active) setWishlist(r);
      })
      .catch((e) => {
        if (active) setWishlistError(e.message);
      })
      .finally(() => {
        if (active) setWishlistLoading(false);
      });
    if (route === "trips") {
      setTripsLoading(true);
      setTripsError("");
      api<Booking[]>("/bookings", user.id)
        .then((r) => {
          if (active) setTrips(r);
        })
        .catch((e) => {
          if (active) setTripsError(e.message);
        })
        .finally(() => {
          if (active) setTripsLoading(false);
        });
    }
    return () => {
      active = false;
    };
  }, [ready, user.id, route, refresh]);
  useEffect(() => {
    const close = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMenu(false);
    };
    window.addEventListener("keydown", close);
    return () => window.removeEventListener("keydown", close);
  }, []);
  async function toggleSave(h: Listing) {
    if (!ready || wishlistLoading || wishlistError) {
      notify("Your wishlist is still loading. Please try again shortly.");
      return;
    }
    const pendingKey = `${user.id}/${h.id}`;
    if (pendingSaves.current.has(pendingKey)) return;
    pendingSaves.current.add(pendingKey);
    const exists = wishlist.some((w) => w.id === h.id);
    try {
      await api("/wishlists/" + h.id, user.id, exists ? "DELETE" : "PUT");
      if (currentUser.current !== user.id) return;
      setWishlist((w) => (exists ? w.filter((x) => x.id !== h.id) : [...w, h]));
      notify(
        exists
          ? "Removed from your wishlist."
          : "Saved to your wishlist. A little inspiration for later.",
      );
    } catch (e) {
      notify((e as Error).message);
    } finally {
      pendingSaves.current.delete(pendingKey);
    }
  }
  function searchHomes() {
    if ((start && !end) || (!start && end)) {
      setModal("dates");
      notify("Choose both check-in and checkout to search.");
      return;
    }
    if (
      start &&
      (start < today() ||
        end <= start ||
        (Date.parse(end) - Date.parse(start)) / 86400000 > 90)
    ) {
      setModal("dates");
      notify("Choose a future stay between 1 and 90 nights.");
      return;
    }
    setSearch({ q: q.trim(), start, end, guests });
    setPage(1);
    navigate("explore");
  }
  function clear() {
    setQ("");
    setStart("");
    setEnd("");
    setGuests(1);
    setCategory("");
    setFilters(defaultFilters);
    setSearch(emptySearch);
    setPage(1);
  }
  function switchUser(u: User, target?: string) {
    currentUser.current = u.id;
    setUser(u);
    if (u.id !== user.id) {
      setWishlist([]);
      setTrips([]);
      setWishlistLoading(true);
      setTripsLoading(true);
    }
    setCancel(null);
    setReviewing(null);
    try {
      localStorage.setItem("airbnb-demo-user", String(u.id));
    } catch {
      /* Keep the profile for this session. */
    }
    setModal("");
    setMenu(false);
    notify(`You’re browsing as ${u.name}.`);
    if (target) navigate(target);
    else if (route === "host" && u.role !== "host") navigate("explore");
  }
  function host() {
    if (user.role === "host") navigate("host");
    else setModal("host-profile");
  }
  async function cancelTrip() {
    if (!cancel || cancelling.current) return;
    cancelling.current = true;
    setBusy(true);
    try {
      await api("/bookings/" + cancel.id, user.id, "DELETE");
      notify("Reservation cancelled. Your dates have been released.");
      setCancel(null);
      setRefresh((n) => n + 1);
    } catch (e) {
      notify((e as Error).message);
    } finally {
      cancelling.current = false;
      setBusy(false);
    }
  }
  async function submitReview(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!reviewing || reviewInFlight.current) return;
    reviewInFlight.current = true;
    setReviewBusy(true);
    try {
      await api(`/bookings/${reviewing.id}/review`, user.id, "POST", {
        rating: reviewRating,
        comment: reviewComment.trim(),
      });
      notify("Thanks for sharing your stay with other guests.");
      setReviewing(null);
      setReviewComment("");
      setRefresh((value) => value + 1);
    } catch (e) {
      notify((e as Error).message);
    } finally {
      reviewInFlight.current = false;
      setReviewBusy(false);
    }
  }
  const listingId = /^listing\/[1-9]\d*$/.test(route)
    ? Number(route.split("/")[1])
    : null;
  const filterCount =
    (filters.min > 0 || filters.max < 1000000 ? 1 : 0) +
    (filters.type ? 1 : 0) +
    filters.amenities.length +
    [
      filters.bedrooms,
      filters.beds,
      filters.bathrooms,
      filters.min_rating,
      filters.max_rating < 5,
      filters.superhost,
    ].filter(Boolean).length;
  const isExplore = route === "explore";
  const activeFilters: { key: string; label: string; remove: () => void }[] =
    [];
  if (category)
    activeFilters.push({
      key: "category",
      label: category,
      remove: () => setCategory(""),
    });
  if (search.q)
    activeFilters.push({
      key: "location",
      label: search.q,
      remove: () => {
        setQ("");
        setSearch((s) => ({ ...s, q: "" }));
      },
    });
  if (search.start)
    activeFilters.push({
      key: "dates",
      label: `${prettyDate(search.start)} – ${prettyDate(search.end)}`,
      remove: () => {
        setStart("");
        setEnd("");
        setSearch((s) => ({ ...s, start: "", end: "" }));
      },
    });
  if (search.guests > 1)
    activeFilters.push({
      key: "guests",
      label: `${search.guests} guests`,
      remove: () => {
        setGuests(1);
        setSearch((s) => ({ ...s, guests: 1 }));
      },
    });
  if (filters.min > 0 || filters.max < 1000000)
    activeFilters.push({
      key: "price",
      label:
        filters.max === 1000000
          ? `From ${money(filters.min)} / night`
          : `${money(filters.min)} – ${money(filters.max)} / night`,
      remove: () => setFilters((f) => ({ ...f, min: 0, max: 1000000 })),
    });
  if (filters.type)
    activeFilters.push({
      key: "type",
      label: filters.type,
      remove: () => setFilters((f) => ({ ...f, type: "" })),
    });
  (["bedrooms", "beds", "bathrooms"] as const).forEach((key) => {
    if (filters[key])
      activeFilters.push({
        key,
        label: `${filters[key]}+ ${key}`,
        remove: () => setFilters((f) => ({ ...f, [key]: 0 })),
      });
  });
  if (filters.min_rating || filters.max_rating < 5)
    activeFilters.push({
      key: "rating",
      label: `Rating ${filters.min_rating}–${filters.max_rating}`,
      remove: () => setFilters((f) => ({ ...f, min_rating: 0, max_rating: 5 })),
    });
  if (filters.superhost)
    activeFilters.push({
      key: "superhost",
      label: "Superhost",
      remove: () => setFilters((f) => ({ ...f, superhost: false })),
    });
  filters.amenities.forEach((amenity) =>
    activeFilters.push({
      key: `amenity-${amenity}`,
      label: amenity,
      remove: () =>
        setFilters((f) => ({
          ...f,
          amenities: f.amenities.filter((a) => a !== amenity),
        })),
    }),
  );
  const savedIds = wishlist.map((h) => h.id);
  const cards = (items: Listing[]) =>
    items.map((h) => (
      <ListingCard
        key={h.id}
        listing={h}
        saved={savedIds.includes(h.id)}
        onSave={() => toggleSave(h)}
        onOpen={() => navigate("listing/" + h.id)}
      />
    ));
  return (
    <>
      <a
        className="skip-link"
        href="#main-content"
        onClick={(event) => {
          event.preventDefault();
          const main = document.getElementById("main-content");
          main?.focus();
          main?.scrollIntoView();
        }}
      >
        Skip to main content
      </a>
      <MarketplaceHeader
        headerSearch={headerSearch}
        compactSearch={compactSearch}
        isExplore={isExplore}
        activityKind={activityKind}
        user={user}
        menu={menu}
        theme={theme}
        clear={clear}
        navigate={navigate}
        host={host}
        setMenu={setMenu}
        setModal={setModal}
        setTheme={setTheme}
      >
        {activityBrowse && (
          <ActivitySearchBar
            compactSearch={compactSearch}
            activityKind={activityKind}
            activityQ={activityQ}
            activityDay={activityDay}
            activityPeople={activityPeople}
            activityCategory={activityCategory}
            setActivityQ={setActivityQ}
            setActivityDay={setActivityDay}
            setActivityPeople={setActivityPeople}
            setActivityCategory={setActivityCategory}
            setActivitySearch={setActivitySearch}
          />
        )}
        {isExplore && (
          <HomeSearchBar
            compactSearch={compactSearch}
            q={q}
            setQ={setQ}
            start={start}
            end={end}
            guests={guests}
            setModal={setModal}
            searchHomes={searchHomes}
          />
        )}
      </MarketplaceHeader>
      <nav
        className="marketplace-mobile-sections"
        aria-label="Marketplace sections"
      >
        <button aria-pressed={isExplore} onClick={() => navigate("explore")}>
          Homes
        </button>
        <button
          aria-pressed={activityKind === "experiences"}
          onClick={() => navigate("experiences")}
        >
          Experiences
        </button>
        <button
          aria-pressed={activityKind === "services"}
          onClick={() => navigate("services")}
        >
          Services
        </button>
      </nav>
      {activityBrowse && ready && activityKind && (
        <ActivityBrowse
          key={`${activityKind}-${JSON.stringify(activitySearch)}`}
          kind={activityKind}
          user={user.id}
          search={{
            ...activitySearch,
            category:
              activityKind === "services" ? activitySearch.category : undefined,
          }}
          favorites={activityFavorites.map((a) => a.id)}
          onSave={toggleActivitySave}
          navigate={navigate}
        />
      )}
      {activityId && activityKind && ready && (
        <ActivityDetail
          key={`${activityId}-${user.id}`}
          id={activityId}
          kind={activityKind}
          user={user.id}
          saved={activityFavorites.some((a) => a.id === activityId)}
          onSave={toggleActivitySave}
          navigate={navigate}
          notify={notify}
        />
      )}
      {isExplore && (
        <>
          <div className="category-bar">
            <div className="category-scroll">
              {["All homes", ...categories].map((c, i) => {
                const Icon = categoryIcons[i];
                return (
                  <button
                    key={c}
                    className={`category ${category === c || (!category && i === 0) ? "active" : ""}`}
                    onClick={() => {
                      setCategory(i === 0 ? "" : c);
                      setPage(1);
                    }}
                  >
                    <Icon size={25} strokeWidth={1.6} />
                    <span>{c}</span>
                  </button>
                );
              })}
            </div>
            <button
              className={`filter-button ${filterCount ? "filtered" : ""}`}
              onClick={() => {
                setDraftFilters(filters);
                setModal("filters");
              }}
            >
              <SlidersHorizontal size={17} /> Filters{" "}
              {filterCount > 0 && <span>{filterCount}</span>}
            </button>
          </div>
          <main id="main-content" tabIndex={-1} className="explore-shell">
            {!search.q &&
              !category &&
              !filterCount &&
              !search.start &&
              page === 1 && (
                <section
                  className="destination-discovery"
                  aria-label="Explore destinations"
                >
                  <div className="discovery-title">
                    <h2>Where will your next story begin?</h2>
                    <span>Coast, mountains, or somewhere in between</span>
                  </div>
                  <div className="destination-cards">
                    {[
                      [
                        "Goa",
                        "Salt air & slow mornings",
                        "photo-1499793983690-e29da59ef1c2",
                      ],
                      [
                        "Himachal",
                        "A little closer to the clouds",
                        "photo-1449158743715-0a90ebb6d2d8",
                      ],
                      [
                        "Kerala",
                        "Green views, everywhere",
                        "photo-1470770841072-f978cf4d019e",
                      ],
                      [
                        "Bali",
                        "Your island state of mind",
                        "photo-1613977257363-707ba9348227",
                      ],
                    ].map(([destination, caption, photo]) => (
                      <button
                        key={destination}
                        className="destination-card"
                        onClick={() => {
                          setQ(destination);
                          setSearch({ ...search, q: destination });
                          setPage(1);
                        }}
                      >
                        <SafeImage
                          src={`https://images.unsplash.com/${photo}?auto=format&fit=crop&w=600&q=80`}
                          alt=""
                        />
                        <span>
                          <strong>{destination}</strong>
                          <small>{caption}</small>
                        </span>
                        <ArrowUpRight size={22} />
                      </button>
                    ))}
                  </div>
                </section>
              )}
            <div className="explore-heading">
              <div>
                <div className="eyebrow">A LITTLE CHANGE OF SCENERY</div>
                <h1>
                  {search.q
                    ? `Stays in ${search.q}`
                    : category
                      ? `${category}. Endless possibilities.`
                      : "Find your kind of getaway."}
                </h1>
                <p>
                  {search.q || category
                    ? "Thoughtfully hosted homes. A place to make your own."
                    : "Extraordinary places. A little closer to feeling at home."}
                </p>
              </div>
              <div className="results-note">
                <span className="green-dot" />
                {loading
                  ? "Finding lovely places…"
                  : `${total} beautiful places to stay`}
                <span className="results-dates">
                  {search.start
                    ? `${prettyDate(search.start)} – ${prettyDate(search.end)}`
                    : "A new favourite is waiting"}
                </span>
                <label className="sort-control">
                  Sort by
                  <select
                    value={sort}
                    onChange={(event) => {
                      setSort(event.target.value);
                      setPage(1);
                    }}
                  >
                    <option value="recommended">Recommended</option>
                    <option value="price_low">Price: low to high</option>
                    <option value="price_high">Price: high to low</option>
                    <option value="rating">Highest rated</option>
                  </select>
                </label>
              </div>
            </div>
            {activeFilters.length > 0 ? (
              <div
                className="active-filters"
                role="group"
                aria-label="Active filters"
              >
                {activeFilters.map((filter) => (
                  <button
                    key={filter.key}
                    className="filter-chip"
                    aria-label={`Remove ${filter.label} filter`}
                    onClick={() => {
                      filter.remove();
                      setPage(1);
                    }}
                  >
                    {filter.label} <X size={14} aria-hidden="true" />
                  </button>
                ))}
                {activeFilters.length > 1 && (
                  <button className="clear-filters" onClick={clear}>
                    Clear all filters
                  </button>
                )}
              </div>
            ) : null}
            {loading ? (
              <Loading />
            ) : error ? (
              <Empty
                title="Let’s try that again"
                text={error}
                action={
                  <button
                    className="dark-button"
                    onClick={() => setRefresh((n) => n + 1)}
                  >
                    Try again
                  </button>
                }
              />
            ) : homes.length ? (
              <>
                <div className="listing-grid">{cards(homes)}</div>
                <div className="explore-more">
                  <h3>Keep exploring. Your next favourite is out there.</h3>
                  {pages > 1 && (
                    <div className="pagination">
                      <button
                        className="circle-button"
                        disabled={page <= 1}
                        aria-label="Previous page"
                        onClick={() => {
                          setPage(page - 1);
                          window.scrollTo({ top: 220, behavior: "smooth" });
                        }}
                      >
                        <ArrowLeft size={17} />
                      </button>
                      {Array.from({ length: pages }, (_, i) => i)
                        .filter(
                          (i) =>
                            i === 0 ||
                            i === pages - 1 ||
                            Math.abs(i + 1 - page) <= 1,
                        )
                        .map((i) => (
                          <button
                            key={i}
                            className={`circle-button ${page === i + 1 ? "active" : ""}`}
                            aria-label={`Page ${i + 1}`}
                            aria-current={page === i + 1 ? "page" : undefined}
                            onClick={() => {
                              setPage(i + 1);
                              window.scrollTo({ top: 220, behavior: "smooth" });
                            }}
                          >
                            {i + 1}
                          </button>
                        ))}
                      <button
                        className="circle-button"
                        disabled={page >= pages}
                        aria-label="Next page"
                        onClick={() => {
                          setPage(page + 1);
                          window.scrollTo({ top: 220, behavior: "smooth" });
                        }}
                      >
                        <ChevronRight size={17} />
                      </button>
                    </div>
                  )}
                  <p>
                    Showing {(page - 1) * 15 + 1}–{Math.min(page * 15, total)}{" "}
                    of {total} homes
                  </p>
                </div>
              </>
            ) : (
              <Empty
                title="A different search might do the trick"
                text="Try a nearby destination, different dates, or fewer filters."
                action={
                  <button className="dark-button" onClick={clear}>
                    Explore all homes
                  </button>
                }
              />
            )}
            <section className="hosting-invitation">
              <div>
                <p className="eyebrow">A SPACE WORTH SHARING</p>
                <h2>Your place could be someone’s favourite getaway.</h2>
                <p>
                  Create a listing, welcome guests, and manage your reservations
                  in one place.
                </p>
                <button className="dark-button" onClick={host}>
                  Explore hosting <ArrowUpRight size={17} />
                </button>
              </div>
              <SafeImage
                src="https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=900&q=80"
                alt="A welcoming living room with comfortable seating"
              />
            </section>
          </main>
          {!loading && homes.length > 0 && (
            <button
              className={`map-toggle${footerVisible ? " map-toggle-hidden" : ""}`}
              tabIndex={footerVisible ? -1 : undefined}
              aria-hidden={footerVisible || undefined}
              onClick={() => setMapView(!mapView)}
            >
              {mapView ? "Show homes" : "Show map"}
              <Map size={17} />
            </button>
          )}
        </>
      )}
      {listingId !== null && ready && (
        <Detail
          key={`${listingId}-${user.id}`}
          id={listingId}
          user={user.id}
          saved={savedIds.includes(listingId)}
          onSave={() => {
            api<Listing>("/listings/" + listingId, user.id)
              .then(toggleSave)
              .catch((e) => notify(e.message));
          }}
          onBack={() => navigate("explore")}
          onBooked={() => {
            setRefresh((n) => n + 1);
            navigate("trips");
          }}
          notify={notify}
          initialStart={search.start}
          initialEnd={search.end}
          initialGuests={search.guests}
        />
      )}
      {route === "wishlists" && (
        <main id="main-content" tabIndex={-1} className="workspace-shell">
          <p className="eyebrow">KEEP THE GOOD ONES CLOSE</p>
          <h1>Your wishlists</h1>
          <p className="muted page-subtitle">
            Places you love. Trips you haven’t taken yet.
          </p>
          <h2>Homes</h2>
          {wishlistLoading ? (
            <Loading />
          ) : wishlistError ? (
            <Empty
              title="Your wishlist couldn’t load"
              text={wishlistError}
              action={
                <button
                  className="dark-button"
                  onClick={() => setRefresh((n) => n + 1)}
                >
                  Try again
                </button>
              }
            />
          ) : wishlist.length ? (
            <div className="listing-grid">{cards(wishlist)}</div>
          ) : (
            <Empty
              title="Your next adventure starts with a heart"
              text="Tap the heart on any home to save it here for later."
              action={
                <button
                  className="dark-button"
                  onClick={() => navigate("explore")}
                >
                  Start exploring
                </button>
              }
            />
          )}
          <h2 className="activity-section-title">Experiences & services</h2>
          {!activitySavedReady ? (
            <p>Loading saved offerings…</p>
          ) : activityFavorites.length ? (
            <div className="activity-grid">
              {activityFavorites.map((a) => (
                <ActivityCard
                  key={a.id}
                  item={a}
                  saved
                  onSave={toggleActivitySave}
                  navigate={navigate}
                />
              ))}
            </div>
          ) : (
            <p className="muted">
              Save an experience or service to find it here.
            </p>
          )}
        </main>
      )}
      {route === "trips" && (
        <TripsPage
          user={user}
          trips={trips}
          tripsLoading={tripsLoading}
          tripsError={tripsError}
          tripTab={tripTab}
          setTripTab={setTripTab}
          setRefresh={setRefresh}
          navigate={navigate}
          notify={notify}
          setCancel={setCancel}
          setReviewing={setReviewing}
          setReviewRating={setReviewRating}
          setReviewComment={setReviewComment}
        />
      )}
      {route.startsWith("host") && (
        <nav className="provider-nav" aria-label="Hosting sections">
          <button onClick={() => navigate("host")}>Homes & overview</button>
          <button onClick={() => navigate("host-experiences")}>
            Experiences
          </button>
          <button onClick={() => navigate("host-services")}>Services</button>
        </nav>
      )}
      {(route === "host-experiences" || route === "host-services") &&
        (user.role === "host" ? (
          <ActivityHost
            key={`${route}-${user.id}`}
            kind={route === "host-experiences" ? "experiences" : "services"}
            user={user}
            navigate={navigate}
            notify={notify}
          />
        ) : (
          <main className="workspace-shell">
            <Empty
              title="Choose a host profile"
              text="Providers manage their offerings with a demo host profile."
              action={
                <button
                  className="primary-button"
                  onClick={() => setModal("host-profile")}
                >
                  Choose host profile
                </button>
              }
            />
          </main>
        ))}
      {route === "host" &&
        (user.role === "host" ? (
          <Host
            key={user.id}
            user={user}
            notify={notify}
            onOpen={(id) => navigate("listing/" + id)}
            onChanged={() => setRefresh((n) => n + 1)}
          />
        ) : (
          <main id="main-content" tabIndex={-1} className="workspace-shell">
            <Empty
              title="Make yourself at home, host"
              text="Choose a demo host profile to create and manage listings."
              action={
                <button
                  className="primary-button"
                  onClick={() => setModal("host-profile")}
                >
                  Choose host profile
                </button>
              }
            />
          </main>
        ))}
      {!ready && listingId !== null && <Loading />}
      {listingId === null &&
        !activityKind &&
        ![
          "explore",
          "trips",
          "wishlists",
          "host",
          "host-experiences",
          "host-services",
        ].includes(route) && (
          <main id="main-content" tabIndex={-1} className="workspace-shell">
            <Empty
              title="We couldn’t find that page"
              text="This link may be incomplete or out of date."
              action={
                <button
                  className="dark-button"
                  onClick={() => navigate("explore")}
                >
                  Back to exploring
                </button>
              }
            />
          </main>
        )}
      <footer>
        <div className="footer-main">
          <Inspiration
            onChoose={(destination) => {
              setQ(destination);
              setStart("");
              setEnd("");
              setGuests(1);
              setSearch({ q: destination, start: "", end: "", guests: 1 });
              setCategory("");
              setFilters(defaultFilters);
              setPage(1);
              navigate("explore");
              window.scrollTo({ top: 0, behavior: "smooth" });
            }}
          />
        </div>
        <div className="footer-bottom" ref={footerBottom}>
          <span>© 2026 Airbnb clone · An independent assignment project</span>
          <div>
            <button onClick={() => setModal("about")}>About this demo</button>
            <span>·</span>
            <button onClick={() => setModal("help")}>Help centre</button>
          </div>
          <div className="footer-locale">
            <Globe size={15} /> English (IN)<strong>₹ INR</strong>
          </div>
        </div>
      </footer>
      <nav className="mobile-nav" aria-label="Mobile navigation">
        <button
          className={isExplore ? "active" : ""}
          onClick={() => navigate("explore")}
        >
          <Search />
          Explore
        </button>
        <button
          className={route === "wishlists" ? "active" : ""}
          onClick={() => navigate("wishlists")}
        >
          <Heart />
          Wishlists
        </button>
        <button
          className={route === "trips" ? "active" : ""}
          onClick={() => navigate("trips")}
        >
          <BriefcaseBusiness />
          Trips
        </button>
        <button onClick={() => setModal("profiles")}>
          <UserRound />
          Profile
        </button>
      </nav>
      {modal === "dates" && (
        <Modal title="When’s your getaway?" wide onClose={() => setModal("")}>
          <div className="modal-body">
            <Calendar
              start={start}
              end={end}
              onChange={(s, e) => {
                setStart(s);
                setEnd(e);
              }}
            />
            <div className="form-actions">
              <span className="muted small">
                A little time away goes a long way.
              </span>
              <button className="dark-button" onClick={() => setModal("")}>
                Done
              </button>
            </div>
          </div>
        </Modal>
      )}
      {modal === "guests" && (
        <Modal title="Who’s coming along?" onClose={() => setModal("")}>
          <div className="modal-body">
            <GuestPicker value={guests} onChange={setGuests} />
            <p className="muted small">
              Our homes accommodate up to 16 guests. Each listing has its own
              capacity.
            </p>
            <button
              className="dark-button float-right"
              onClick={() => setModal("")}
            >
              Done
            </button>
          </div>
        </Modal>
      )}
      {modal === "filters" && (
        <FilterModal
          draftFilters={draftFilters}
          setDraftFilters={setDraftFilters}
          setFilters={setFilters}
          setPage={setPage}
          setModal={setModal}
          notify={notify}
        />
      )}
      {(modal === "profiles" || modal === "host-profile") && (
        <Modal
          title={
            modal === "host-profile"
              ? "Step into your hosting space"
              : "Who’s exploring today?"
          }
          onClose={() => setModal("")}
        >
          <div className="modal-body">
            <p className="muted">
              One marketplace, two ways to use it. Guests book and save stays;
              hosts manage their homes and reservations. Choose a demo profile
              below—no password needed.
            </p>
            <div className="profile-options">
              {users
                .filter((u) => modal !== "host-profile" || u.role === "host")
                .map((u) => (
                  <button
                    key={u.id}
                    onClick={() =>
                      switchUser(
                        u,
                        modal === "host-profile" ? "host" : undefined,
                      )
                    }
                  >
                    <Avatar initials={u.avatar} name={u.name} />
                    <span>
                      <strong>{u.name}</strong>
                      <small>
                        {u.role === "host"
                          ? "Host · Manage your homes"
                          : "Guest · Find your next stay"}
                      </small>
                    </span>
                    {u.id === user.id ? (
                      <Check size={20} />
                    ) : (
                      <ChevronRight size={20} />
                    )}
                  </button>
                ))}
            </div>
          </div>
        </Modal>
      )}
      {["language", "help", "about"].includes(modal) && (
        <Modal
          title={
            modal === "language"
              ? "Language & currency"
              : modal === "about"
                ? "About this demo"
                : "A little help, right here"
          }
          onClose={() => {
            setModal("");
          }}
        >
          <div className="modal-body info-modal">
            <div className="empty-icon">
              {modal === "language" ? (
                <Globe size={32} />
              ) : (
                <Sparkles size={32} />
              )}
            </div>
            {modal === "language" ? (
              <>
                <h2>English (India) · ₹ INR</h2>
                <p>
                  This demo displays all prices in Indian rupees. More languages
                  and currencies are coming soon.
                </p>
              </>
            ) : modal === "about" ? (
              <>
                <h2>Built for the love of a good getaway.</h2>
                <p>
                  This is an independent educational Airbnb clone, not an
                  official Airbnb service. Listings, hosts, and reviews are
                  sample data. Property photos are illustrative.
                </p>
                <p>
                  Bookings and host edits are saved, while checkout is
                  simulated. No real payment is processed.
                </p>
              </>
            ) : (
              <>
                <h2>Make yourself at home.</h2>
                <p>
                  Search a destination, choose your dates, and reserve a place
                  you love. Find your reservations under Trips.
                </p>
                <p>
                  Want to host? Switch to a host profile to add and manage
                  homes. Messaging and identity verification are coming soon.
                </p>
              </>
            )}
          </div>
        </Modal>
      )}
      {reviewing && (
        <Modal
          title="Share your stay"
          onClose={() => {
            if (!reviewBusy) setReviewing(null);
          }}
        >
          <form className="modal-body review-form" onSubmit={submitReview}>
            <h2>{reviewing.listing.title}</h2>
            <p className="muted">
              Your review helps future guests know what to expect.
            </p>
            <label>
              Your rating
              <select
                aria-label="Your rating"
                value={reviewRating}
                onChange={(event) =>
                  setReviewRating(Number(event.target.value))
                }
              >
                {[5, 4, 3, 2, 1].map((value) => (
                  <option key={value} value={value}>
                    {value} star{value === 1 ? "" : "s"}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Your review
              <textarea
                aria-label="Your review"
                required
                minLength={10}
                maxLength={1000}
                rows={5}
                value={reviewComment}
                onChange={(event) => setReviewComment(event.target.value)}
                placeholder="What made your stay memorable?"
              />
              <small className="muted">10–1,000 characters</small>
            </label>
            <div className="form-actions">
              <button
                type="button"
                className="text-button"
                disabled={reviewBusy}
                onClick={() => setReviewing(null)}
              >
                Cancel
              </button>
              <button className="primary-button" disabled={reviewBusy}>
                {reviewBusy ? "Sharing…" : "Submit review"}
              </button>
            </div>
          </form>
        </Modal>
      )}
      {cancel && (
        <Modal
          title="Cancel your trip?"
          onClose={() => {
            if (!busy) setCancel(null);
          }}
        >
          <div className="modal-body">
            <h2>{cancel.listing.title}</h2>
            <p>
              {prettyDate(cancel.check_in)} – {prettyDate(cancel.check_out)}
            </p>
            <p>
              Your reservation will be cancelled and these dates will become
              available to other guests. No real payment was taken.
            </p>
            <div className="form-actions">
              <button
                className="text-button"
                disabled={busy}
                onClick={() => setCancel(null)}
              >
                Keep my trip
              </button>
              <button
                className="primary-button"
                disabled={busy}
                onClick={cancelTrip}
              >
                {busy ? "Cancelling…" : "Cancel reservation"}
              </button>
            </div>
          </div>
        </Modal>
      )}
      {mapView && (
        <Modal
          title="Explore the map"
          wide
          className="map-modal"
          onClose={() => setMapView(false)}
        >
          {mapLoading ? (
            <Loading />
          ) : mapError ? (
            <Empty
              title="The map couldn’t load"
              text={mapError}
              action={
                <button
                  className="dark-button"
                  onClick={() => setRefresh((n) => n + 1)}
                >
                  Try again
                </button>
              }
            />
          ) : (
            <StayMap
              homes={mapHomes}
              onOpen={(id) => {
                setMapView(false);
                navigate("listing/" + id);
              }}
            />
          )}
        </Modal>
      )}
      {toast && (
        <div className="toast" role="status">
          <Check size={18} />
          {toast}
          <button
            aria-label="Dismiss notification"
            onClick={() => setToast("")}
          >
            <X size={16} />
          </button>
        </div>
      )}
    </>
  );
}
