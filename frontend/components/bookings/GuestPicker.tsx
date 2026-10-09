"use client";

export function GuestPicker({
  value,
  onChange,
  max = 16,
}: {
  value: number;
  onChange: (n: number) => void;
  max?: number;
}) {
  return (
    <div className="guest-picker">
      <div>
        <strong>Guests</strong>
        <p>Ages 2 and above</p>
      </div>
      <div className="stepper">
        <button
          className="circle-button"
          aria-label="Remove guest"
          disabled={value <= 1}
          onClick={() => onChange(value - 1)}
        >
          −
        </button>
        <span>{value}</span>
        <button
          className="circle-button"
          aria-label="Add guest"
          disabled={value >= max}
          onClick={() => onChange(value + 1)}
        >
          +
        </button>
      </div>
    </div>
  );
}
