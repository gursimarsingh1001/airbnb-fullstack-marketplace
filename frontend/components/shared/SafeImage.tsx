"use client";
import { useState } from "react";

export function SafeImage({
  src,
  alt,
  ...props
}: React.ImgHTMLAttributes<HTMLImageElement>) {
  const [failed, setFailed] = useState<string | null>(null);
  const fallback = !src || failed === src;
  return (
    <img
      {...props}
      src={fallback ? "/image-placeholder.svg" : src}
      alt={fallback ? `${alt || "Listing photo"} — photo unavailable` : alt}
      onError={() => {
        if (!fallback && typeof src === "string") setFailed(src);
      }}
    />
  );
}
