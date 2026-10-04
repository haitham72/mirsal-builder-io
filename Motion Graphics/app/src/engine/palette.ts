import { hexToLinear } from './util';

// The Mirsal palette (README §4.1), the app's own iOS look: a light stage, slate text, one signal
// colour (Mirsal blue). AI cyan only marks the AI at work; gold is the one rare accent.
export const HEX = {
  ink: '#1E293B', // text on the light stage (Slate 800)
  ink2: '#FFFFFF', // surface: cards, sheets, the window
  graphite: '#64748B', // secondary text (Slate 500)
  ash: '#CBD5E1', // hairlines, separators, unsaid words (Slate 300)
  bone: '#F7F8FA', // the stage: the app's background
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
