export const HOVE = {
  name: "Hove",
  lat: 50.8279,
  lon: -0.1688,
};

const PHRASES = [
  "Checking the clouds…",
  "Looking for a dark patch…",
  "Seeing what's up tonight…",
];

export function loadingPhrase(tick: number): string {
  return PHRASES[tick % PHRASES.length];
}

export function formatClock(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString("en-GB", { hour: "numeric", minute: "2-digit" }).toLowerCase();
}

export function formatWindowSpan(start: string, end: string): string {
  return `${formatClock(start)}–${formatClock(end)}`;
}
