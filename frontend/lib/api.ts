export type User = {
  id: number;
  name: string;
  role: "guest" | "host";
  avatar: string;
  joined_year: number;
};
export type Review = {
  id: number;
  name: string;
  avatar: string;
  rating: number;
  comment: string;
  created_at: string;
};
export type Listing = {
  id: number;
  host_id: number;
  title: string;
  description: string;
  location: string;
  country: string;
  latitude: number;
  longitude: number;
  category: string;
  property_type: string;
  price: number;
  cleaning_fee: number;
  max_guests: number;
  bedrooms: number;
  beds: number;
  bathrooms: number;
  superhost: number;
  photos: string[];
  amenities: string[];
  host: User;
  rating: number | null;
  review_count: number;
  reviews?: Review[];
  unavailable?: { check_in: string; check_out: string }[];
};
export type Booking = {
  id: number;
  listing: Listing;
  check_in: string;
  check_out: string;
  guests: number;
  nightly_price: number;
  cleaning_fee: number;
  service_fee: number;
  total: number;
  status: string;
  guest_name: string;
  reviewed: boolean;
};
export type Quote = {
  nights: number;
  nightly_price: number;
  subtotal: number;
  cleaning_fee: number;
  service_fee: number;
  total: number;
};
export const money = (n: number) => "₹" + n.toLocaleString("en-IN");
export const dateKey = (d: Date) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
// The demo uses India calendar days consistently with the API and SQLite.
export const today = () => new Date(Date.now() + 330 * 60 * 1000).toISOString().slice(0, 10);
export const prettyDate = (s: string) =>
  s
    ? new Date(s + "T12:00:00").toLocaleDateString("en-GB", {
        day: "numeric",
        month: "short",
      })
    : "Add dates";
export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message);
    this.name = "ApiError";
  }
}
export type ApiOptions = {
  headers?: Record<string, string>;
  signal?: AbortSignal;
};
export async function api<T>(
  path: string,
  user: number,
  method = "GET",
  body?: unknown,
  options: ApiOptions = {},
): Promise<T> {
  const base =
    process.env.NEXT_PUBLIC_API_URL ||
    (typeof window !== "undefined" &&
    ["localhost", "127.0.0.1"].includes(window.location.hostname) &&
    window.location.port === "3001"
      ? "http://127.0.0.1:8001"
      : "");
  let response: Response;
  try {
    response = await fetch(base + "/api" + path, {
      method,
      headers: {
        "Content-Type": "application/json",
        "X-Demo-User": String(user),
        ...options.headers,
      },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: options.signal,
      cache: "no-store",
    });
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") throw error;
    throw new Error(
      "We couldn’t connect. Please check your connection and try again.",
    );
  }
  let data;
  try {
    data = await response.json();
  } catch {
    throw new ApiError("The server returned an unexpected response. Please try again.", response.status);
  }
  if (!response.ok)
    throw new ApiError(
      typeof data?.detail === "string"
        ? data.detail
        : Array.isArray(data?.detail)
          ? data.detail.map((e: { msg: string }) => e.msg).join(". ")
          : "Something went wrong. Please try again.",
      response.status,
    );
  return data;
}
export const amenityNames = [
  "Wifi",
  "Kitchen",
  "Free parking",
  "Air conditioning",
  "Pool",
  "Mountain view",
  "Beach access",
  "Washer",
  "Workspace",
  "Garden",
  "Lake view",
  "Hot tub",
];
export const categories = [
  "Amazing views",
  "Beachfront",
  "Cabins",
  "Countryside",
  "Amazing pools",
  "Design",
  "Lakefront",
  "Tiny homes",
  "Tropical",
];
