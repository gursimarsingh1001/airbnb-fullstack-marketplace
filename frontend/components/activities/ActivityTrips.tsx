"use client";
import { useEffect, useState } from "react";
import { api, money } from "@/lib/api";
import { ActivityBooking, activityPath, kindLabel } from "@/lib/activities";
import { Empty, Loading, Modal, SafeImage } from "../UI";
export type TripTab = "Upcoming" | "Past" | "Cancelled";
export default function ActivityTrips({
  user,
  tab,
  navigate,
  notify,
}: {
  user: number;
  tab: TripTab;
  navigate: (p: string) => void;
  notify: (s: string) => void;
}) {
  const [data, setData] = useState<ActivityBooking[] | null>(null),
    [error, setError] = useState(""),
    [cancel, setCancel] = useState<ActivityBooking | null>(null),
    [busy, setBusy] = useState(false),
    [refresh, setRefresh] = useState(0);
  useEffect(() => {
    const c = new AbortController();
    setData(null);
    setError("");
    api<ActivityBooking[]>("/activities/bookings", user, "GET", undefined, {
      signal: c.signal,
    })
      .then(setData)
      .catch((e) => {
        if (!c.signal.aborted) setError(e.message);
      });
    return () => c.abort();
  }, [user, refresh]);
  async function remove() {
    if (!cancel || busy) return;
    setBusy(true);
    try {
      await api(`/activities/bookings/${cancel.id}`, user, "DELETE");
      setCancel(null);
      setRefresh((n) => n + 1);
      notify("Reservation cancelled. Your session has been released.");
    } catch (e) {
      notify((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const now = new Date(Date.now() + 330 * 60000)
    .toISOString()
    .slice(0, 16)
    .replace("T", " ");
  const visible = (data || []).filter((b) =>
    tab === "Cancelled"
      ? b.status === "cancelled"
      : b.status === "confirmed" &&
        (tab === "Past"
          ? `${b.day} ${b.end_time}` <= now
          : `${b.day} ${b.end_time}` > now),
  );
  return (
    <section className="activity-trips">
      <h2>Experiences & services</h2>
      {error ? (
        <Empty
          title="Reservations couldn’t load"
          text={error}
          action={
            <button onClick={() => setRefresh((n) => n + 1)}>Retry</button>
          }
        />
      ) : !data ? (
        <Loading />
      ) : !visible.length ? (
        <p className="muted">
          No {tab.toLowerCase()} experiences or services yet.
        </p>
      ) : (
        <div className="trips-grid">
          {visible.map((b) => (
            <article className="trip-card" key={b.id}>
              <button onClick={() => navigate(activityPath(b.activity))}>
                <SafeImage src={b.activity.photos[0]} alt={b.activity.title} />
              </button>
              <div className="trip-copy">
                <p className="eyebrow">{kindLabel(b.kind)}</p>
                <span className={`status ${b.status}`}>{b.status}</span>
                <h2>{b.activity.title}</h2>
                <p>{b.activity.location}</p>
                <hr />
                <p>
                  {b.day} · {b.start_time}–{b.end_time} IST
                </p>
                <p>
                  {b.people} guests · {money(b.total)} total
                </p>
                <div className="trip-actions">
                  <button
                    className="text-button"
                    onClick={() => navigate(activityPath(b.activity))}
                  >
                    View {kindLabel(b.kind).toLowerCase()}
                  </button>
                  {b.status === "confirmed" &&
                    `${b.day} ${b.start_time}` > now && (
                      <button
                        className="text-button"
                        onClick={() => setCancel(b)}
                      >
                        Cancel reservation
                      </button>
                    )}
                </div>
                <small>Confirmation #ACT{b.id}</small>
              </div>
            </article>
          ))}
        </div>
      )}
      {cancel && (
        <Modal
          title="Cancel this reservation?"
          onClose={() => {
            if (!busy) setCancel(null);
          }}
        >
          <p>
            {cancel.activity.title} · {cancel.day} {cancel.start_time} IST
          </p>
          <p>You’ll receive a full mock refund of {money(cancel.total)}.</p>
          <button
            className="primary-button"
            disabled={busy}
            onClick={() => void remove()}
          >
            {busy ? "Cancelling…" : "Confirm cancellation"}
          </button>
        </Modal>
      )}
    </section>
  );
}
