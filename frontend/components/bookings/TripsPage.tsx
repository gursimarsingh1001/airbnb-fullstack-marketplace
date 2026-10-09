"use client";
import { Dispatch, SetStateAction } from "react";
import { CalendarDays, UserRound, ArrowUpRight } from "lucide-react";
import { Booking, User, money, prettyDate, today } from "@/lib/api";
import { Empty } from "../shared/Empty";
import { Loading } from "../shared/Loading";
import { SafeImage } from "../shared/SafeImage";
import ActivityTrips, { TripTab } from "../activities/ActivityTrips";
type Props = {
  user: User;
  trips: Booking[];
  tripsLoading: boolean;
  tripsError: string;
  tripTab: TripTab;
  setTripTab: (tab: TripTab) => void;
  setRefresh: Dispatch<SetStateAction<number>>;
  navigate: (route: string) => void;
  notify: (message: string) => void;
  setCancel: (booking: Booking) => void;
  setReviewing: (booking: Booking) => void;
  setReviewRating: (rating: number) => void;
  setReviewComment: (comment: string) => void;
};
export default function TripsPage({
  user,
  trips,
  tripsLoading,
  tripsError,
  tripTab,
  setTripTab,
  setRefresh,
  navigate,
  notify,
  setCancel,
  setReviewing,
  setReviewRating,
  setReviewComment,
}: Props) {
  return (
    <main id="main-content" tabIndex={-1} className="workspace-shell">
      <p className="eyebrow">SOMETHING TO LOOK FORWARD TO</p>
      <h1>Your trips</h1>
      <p className="muted page-subtitle">
        New places. New memories. All in one place.
      </p>
      <div className="activity-tabs">
        {(["Upcoming", "Past", "Cancelled"] as TripTab[]).map((t) => (
          <button
            key={t}
            aria-pressed={tripTab === t}
            onClick={() => setTripTab(t)}
          >
            {t}
          </button>
        ))}
      </div>
      <h2>Homes</h2>
      {tripsLoading ? (
        <Loading />
      ) : tripsError ? (
        <Empty
          title="Your trips couldn’t load"
          text={tripsError}
          action={
            <button
              className="dark-button"
              onClick={() => setRefresh((n) => n + 1)}
            >
              Try again
            </button>
          }
        />
      ) : trips.length ? (
        <div className="trips-grid">
          {trips
            .filter((b) =>
              tripTab === "Cancelled"
                ? b.status === "cancelled"
                : b.status === "confirmed" &&
                  (tripTab === "Past"
                    ? b.check_out <= today()
                    : b.check_out > today()),
            )
            .map((b) => (
              <article className="trip-card" key={b.id}>
                <button onClick={() => navigate("listing/" + b.listing.id)}>
                  <SafeImage src={b.listing.photos[0]} alt={b.listing.title} />
                </button>
                <div className="trip-copy">
                  <span className={`status ${b.status}`}>{b.status}</span>
                  <h2>{b.listing.location.split(",")[0]}</h2>
                  <p>{b.listing.title}</p>
                  <hr />
                  <div className="trip-details">
                    <CalendarDays size={18} />
                    <span>
                      {prettyDate(b.check_in)} – {prettyDate(b.check_out)},{" "}
                      {b.check_in.slice(0, 4)}
                    </span>
                  </div>
                  <div className="trip-details">
                    <UserRound size={18} />
                    <span>
                      {b.guests} guests · {money(b.total)} total
                    </span>
                  </div>
                  <div className="trip-actions">
                    <button
                      className="text-button"
                      onClick={() => navigate("listing/" + b.listing.id)}
                    >
                      View home <ArrowUpRight size={16} />
                    </button>
                    {b.status === "confirmed" && b.check_in >= today() && (
                      <button
                        className="text-button muted"
                        onClick={() => setCancel(b)}
                      >
                        Cancel trip
                      </button>
                    )}
                    {b.status === "confirmed" &&
                      b.check_out <= today() &&
                      (b.reviewed ? (
                        <span className="review-submitted" role="status">
                          Review shared
                        </span>
                      ) : (
                        <button
                          className="text-button"
                          onClick={() => {
                            setReviewing(b);
                            setReviewRating(5);
                            setReviewComment("");
                          }}
                        >
                          Leave a review
                        </button>
                      ))}
                  </div>
                  <small className="muted">
                    Confirmation #AB{String(b.id).padStart(6, "0")}
                  </small>
                </div>
              </article>
            ))}
        </div>
      ) : (
        <Empty
          title="Time to dust off your bags"
          text="Your next adventure is waiting. Find a home you’ll love."
          action={
            <button
              className="primary-button"
              onClick={() => navigate("explore")}
            >
              Start searching
            </button>
          }
        />
      )}
      <ActivityTrips
        key={user.id}
        user={user.id}
        tab={tripTab}
        navigate={navigate}
        notify={notify}
      />
    </main>
  );
}
