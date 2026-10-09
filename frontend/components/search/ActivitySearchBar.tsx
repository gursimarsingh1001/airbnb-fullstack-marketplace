"use client";
import { useRef } from "react";
import { Search } from "lucide-react";
import { today } from "@/lib/api";
import {
  ActivityKind,
  ActivitySearch,
  activityCategories,
} from "@/lib/activities";
import { compactActivityDate } from "@/lib/search";
type Props = {
  compactSearch: boolean;
  activityKind: ActivityKind | null;
  activityQ: string;
  activityDay: string;
  activityPeople: number;
  activityCategory: string;
  setActivityQ: (value: string) => void;
  setActivityDay: (value: string) => void;
  setActivityPeople: (value: number) => void;
  setActivityCategory: (value: string) => void;
  setActivitySearch: (value: ActivitySearch) => void;
};
export default function ActivitySearchBar({
  compactSearch,
  activityKind,
  activityQ,
  activityDay,
  activityPeople,
  activityCategory,
  setActivityQ,
  setActivityDay,
  setActivityPeople,
  setActivityCategory,
  setActivitySearch,
}: Props) {
  const activityDateInput = useRef<HTMLInputElement>(null);
  const openActivityDatePicker = () => {
    const input = activityDateInput.current;
    if (!input) return;
    try {
      if (typeof input.showPicker === "function") input.showPicker();
      else {
        input.focus();
        input.click();
      }
    } catch {
      input.focus();
      input.click();
    }
  };
  return (
    <div className="search-wrap activity-header-search">
      <form
        className="search-bar"
        onSubmit={(e) => {
          e.preventDefault();
          setActivitySearch({
            q: activityQ.trim(),
            day: activityDay,
            people: activityPeople,
            category:
              activityKind === "services" ? activityCategory : undefined,
          });
        }}
      >
        <label className="search-destination">
          <strong>Where</strong>
          <input
            aria-label="Activity destination"
            list="activity-destinations"
            placeholder={compactSearch ? "Anywhere" : "Search destinations"}
            value={activityQ}
            onChange={(e) => setActivityQ(e.target.value)}
          />
        </label>
        <datalist id="activity-destinations">
          {[
            "Goa",
            "Jaipur",
            "Bali",
            "Manali",
            "Rome",
            "Mumbai",
            "Barcelona",
            "Delhi",
            "London",
            "Udaipur",
          ].map((v) => (
            <option key={v}>{v}</option>
          ))}
        </datalist>
        <span className="search-divider" />
        <div className="search-segment activity-date-segment">
          <strong>Date</strong>
          <input
            ref={activityDateInput}
            className="activity-date-input"
            id="activity-date-input"
            aria-label="Activity date"
            type="date"
            min={today()}
            value={activityDay}
            onChange={(e) => setActivityDay(e.target.value)}
          />
          <button
            type="button"
            className="activity-date-summary"
            aria-label={`Choose activity date, ${compactActivityDate(activityDay)}`}
            onClick={openActivityDatePicker}
          >
            {compactActivityDate(activityDay)}
          </button>
        </div>
        <span className="search-divider" />
        {activityKind === "services" ? (
          <label className="search-segment">
            <strong>Service</strong>
            <select
              aria-label="Service type"
              value={activityCategory}
              onChange={(e) => setActivityCategory(e.target.value)}
            >
              <option value="">Any service</option>
              {activityCategories.services.map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </label>
        ) : (
          <label className="search-segment">
            <strong>Guests</strong>
            <select
              aria-label="Activity guests"
              value={activityPeople}
              onChange={(e) => setActivityPeople(Number(e.target.value))}
            >
              {Array.from({ length: 16 }, (_, i) => (
                <option value={i + 1} key={i}>
                  {i + 1} {i ? "guests" : "guest"}
                </option>
              ))}
            </select>
          </label>
        )}
        <button className="search-submit" aria-label={`Search ${activityKind}`}>
          <Search size={21} />
        </button>
      </form>
    </div>
  );
}
