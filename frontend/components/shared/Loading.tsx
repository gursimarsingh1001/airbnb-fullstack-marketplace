"use client";

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
