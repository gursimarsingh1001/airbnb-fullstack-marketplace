"use client";
import { useEffect, useState } from "react";
import { api, money, User } from "@/lib/api";
import {
  Activity,
  ActivityBooking,
  ActivityKind,
  activityPath,
} from "@/lib/activities";
import { Empty, Loading, Modal, SafeImage } from "../UI";
import ActivityEditor from "./ActivityEditor";
export default function ActivityHost({
  kind,
  user,
  navigate,
  notify,
}: {
  kind: ActivityKind;
  user: User;
  navigate: (p: string) => void;
  notify: (s: string) => void;
}) {
  const [data, setData] = useState<{
      items: Activity[];
      bookings: ActivityBooking[];
    } | null>(null),
    [error, setError] = useState(""),
    [refresh, setRefresh] = useState(0),
    [tab, setTab] = useState("listings");
  const [editor, setEditor] = useState<Activity | null | false>(false),
    [removing, setRemoving] = useState<Activity | null>(null),
    [busy, setBusy] = useState(false);
  useEffect(() => {
    const c = new AbortController();
    setError("");
    api<{ items: Activity[]; bookings: ActivityBooking[] }>(
      "/activities/host/dashboard",
      user.id,
      "GET",
      undefined,
      { signal: c.signal },
    )
      .then(setData)
      .catch((e) => {
        if (!c.signal.aborted) setError(e.message);
      });
    return () => c.abort();
  }, [user.id, refresh]);
  async function edit(a: Activity) {
    setBusy(true);
    try {
      setEditor(await api<Activity>(`/activities/${a.id}`, user.id));
    } catch (e) {
      notify((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function remove() {
    if (!removing || busy) return;
    setBusy(true);
    try {
      await api(`/activities/host/${removing.id}`, user.id, "DELETE");
      setRemoving(null);
      setRefresh((n) => n + 1);
      notify("Offering deleted.");
    } catch (e) {
      notify((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const items = data?.items.filter((a) => a.kind === kind) || [],
    bookings = data?.bookings.filter((b) => b.kind === kind) || [];
  return (
    <main id="main-content" className="workspace-shell">
      <div className="page-title-row">
        <div>
          <p className="eyebrow">YOUR HOSTING SPACE</p>
          <h1>Your {kind}</h1>
          <p>Create something memorable for your guests.</p>
        </div>
        <button className="dark-button" onClick={() => setEditor(null)}>
          Create {kind === "experiences" ? "experience" : "service"}
        </button>
      </div>
      <div className="activity-tabs">
        <button
          aria-pressed={tab === "listings"}
          onClick={() => setTab("listings")}
        >
          Listings ({items.length})
        </button>
        <button
          aria-pressed={tab === "reservations"}
          onClick={() => setTab("reservations")}
        >
          Reservations ({bookings.length})
        </button>
      </div>
      {error ? (
        <Empty
          title="Dashboard couldn’t load"
          text={error}
          action={
            <button onClick={() => setRefresh((n) => n + 1)}>Retry</button>
          }
        />
      ) : !data ? (
        <Loading />
      ) : tab === "listings" ? (
        <div className="activity-grid">
          {items.map((a) => (
            <article className="activity-provider-card" key={a.id}>
              <button onClick={() => navigate(activityPath(a))}>
                <SafeImage src={a.photos[0]} alt={a.title} />
              </button>
              <h3>{a.title}</h3>
              <p>
                {a.location} · {money(a.price)} / {a.price_type}
              </p>
              <div className="activity-actions">
                <button
                  className="text-button"
                  disabled={busy}
                  onClick={() => void edit(a)}
                >
                  Edit {a.title}
                </button>
                <button className="text-button" onClick={() => setRemoving(a)}>
                  Delete {a.title}
                </button>
              </div>
            </article>
          ))}
          {!items.length && <p>You haven’t published any {kind} yet.</p>}
        </div>
      ) : (
        <div className="trips-grid">
          {bookings.map((b) => (
            <article className="activity-provider-reservation" key={b.id}>
              <span className={`status ${b.status}`}>{b.status}</span>
              <h3>{b.activity.title}</h3>
              <p>
                {b.guest_name} · {b.people} guests
              </p>
              <p>
                {b.day} · {b.start_time}–{b.end_time} IST
              </p>
              <strong>{money(b.total)} total</strong>
              <p>Confirmation #ACT{b.id}</p>
            </article>
          ))}
          {!bookings.length && (
            <p>Reservations will appear here when guests book.</p>
          )}
        </div>
      )}
      {editor !== false && (
        <ActivityEditor
          kind={kind}
          item={editor}
          user={user.id}
          onClose={() => setEditor(false)}
          onSaved={() => {
            setEditor(false);
            setRefresh((n) => n + 1);
            notify(
              editor
                ? "Offering updated."
                : `${kind === "experiences" ? "Experience" : "Service"} published.`,
            );
          }}
        />
      )}
      {removing && (
        <Modal
          title="Remove this offering?"
          onClose={() => {
            if (!busy) setRemoving(null);
          }}
        >
          <p>
            {removing.title} will no longer appear in search. Reservation
            history is preserved. Upcoming confirmed reservations must finish or
            be cancelled first.
          </p>
          <button
            className="primary-button"
            disabled={busy}
            onClick={() => void remove()}
          >
            {busy ? "Removing…" : "Confirm removal"}
          </button>
        </Modal>
      )}
    </main>
  );
}
