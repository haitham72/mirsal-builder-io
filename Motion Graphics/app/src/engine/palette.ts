import { hexToLinear } from './util';

// The Mirsal palette (README §4.1): a night-navy stage, paper white, and one signal colour,
// Mirsal blue. AI cyan is the hot core of the orb; gold is the one rare accent.
export const HEX = {
  ink: '#070B16', // stage: deep night navy
  ink2: '#111A2E', // raised navy: cards, panels, the window frame
  graphite: '#475569', // dim lines, secondary text (Slate 600)
  ash: '#94A3B8', // mid grey, unsaid karaoke outlines (Slate 400)
  bone: '#F7F8FA', // paper white: primary text, light plates (the app's background)
  signal: '#3B82F6', // Mirsal blue: the said word, the pen, the one button
  ember: '#22D3EE', // AI cyan: the orb's core, the rolling highlight
  blood: '#2563EB', // Primary Dark: the shadow side of signal
  acid: '#F59E0B', // gold, at most once per plate: the falcon's beak, the price, the heart
} as const;

export type PaletteKey = keyof typeof HEX;

/** Linear RGB triplets for GL uniforms. */
export const LIN: Record<PaletteKey, [number, number, number]> = Object.fromEntries(
  Object.entries(HEX).map(([k, v]) => [k, hexToLinear(v)]),
) as Record<PaletteKey, [number, number, number]>;

/** CSS rgba() for Canvas2D. */
export function rgba(key: PaletteKey | string, a = 1): string {
  const hex = (HEX as Record<string, string>)[key] ?? key;
  const n = parseInt(hex.replace('#', ''), 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
}
