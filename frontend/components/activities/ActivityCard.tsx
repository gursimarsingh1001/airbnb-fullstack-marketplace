"use client";
import { Heart, Star } from "lucide-react";
import { SafeImage } from "../UI";
import { money } from "@/lib/api";
import { Activity, activityPath } from "@/lib/activities";
export default function ActivityCard({
  item,
  saved,
  onSave,
  navigate,
}: {
  item: Activity;
  saved: boolean;
  onSave: (a: Activity) => void;
  navigate: (path: string) => void;
}) {
  return (
    <article className="activity-card">
      <div className="activity-card-image">
        <button
          onClick={() => navigate(activityPath(item))}
          aria-label={`View ${item.title}`}
        >
          <SafeImage src={item.photos[0]} alt={item.title} loading="lazy" />
        </button>
        <button
          className="activity-heart"
          aria-label={`${saved ? "Remove from" : "Save to"} wishlist: ${item.title}`}
          aria-pressed={saved}
          onClick={() => onSave(item)}
        >
          <Heart size={23} fill={saved ? "#ff385c" : "#0005"} />
        </button>
        {item.rating !== null && item.rating >= 4.9 && (
          <span className="activity-badge">Guest favourite</span>
        )}
      </div>
      <button
        className="activity-card-copy"
        onClick={() => navigate(activityPath(item))}
      >
        <span className="activity-location">
          {item.location}, {item.country}
        </span>
        <h3>{item.title}</h3>
        <span>
          {item.duration_minutes} min · {item.category}
        </span>
        <span>
          <Star size={13} fill="currentColor" />{" "}
          {item.rating?.toFixed(2) || "New"} · {item.review_count} reviews
        </span>
        <span>
          <strong>From {money(item.price)}</strong> /{" "}
          {item.price_type === "person" ? "guest" : "group"}
        </span>
      </button>
    </article>
  );
}
