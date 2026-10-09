import type { NextConfig } from "next";
import { PHASE_DEVELOPMENT_SERVER } from "next/constants";
export default function config(phase: string): NextConfig {
  return {
    ...(phase === PHASE_DEVELOPMENT_SERVER
      ? {
          async rewrites() {
            return [
              { source: "/experiences/:id", destination: "/experiences" },
              { source: "/services/:id", destination: "/services" },
            ];
          },
        }
      : { output: "export" }),
    images: { unoptimized: true },
    trailingSlash: true,
  };
}
