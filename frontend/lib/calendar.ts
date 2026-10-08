export type UnavailableRange = { check_in: string; check_out: string };

/** Stay dates are ISO date-only values; checkout never occupies that night. */
export function canChooseDate(key: string, start: string, end: string, unavailable: UnavailableRange[], minimum: string) {
  const max = new Date(`${minimum}T00:00:00Z`);
  max.setUTCDate(max.getUTCDate() + 730);
  if (key < minimum || key > max.toISOString().slice(0, 10)) return false;
  const choosingCheckout = !!start && !end && key > start;
  if (choosingCheckout) {
    const nights = (Date.parse(key) - Date.parse(start)) / 86400000;
    return nights <= 90 && !unavailable.some((r) => start < r.check_out && key > r.check_in);
  }
  return !unavailable.some((r) => key >= r.check_in && key < r.check_out);
}
