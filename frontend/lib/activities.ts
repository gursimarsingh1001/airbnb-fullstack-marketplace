import type { User, Review } from "./api";
export type ActivityKind = "experiences" | "services";
export type ActivitySlot = {
  id: number;
  day: string;
  start_time: string;
  capacity: number;
  remaining: number;
};
export type Activity = {
  id: number;
  kind: ActivityKind;
  host_id: number;
  title: string;
  description: string;
  location: string;
  country: string;
  category: string;
  price: number;
  price_type: "person" | "group";
  duration_minutes: number;
  capacity: number;
  language: string;
  setting: string;
  service_location: string;
  itinerary: string;
  included: string;
  requirements: string;
  photos: string[];
  host: User;
  rating: number | null;
  review_count: number;
  reviews?: Review[];
  slots?: ActivitySlot[];
  deleted?: number;
};
export type ActivityQuote = {
  unit_price: number;
  price_type: "person" | "group";
  people: number;
  subtotal: number;
  service_fee: number;
  total: number;
  day: string;
  start_time: string;
  end_time: string;
};
export type ActivityBooking = ActivityQuote & {
  id: number;
  activity: Activity;
  kind: ActivityKind;
  status: string;
  guest_name: string;
  slot_id: number;
};
export type ActivitySearch = {
  q: string;
  day: string;
  people: number;
  category?: string;
};
export const activityCategories: Record<ActivityKind, string[]> = {
  experiences: [
    "Food & drink",
    "Culture & history",
    "Nature & outdoors",
    "Art & creativity",
    "Sports",
    "Wellness",
    "Nightlife",
    "Hidden gems",
  ],
  services: [
    "Private chefs",
    "Photography",
    "Massage",
    "Personal training",
    "Beauty",
    "Hair styling",
    "Spa & wellness",
    "Catering",
    "Private guides",
  ],
};
export const kindLabel = (kind: ActivityKind) =>
  kind === "experiences" ? "Experience" : "Service";
export const activityPath = (a: Activity) => `${a.kind}/${a.id}`;
