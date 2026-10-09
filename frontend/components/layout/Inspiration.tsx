"use client";
import { useState } from "react";

const destinations: Record<string, [string, string][]> = {
  "Popular": [["Goa", "Beachside stays"], ["Manali", "Mountain cabins"], ["Jaipur", "City escapes"], ["Kerala", "Slow, green getaways"], ["Bali", "Tropical villas"], ["Udaipur", "Lakeside living"], ["Coorg", "Coffee country"], ["Rishikesh", "Riverside retreats"], ["Ooty", "Hillside hideaways"], ["Lonavala", "Weekend getaways"], ["Darjeeling", "Tea garden mornings"], ["Pondicherry", "Coastal cottages"]],
  "Mountains & nature": [["Leh", "High-altitude escapes"], ["Manali", "Cabins in the hills"], ["Jibhi", "Forest hideaways"], ["Shimla", "Pine-scented mornings"], ["Darjeeling", "Tea country"], ["Gangtok", "Himalayan views"], ["Shillong", "Green hills"], ["Tawang", "Mountain retreats"], ["Wayanad", "Forest cottages"], ["Coorg", "Coffee estates"], ["Kodaikanal", "Misty mornings"], ["Munnar", "Tea garden stays"]],
  "Coast & islands": [["Goa", "Villas by the sea"], ["Gokarna", "Quiet beach breaks"], ["Varkala", "Clifftop escapes"], ["Kochi", "Coastal city stays"], ["Pondicherry", "Seaside weekends"], ["Port Blair", "Island adventures"], ["Puri", "Bay of Bengal stays"], ["Visakhapatnam", "Coast & city"], ["Bali", "Tropical hideaways"], ["Phuket", "Island villas"], ["Galle", "Southern coast stays"], ["Santorini", "Aegean views"]],
  "Cities & culture": [["Delhi", "Capital city stays"], ["Mumbai", "City by the sea"], ["Bengaluru", "Garden city escapes"], ["Hyderabad", "Heritage & modern living"], ["Chennai", "Coastal city breaks"], ["Kolkata", "Art & neighbourhoods"], ["Ahmedabad", "Heritage weekends"], ["Varanasi", "Riverside mornings"], ["Amritsar", "Culture & food"], ["Lucknow", "Old-city charm"], ["Bhopal", "Lakes & culture"], ["Jaipur", "Pink city getaways"]],
  "Beyond India": [["Bali", "Indonesia · Tropical villas"], ["Florence", "Italy · Tuscan escapes"], ["Santorini", "Greece · Island homes"], ["Kathmandu", "Nepal · Cultural stays"], ["Pokhara", "Nepal · Lakeside retreats"], ["Galle", "Sri Lanka · Coastal stays"], ["Ella", "Sri Lanka · Hill country"], ["Phuket", "Thailand · Island villas"], ["Chiang Mai", "Thailand · Garden stays"], ["Bangkok", "Thailand · City breaks"], ["Colombo", "Sri Lanka · Oceanfront city"]],
};

export default function Inspiration({ onChoose }: { onChoose: (destination: string) => void }) {
  const [active, setActive] = useState("Popular");
  return <section className="inspiration" aria-labelledby="inspiration-title">
    <h3 id="inspiration-title">Inspiration for your next escape</h3>
    <p>A weekend nearby or a little further afield. Find a place that feels like you.</p>
    <div className="inspiration-tabs" aria-label="Destination themes">
      {Object.keys(destinations).map((name) => <button key={name} aria-pressed={name === active} onClick={() => setActive(name)}>{name}</button>)}
    </div>
    <div className="footer-destinations">
      {destinations[active].map(([name, description]) => <button key={name} onClick={() => onChoose(name)}><strong>{name}</strong><span>{description}</span></button>)}
    </div>
    <p className="inspiration-note">Explore fictional demo stays with illustrative photography.</p>
  </section>;
}
