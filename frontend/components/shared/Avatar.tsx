"use client";
import { useState } from "react";

export function Avatar({
  initials,
  name,
  large = false,
}: {
  initials: string;
  name: string;
  large?: boolean;
}) {
  const [failed, setFailed] = useState(false);
  const portraits: Record<string, string> = {
    AM: "photo-1472099645785-5658abf4ff4e",
    AS: "photo-1580489944761-15a19d654956",
    MR: "photo-1500648767791-00dcc994a43e",
    MP: "photo-1506794778202-cad84cf45f1d",
    SC: "photo-1494790108377-be9c29b29330",
    RK: "photo-1517841905240-472988babdf9",
  };
  const directPortrait = /^https:\/\//.test(initials) ? initials : null;
  const portrait =
    directPortrait ||
    (portraits[initials]
      ? `https://images.unsplash.com/${portraits[initials]}?auto=format&fit=crop&w=120&h=120&q=80`
      : null);
  const fallbackInitials = directPortrait
    ? name
        .split(/\s+/)
        .map((part) => part[0])
        .slice(0, 2)
        .join("")
        .toUpperCase()
    : initials;
  return (
    <span className={`avatar photo-avatar${large ? " large" : ""}`}>
      {!failed && portrait ? (
        <img
          src={portrait}
          alt={`${name} — illustrative demo portrait`}
          onError={() => setFailed(true)}
        />
      ) : (
        fallbackInitials
      )}
    </span>
  );
}
