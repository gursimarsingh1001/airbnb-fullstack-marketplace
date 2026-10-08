"use client";
import { useEffect, useRef, useState } from "react";
import {
  X,
  ChevronLeft,
  ChevronRight,
  Heart,
  Star,
  Check,
  Home,
  Mountain,
  Palmtree,
  Waves,
  Trees,
  Building2,
  Compass,
  House,
  Flower2,
  SlidersHorizontal,
  Wifi,
  Utensils,
  Car,
  Wind,
  Laptop,
  Droplets,
  Fence,
} from "lucide-react";
import { Listing, dateKey, today, money, prettyDate } from "@/lib/api";
import { canChooseDate } from "@/lib/calendar";

/** Keep listing geometry stable when a host's external photo is unavailable. */
export function SafeImage({ src, alt, ...props }: React.ImgHTMLAttributes<HTMLImageElement>) {
  const [failed, setFailed] = useState<string | null>(null);
  const fallback = !src || failed === src;
  return <img {...props} src={fallback ? "/image-placeholder.svg" : src}
    alt={fallback ? `${alt || "Listing photo"} — photo unavailable` : alt}
    onError={() => { if (!fallback && typeof src === "string") setFailed(src); }} />;
}

export const categoryIcons = [
  Compass,
  Mountain,
  Palmtree,
  House,
  Trees,
  Waves,
  Building2,
  Droplets,
  Home,
  Flower2,
];
export const amenityIcons: Record<string, typeof Wifi> = {
  Wifi: Wifi,
  Kitchen: Utensils,
  "Free parking": Car,
  "Air conditioning": Wind,
  Pool: Waves,
  "Mountain view": Mountain,
  "Beach access": Palmtree,
  Washer: Droplets,
  Workspace: Laptop,
  Garden: Fence,
  "Lake view": Waves,
  "Hot tub": Droplets,
};
export function Logo() {
  return (
    <span className="logo">
      <svg
        viewBox="0 0 32 34"
        width="34"
        height="36"
        fill="none"
        aria-hidden="true"
      >
        <path
          d="M16 2C12 2 10.7 7.6 7.2 14.6 4 21 1 26.1 4 29.4c4 4.5 10-2 12-5 2 3 8 9.5 12 5 3-3.3 0-8.4-3.2-14.8C21.3 7.6 20 2 16 2Z"
          stroke="currentColor"
          strokeWidth="2.2"
        />
        <path
          d="M16 24.4c-6-6.8-5-12.7 0-12.7s6 5.9 0 12.7Z"
          stroke="currentColor"
          strokeWidth="2.2"
        />
      </svg>
      <span>airbnb</span>
    </span>
  );
}
export function Modal({
  title,
  children,
  onClose,
  wide = false,
}: {
  title: string;
  children: React.ReactNode;
  onClose: () => void;
  wide?: boolean;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const close = useRef(onClose);
  close.current = onClose;
  useEffect(() => {
    const prior = document.activeElement as HTMLElement;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    // A modal can be nested in a page: make every sibling along that branch
    // inert, while leaving the dialog and its ancestors interactive.
    const inert: { node: HTMLElement; previous: boolean }[] = [];
    let branch: HTMLElement | null = ref.current?.parentElement || null;
    while (branch?.parentElement && branch !== document.body) {
      for (const sibling of branch.parentElement.children) {
        if (sibling !== branch && sibling instanceof HTMLElement) {
          inert.push({ node: sibling, previous: sibling.inert });
          sibling.inert = true;
        }
      }
      branch = branch.parentElement;
    }
    ref.current?.focus();
    const key = (e: KeyboardEvent) => {
      if (e.key === "Escape") close.current();
      if (e.key === "Tab") {
        const els = Array.from(ref.current?.querySelectorAll<HTMLElement>(
          'button:not(:disabled),a[href],input:not(:disabled):not([type="hidden"]),select:not(:disabled),textarea:not(:disabled),[tabindex="0"]',
        ) || []).filter((el) => el.getClientRects().length > 0);
        if (!els?.length) return;
        const first = els[0],
          last = els[els.length - 1];
        if (
          e.shiftKey &&
          (document.activeElement === first ||
            document.activeElement === ref.current)
        ) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    document.addEventListener("keydown", key);
    return () => {
      document.body.style.overflow = overflow;
      inert.forEach(({ node, previous }) => { node.inert = previous; });
      document.removeEventListener("keydown", key);
      prior?.focus();
    };
  }, []);
  return (
    <div
      className="modal-backdrop"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className={`modal ${wide ? "modal-wide" : ""}`}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        ref={ref}
        tabIndex={-1}
      >
        <div className="modal-heading">
          <button
            className="icon-button"
            aria-label="Close dialog"
            onClick={onClose}
          >
            <X size={20} />
          </button>
          <strong>{title}</strong>
          <span />
        </div>
        {children}
      </div>
    </div>
  );
}
export function Calendar({
  start,
  end,
  onChange,
  unavailable = [],
}: {
  start: string;
  end: string;
  onChange: (s: string, e: string) => void;
  unavailable?: { check_in: string; check_out: string }[];
}) {
  const [month, setMonth] = useState(() => {
    const d = start ? new Date(start + "T12:00:00") : new Date();
    return new Date(d.getFullYear(), d.getMonth(), 1);
  });
  const booked = (key: string) =>
    unavailable.some((r) => key >= r.check_in && key < r.check_out);
  const choose = (key: string) => {
    if (!start || end || key <= start) {
      onChange(key, "");
      return;
    }
    const crossing = unavailable.some(
      (r) => start < r.check_out && key > r.check_in,
    );
    if (!crossing) onChange(start, key);
    else onChange(key, "");
  };
  return (
    <div className="calendar">
      <div className="calendar-nav">
        <button
          className="icon-button"
          aria-label="Previous month"
          disabled={
            month <=
            new Date(new Date().getFullYear(), new Date().getMonth(), 1)
          }
          onClick={() =>
            setMonth(new Date(month.getFullYear(), month.getMonth() - 1, 1))
          }
        >
          <ChevronLeft size={19} />
        </button>
        <span>
          {!start || end ? "Select check-in date" : "Select checkout date"}
        </span>
        <button
          className="icon-button"
          aria-label="Next month"
          onClick={() =>
            setMonth(new Date(month.getFullYear(), month.getMonth() + 1, 1))
          }
        >
          <ChevronRight size={19} />
        </button>
      </div>
      <div className="calendar-months">
        {[0, 1].map((offset) => {
          const d = new Date(month.getFullYear(), month.getMonth() + offset, 1);
          const count = new Date(
            d.getFullYear(),
            d.getMonth() + 1,
            0,
          ).getDate();
          return (
            <div className="calendar-month" key={offset}>
              <h4>
                {d.toLocaleDateString("en-GB", {
                  month: "long",
                  year: "numeric",
                })}
              </h4>
              <div className="calendar-grid">
                {["M", "T", "W", "T", "F", "S", "S"].map((v, i) => (
                  <span key={"w" + i} className="weekday">
                    {v}
                  </span>
                ))}
                {Array.from({ length: (d.getDay() + 6) % 7 }, (_, i) => (
                  <span key={"blank" + i} />
                ))}
                {Array.from({ length: count }, (_, i) => {
                  const key = dateKey(
                    new Date(d.getFullYear(), d.getMonth(), i + 1),
                  );
                  const disabled = !canChooseDate(key, start, end, unavailable, today());
                  return (
                    <button
                      key={key}
                      disabled={disabled}
                      aria-label={key}
                      title={booked(key) ? (disabled ? "Unavailable" : "Available for checkout only") : undefined}
                      aria-pressed={key === start || key === end}
                      className={`${key === start || key === end ? "selected" : ""} ${key > start && key < end ? "in-range" : ""}`}
                      onClick={() => choose(key)}
                      onKeyDown={(event) => {
                        const offsets: Record<string, number> = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7 };
                        const offset = offsets[event.key];
                        if (!offset) return;
                        event.preventDefault();
                        const buttons = Array.from(event.currentTarget.closest(".calendar")!.querySelectorAll<HTMLButtonElement>(".calendar-grid button"))
                          .filter((button) => button.getClientRects().length > 0);
                        let index = buttons.indexOf(event.currentTarget) + offset;
                        while (index >= 0 && index < buttons.length && buttons[index].disabled) index += Math.sign(offset);
                        buttons[index]?.focus();
                      }}
                    >
                      {i + 1}
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
      <p className="calendar-help">Crossed-out dates are unavailable. Checkout may be on another guest’s arrival date.</p>
      <div className="calendar-bottom">
        <span>
          {start
            ? `${prettyDate(start)}${end ? " – " + prettyDate(end) : " – Checkout"}`
            : "Choose your perfect getaway"}
        </span>
        <button className="text-button" onClick={() => onChange("", "")}>
          Clear dates
        </button>
      </div>
    </div>
  );
}
export function GuestPicker({
  value,
  onChange,
  max = 16,
}: {
  value: number;
  onChange: (n: number) => void;
  max?: number;
}) {
  return (
    <div className="guest-picker">
      <div>
        <strong>Guests</strong>
        <p>Ages 2 and above</p>
      </div>
      <div className="stepper">
        <button
          className="circle-button"
          aria-label="Remove guest"
          disabled={value <= 1}
          onClick={() => onChange(value - 1)}
        >
          −
        </button>
        <span>{value}</span>
        <button
          className="circle-button"
          aria-label="Add guest"
          disabled={value >= max}
          onClick={() => onChange(value + 1)}
        >
          +
        </button>
      </div>
    </div>
  );
}
export function ListingCard({
  listing: l,
  saved,
  onSave,
  onOpen,
}: {
  listing: Listing;
  saved: boolean;
  onSave: () => void;
  onOpen: () => void;
}) {
  const [photo, setPhoto] = useState(0);
  return (
    <article className="listing-card">
      <div className="card-photo">
        <button
          className="photo-link"
          onClick={onOpen}
          aria-label={`View ${l.title}`}
        >
          <SafeImage
            src={l.photos[photo % l.photos.length]}
            alt={`${l.property_type} in ${l.location}`}
            loading="lazy"
          />
        </button>
        {l.superhost > 0 && (
          <span className="guest-favourite">Guest favourite</span>
        )}
        <button
          className={`heart-button ${saved ? "saved" : ""}`}
          aria-label={`${saved ? "Remove from" : "Save to"} wishlist: ${l.title}`}
          aria-pressed={saved}
          onClick={onSave}
        >
          <Heart size={24} />
        </button>
        {l.photos.length > 1 && <button
          className="photo-next"
          aria-label="Next photo"
          onClick={() => setPhoto((photo + 1) % l.photos.length)}
        >
          <ChevronRight size={17} />
        </button>}
        <div className="photo-dots">
          {l.photos.slice(0, 5).map((_, i) => (
            <span key={i} className={i === photo ? "active" : ""} />
          ))}
        </div>
      </div>
      <button className="card-copy" onClick={onOpen}>
        <div className="card-title">
          <strong>{l.location}</strong>
          <span>
            <Star size={12} fill="currentColor" />
            {l.rating?.toFixed(2) || "New"}
          </span>
        </div>
        <p>{l.title}</p>
        <p>
          {l.category} · {l.bedrooms} bedroom{l.bedrooms > 1 ? "s" : ""}
        </p>
        <div className="card-price">
          <strong>{money(l.price)}</strong> <span>night</span>
        </div>
      </button>
    </article>
  );
}
export function Empty({
  title,
  text,
  action,
}: {
  title: string;
  text: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="empty">
      <div className="empty-icon">
        <Compass size={34} />
      </div>
      <h2>{title}</h2>
      <p>{text}</p>
      {action}
    </div>
  );
}
export function Loading() {
  return (
    <div className="listing-grid">
      {Array.from({ length: 10 }, (_, i) => (
        <div className="skeleton-card" key={i}>
          <div />
          <span />
          <span />
        </div>
      ))}
    </div>
  );
}
export { SlidersHorizontal, Check };
