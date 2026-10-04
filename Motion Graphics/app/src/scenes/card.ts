// CARD: the rough-cut plate, in the Mirsal app's clean iOS look. Until a plate has its own scene, the
// timeline points at this one: the plate's lines in Inter on the light stage, each word appearing as it is
// said (Mirsal blue, settling to slate), the Mirsal orb gliding under the word being said, the camera
// holding on a line and easing to the next, and the plate's name in a pill. It reads its lines from
// ctx.params.lines (queries, as lineOf takes them), so it re-times itself to any read.
import type * as THREE from 'three';
import { Scene, type Frame, type PostOverrides } from '../engine/scene';
import { Layer2D, clearRT } from '../engine/gl';
import { LIN, rgba } from '../engine/palette';
import { F, font, measure } from '../engine/type';
import { Lyrics, type Line } from '../engine/lyrics';
import { clamp, ease, prog, TAU } from '../engine/util';
import { Cam2D, drawKaraoke, placeRow, rowWidth, w2s, lineOf, type KWord } from './_vo';

const SIZE = 76, MAXW = 1480, LEAD = 1.28;

/** The Mirsal orb (the logo): a blue sphere with a lighter inner sphere, a small highlight, a soft shadow. */
export function drawOrb(c: CanvasRenderingContext2D, x: number, y: number, r: number, alpha = 1) {
  if (alpha <= 0.003 || r <= 0.5) return;
  c.save();
  c.globalAlpha = alpha;
  c.shadowColor = 'rgba(37,99,235,0.35)';
  c.shadowBlur = r * 1.6;
  c.shadowOffsetY = r * 0.35;
  const g = c.createRadialGradient(x - r * 0.25, y - r * 0.3, r * 0.1, x, y, r);
  g.addColorStop(0, '#60A5FA');
  g.addColorStop(0.7, '#3B82F6');
  g.addColorStop(1, '#2563EB');
  c.fillStyle = g;
  c.beginPath(); c.arc(x, y, r, 0, TAU); c.fill();
  c.shadowColor = 'transparent';
  const g2 = c.createRadialGradient(x + r * 0.05, y - r * 0.1, r * 0.05, x + r * 0.12, y - r * 0.05, r * 0.62);
  g2.addColorStop(0, 'rgba(219,234,254,0.95)');
  g2.addColorStop(1, 'rgba(147,197,253,0.55)');
  c.fillStyle = g2;
  c.beginPath(); c.arc(x + r * 0.12, y - r * 0.08, r * 0.6, 0, TAU); c.fill();
  c.fillStyle = 'rgba(255,255,255,0.9)';
  c.beginPath(); c.arc(x - r * 0.55, y + r * 0.45, r * 0.09, 0, TAU); c.fill();
  c.restore();
}

/** An iOS pill label (the plate's name), screen space. */
function pill(c: CanvasRenderingContext2D, text: string, x: number, y: number) {
  const fam = F.inter(600), size = 15;
  const w = measure(text, fam, size) + 32, h = 34;
  c.save();
  c.shadowColor = 'rgba(15,23,42,0.08)'; c.shadowBlur = 16; c.shadowOffsetY = 4;
  c.fillStyle = rgba('ink2', 1);
  c.beginPath(); c.roundRect(x, y, w, h, h / 2); c.fill();
  c.restore();
  c.font = font(fam, size);
  c.fillStyle = rgba('graphite', 1);
  c.textBaseline = 'middle';
  c.fillText(text, x + 16, y + h / 2 + 1);
  c.textBaseline = 'alphabetic';
}

export default class Card extends Scene {
  cam = new Cam2D();
  ui = new Layer2D();
  kw: KWord[] = [];
  lines: Line[] = [];

