import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {
  title: "Airbnb — Find your kind of getaway",
  description:
    "Discover beautiful homes, unique stays, and your next favourite place. An independent full-stack assignment demo.",
};
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
