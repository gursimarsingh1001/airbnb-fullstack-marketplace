"use client";
import { useState } from "react";
import { Heart, Star, ChevronRight } from "lucide-react";
import { Listing, money } from "@/lib/api";
import { SafeImage } from "../shared/SafeImage";

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
        {l.photos.length > 1 && (
          <button
            className="photo-next"
            aria-label="Next photo"
            onClick={() => setPhoto((photo + 1) % l.photos.length)}
          >
            <ChevronRight size={17} />
          </button>
        )}
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
