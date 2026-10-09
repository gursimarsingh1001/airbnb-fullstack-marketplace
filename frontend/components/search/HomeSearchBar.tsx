"use client";
import { Search, CalendarDays, UserRound } from "lucide-react";
import { prettyDate } from "@/lib/api";
import { compactDateSummary } from "@/lib/search";

type Props = {
  compactSearch: boolean;
  q: string;
  setQ: (value: string) => void;
  start: string;
  end: string;
  guests: number;
  setModal: (value: string) => void;
  searchHomes: () => void;
};
export default function HomeSearchBar({
  compactSearch,
  q,
  setQ,
  start,
  end,
  guests,
  setModal,
  searchHomes,
}: Props) {
  return (
    <div className="search-wrap">
      <form
        className="search-bar"
        onSubmit={(e) => {
          e.preventDefault();
          searchHomes();
        }}
      >
        <label className="search-destination">
          <strong>Where</strong>
          <input
            aria-label="Search destinations"
            list="home-destinations"
            placeholder={compactSearch ? "Anywhere" : "Search destinations"}
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </label>
        <datalist id="home-destinations">
          {[
            "Goa",
            "Manali",
            "Jaipur",
            "Bali",
            "Kerala",
            "Mumbai",
            "Delhi",
            "Coorg",
            "Udaipur",
          ].map((d) => (
            <option key={d}>{d}</option>
          ))}
        </datalist>
        <span className="search-divider" />
        <button
          type="button"
          className="search-segment checkin-segment"
          onClick={() => setModal("dates")}
        >
          <strong>Check in</strong>
          <span className={start ? "has-value" : ""}>
            {compactSearch ? compactDateSummary(start, end) : prettyDate(start)}
          </span>
        </button>
        <span className="search-divider checkout-divider" />
        <button
          type="button"
          className="search-segment checkout-segment"
          tabIndex={compactSearch ? -1 : undefined}
          aria-hidden={compactSearch}
          onClick={() => setModal("dates")}
        >
          <strong>Check out</strong>
          <span className={end ? "has-value" : ""}>{prettyDate(end)}</span>
        </button>
        <span className="search-divider" />
        <button
          type="button"
          className="search-segment guests-segment"
          onClick={() => setModal("guests")}
        >
          <strong>Who</strong>
          <span>{guests > 1 ? `${guests} guests` : "Add guests"}</span>
        </button>
        <button className="search-submit" aria-label="Search homes">
          <Search size={21} />
        </button>
      </form>
      <div className="mobile-search-options">
        <button onClick={() => setModal("dates")}>
          <CalendarDays size={14} />
          {start
            ? prettyDate(start) + (end ? " – " + prettyDate(end) : "")
            : "Any week"}
        </button>
        <span>·</span>
        <button onClick={() => setModal("guests")}>
          <UserRound size={14} />
          {guests > 1 ? `${guests} guests` : "Add guests"}
        </button>
      </div>
    </div>
  );
}
