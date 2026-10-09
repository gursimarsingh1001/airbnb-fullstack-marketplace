"use client";
import { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { dateKey, today, prettyDate } from "@/lib/api";
import { canChooseDate } from "@/lib/calendar";

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
                  const disabled = !canChooseDate(
                    key,
                    start,
                    end,
                    unavailable,
                    today(),
                  );
                  return (
                    <button
                      key={key}
                      disabled={disabled}
                      aria-label={key}
                      title={
                        booked(key)
                          ? disabled
                            ? "Unavailable"
                            : "Available for checkout only"
                          : undefined
                      }
                      aria-pressed={key === start || key === end}
                      className={`${key === start || key === end ? "selected" : ""} ${key > start && key < end ? "in-range" : ""}`}
                      onClick={() => choose(key)}
                      onKeyDown={(event) => {
                        const offsets: Record<string, number> = {
                          ArrowLeft: -1,
                          ArrowRight: 1,
                          ArrowUp: -7,
                          ArrowDown: 7,
                        };
                        const offset = offsets[event.key];
                        if (!offset) return;
                        event.preventDefault();
                        const buttons = Array.from(
                          event.currentTarget
                            .closest(".calendar")!
                            .querySelectorAll<HTMLButtonElement>(
                              ".calendar-grid button",
                            ),
                        ).filter(
                          (button) => button.getClientRects().length > 0,
                        );
                        let index =
                          buttons.indexOf(event.currentTarget) + offset;
                        while (
                          index >= 0 &&
                          index < buttons.length &&
                          buttons[index].disabled
                        )
                          index += Math.sign(offset);
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
      <p className="calendar-help">
        Crossed-out dates are unavailable. Checkout may be on another guest’s
        arrival date.
      </p>
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