  override init() {
    const ly = this.ctx.lyrics;
    const fam = F.inter(700);
    this.lines = (this.ctx.params.lines as string[]).map((q) => lineOf(ly, q));
    let y = 0;
    const lineY: number[] = [];
    for (const L of this.lines) {
      const rows: typeof L.words[] = [[]];
      for (const w of L.words) {
        const row = rows[rows.length - 1]!;
        if (row.length && rowWidth([...row, w].map((x) => x.w), SIZE, fam, -0.02) > MAXW) rows.push([w]);
        else row.push(w);
      }
      lineY.push(y);
      for (const r of rows) {
        this.kw.push(...placeRow(r, -MAXW / 2, y, SIZE, fam, `l${L.i}`, { ant: 0.08, tracking: -0.02 }).words);
        y += SIZE * LEAD;
      }
      y += SIZE * 0.55;
    }
    // hold on a line while it is said, then ease to the next (a key is where the camera ARRIVES)
    const K = this.cam;
    let prev = 0;
    this.lines.forEach((L, i) => {
      const rowsEnd = i + 1 < lineY.length ? lineY[i + 1]! - SIZE * 0.55 : y - SIZE * 0.55;
      const cy = lineY[i]! + (rowsEnd - lineY[i]!) / 2 - SIZE * 0.45;
      if (i === 0) K.key(this.ctx.start, 0, cy, 1);
      else K.key(L.start - 0.3, 0, prev, 1, 0, ease.linear).key(L.start + 0.3, 0, cy, 1, 0, ease.inOutCubic);
      prev = cy;
    });
  }

  /** A said line fades once the next one starts. */
  lineAlpha(g: string, t: number) {
    const i = this.lines.findIndex((L) => `l${L.i}` === g);
    const n1 = this.lines[i + 1], n2 = this.lines[i + 2];
    let a = 1;
    if (n1) a -= 0.75 * prog(t, n1.start - 0.3, n1.start + 0.2);
    if (n2) a -= 0.25 * prog(t, n2.start - 0.3, n2.start + 0.2);
    return a;
  }

  /** World position under the word being said (or the last one said in this plate). */
  head(t: number): { x: number; y: number; a: number } | null {
    let best: KWord | null = null;
    for (const k of this.kw) if (k.w.start <= t) best = k;
    if (!best) return null;
    const p = Lyrics.wordProgress(best.w, t);
    const wpx = (best.lay.width / 100) * best.size;
    const idle = t - best.w.end;
    return { x: best.x + wpx * ease.inOutQuad(p), y: best.y + 30, a: 1 - prog(idle, 0.5, 0.9) };
  }

  override render(f: Frame, out: THREE.WebGLRenderTarget): PostOverrides {
    const { renderer, comp } = this.ctx;
    const t = f.t, c = this.cam.at(t);
    clearRT(renderer, out, LIN.bone);
    const U = this.ui; U.clear();
    const ctx = U.ctx;
    // the stage: the app background with a faint blue wash from the top right
    const bg = ctx.createRadialGradient(1500, -200, 100, 1500, -200, 1500);
    bg.addColorStop(0, 'rgba(59,130,246,0.10)');
    bg.addColorStop(1, 'rgba(59,130,246,0)');
    ctx.fillStyle = bg; ctx.fillRect(0, 0, 1920, 1080);
    // words: hidden until said, Mirsal blue while said, slate after
    drawKaraoke(ctx, c, t, this.kw, { paper: true, outline: false, pop: 0.03, alpha: (g, tt) => this.lineAlpha(g, tt) });
    // the orb glides along under the word being said, a step behind (smoothed over 60 ms)
    const h0 = this.head(t), h1 = this.head(t - 0.06);
    if (h0 && h1) {
      const [sx, sy] = w2s(c, (h0.x + h1.x) / 2, h0.y);
      const appear = ease.outBack(clamp((t - this.lines[0]!.start + 0.2) / 0.35));
      drawOrb(ctx, sx, sy, 11 * appear, h0.a);
    }
    pill(ctx, String(this.ctx.params.fig ?? this.ctx.id), 56, 48);
    ctx.font = font(F.inter(500), 13);
    ctx.fillStyle = rgba('graphite', 0.6);
    ctx.textAlign = 'right';
    ctx.fillText('Rough cut', 1864, 70);
    ctx.textAlign = 'left';
    comp.draw(renderer, U.upload(), out);
    return {};
  }
}
