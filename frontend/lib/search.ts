export const defaultFilters = {
  min: 0,
  max: 1000000,
  type: "",
  amenities: [] as string[],
  bedrooms: 0,
  beds: 0,
  bathrooms: 0,
  min_rating: 0,
  max_rating: 5,
  superhost: false,
};
export type Filters = typeof defaultFilters;
export type SearchState = {
  q: string;
  start: string;
  end: string;
  guests: number;
};
export const searchStorageKey = "airbnb-search-v1";
export const emptySearch: SearchState = {
  q: "",
  start: "",
  end: "",
  guests: 1,
};
export function validDate(value: unknown): value is string {
  return (
    typeof value === "string" &&
    /^\d{4}-\d{2}-\d{2}$/.test(value) &&
    !Number.isNaN(Date.parse(value))
  );
}
export function compactDateSummary(start: string, end: string): string {
  if (!start) return "Any week";
  const startDate = new Date(`${start}T12:00:00`);
  if (Number.isNaN(startDate.getTime())) return "Any week";
  const day = new Intl.DateTimeFormat("en", {
    day: "numeric",
    timeZone: "UTC",
  });
  const month = new Intl.DateTimeFormat("en", {
    month: "short",
    timeZone: "UTC",
  });
  const startDay = day.format(startDate);
  const startMonth = month.format(startDate);
  if (!end) return `${startDay} ${startMonth}`;
  const endDate = new Date(`${end}T12:00:00`);
  if (Number.isNaN(endDate.getTime())) return `${startDay} ${startMonth}`;
  const endDay = day.format(endDate);
  const endMonth = month.format(endDate);
  return startDate.getUTCMonth() === endDate.getUTCMonth() &&
    startDate.getUTCFullYear() === endDate.getUTCFullYear()
    ? `${startDay}–${endDay} ${startMonth}`
    : `${startDay} ${startMonth} – ${endDay} ${endMonth}`;
}
export function compactActivityDate(value: string): string {
  if (!value) return "Any week";
  const date = new Date(`${value}T12:00:00`);
  if (Number.isNaN(date.getTime())) return "Any week";
  const day = new Intl.DateTimeFormat("en", {
    day: "numeric",
    timeZone: "UTC",
  }).format(date);
  const month = new Intl.DateTimeFormat("en", {
    month: "short",
    timeZone: "UTC",
  }).format(date);
  return `${day} ${month}`;
}
