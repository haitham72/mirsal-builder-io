// The edit: which plate plays when. A voiceover has no beat grid, so every cut sits in the pause
// before a line: just before its first word (never after it), anchored to the aligned script
// (data/lyrics.json).
import type { TimelineEntry } from './engine/engine';
import type { SceneClass } from './engine/scene';
import type { Lyrics } from './engine/lyrics';
import type { AudioData } from './engine/audio';

// Scene modules are discovered lazily so a missing/broken scene never breaks the build.
const modules = import.meta.glob<{ default: SceneClass }>('./scenes/*.ts');
const scene = (name: string) => () => {
  const m = modules[`./scenes/${name}.ts`];
  return m ? m() : Promise.reject(new Error(`scene module not found: scenes/${name}.ts`));
};

export function makeTimeline(ly: Lyrics, au: AudioData): TimelineEntry[] {
  /** Cut in the pause before the line containing q: 0.18 s before its first word (less if the pause is short). */
  const cut = (q: string, nth = 0) => {
    const l = ly.get(q, nth);
    const prev = ly.lines[l.i - 1];
    const gap = prev ? l.start - prev.end : 1;
    return l.start - Math.min(0.18, Math.max(0.04, gap * 0.45));
  };
  const b = {
    creator: cut('Meet the Mirsal Creator'),
    persona: cut('And it gets to know you'),
    batch: cut('Need more than one'),
    override: cut('a rejection is never'),
    users: cut('made for the whole team'),
    app: cut('Mirsal has been waiting'),
    outro: cut('Your words'),
    end: au.duration,
  };
  const E = (id: string, file: string, start: number, end: number, extra: Partial<TimelineEntry> = {}): TimelineEntry =>
    ({ id, load: scene(file), start, end, ...extra });
  // A plate without its own scene yet is the rough-cut card (scenes/card.ts) over its own lines. When a
  // plate's scene is written, point its entry at that file (README §5).
  const card = (id: string, fig: string, start: number, end: number, lines: string[]) =>
    E(id, 'card', start, end, { params: { fig, lines } });
  return [
    card('hook', 'Hook', 0, b.creator, ['What if one sentence', 'No designer']),
    card('creator', 'One click', b.creator, b.persona, ['Meet the Mirsal Creator', 'press one button', 'that one click runs']),
    card('persona', 'It learns you', b.persona, b.batch, ['And it gets to know you', 'Tell it your name', 'Ask for cartoonish']),
    card('batch', 'Batching', b.batch, b.override, ['Need more than one', 'It picks the subjects', 'Nine stickers a sheet']),
    card('override', 'No dead ends', b.override, b.users, ['a rejection is never', 'Every blocked sticker']),
    card('users', 'The whole team', b.users, b.app, ['made for the whole team', 'Everyone signs in', 'The best packs']),
    card('app', 'Inside Mirsal', b.app, b.outro, ['Mirsal has been waiting', 'The Creator is an engine']),
    card('outro', 'Mirsal Creator', b.outro, b.end, ['Your words', 'Mirsal Creator —']),
  ];
}
