// CARD: the rough-cut plate. Until a plate has its own scene, the timeline points at this one: the plate's
// lines as karaoke on the graph paper, the orb riding under the word being said, the camera following the
// line, and the plate's name in the corner. It reads its lines from ctx.params.lines (queries, as lineOf
// takes them), so it re-times itself to any read like every other plate.
import type * as THREE from 'three';
import { Scene, type Frame, type PostOverrides } from '../engine/scene';
import { Layer2D } from '../engine/gl';
import { LineBatch } from '../engine/lines';
import { rgba } from '../engine/palette';
import { F } from '../engine/type';
import { Lyrics, type Line } from '../engine/lyrics';
import { ease, prog, pulse } from '../engine/util';
import { Cam2D, gridPass, setGrid, drawKaraoke, placeRow, rowWidth, w2s, label, drawPen, lineOf, type KWord } from './_vo';

const SIZE = 74, MAXW = 1500, LEAD = 1.32;

export default class Card extends Scene {
  cam = new Cam2D();
  grid = gridPass(24, 96);
  ui = new Layer2D();
  fx = new LineBatch(8000);
  kw: KWord[] = [];
  lines: Line[] = [];

  override init() {
    const ly = this.ctx.lyrics;
    const fam = F.archivo(100, 800);
    this.lines = (this.ctx.params.lines as string[]).map((q) => lineOf(ly, q));
    let y = 0;
    const lineY: number[] = [];
    for (const L of this.lines) {
      // wrap the line into rows no wider than MAXW
      const rows: typeof L.words[] = [[]];
      for (const w of L.words) {
        const row = rows[rows.length - 1]!;
        if (row.length && rowWidth([...row, w].map((x) => x.w), SIZE, fam) > MAXW) rows.push([w]);
        else row.push(w);
      }
      lineY.push(y);
      for (const r of rows) {
        this.kw.push(...placeRow(r, -MAXW / 2, y, SIZE, fam, `l${L.i}`, { ant: 0.25 }).words);
        y += SIZE * LEAD;
      }
      y += SIZE * 0.6;
    }
    // the camera holds on a line while it is said, then moves to the next one as it starts
    // (a key is where the camera ARRIVES, so each move gets a hold key before it)
    const K = this.cam;
    let prev = 0, roll = 0;
    this.lines.forEach((L, i) => {
      const rowsH = (i + 1 < lineY.length ? lineY[i + 1]! - SIZE * 0.6 : y - SIZE * 0.6) - lineY[i]!;
      const cy = lineY[i]! + rowsH / 2 - SIZE * 0.45;
      const r = i % 2 ? 0.004 : -0.004;
      if (i === 0) K.key(this.ctx.start, 0, cy, 1, r);
      else K.key(L.start - 0.3, 0, prev, 1, roll, ease.linear).key(L.start + 0.35, 0, cy, 1, r, ease.inOutCubic);
      prev = cy; roll = r;
    });
    K.key(this.ctx.end, 0, K.keys[K.keys.length - 1]!.cy + 20, 1.04, 0, ease.linear);
  }

  /** A said line dims once the next one starts and is gone by the one after. */
  lineAlpha(g: string, t: number) {
    const i = this.lines.findIndex((L) => `l${L.i}` === g);
    const n1 = this.lines[i + 1], n2 = this.lines[i + 2];
    let a = 1;
    if (n1) a -= 0.65 * prog(t, n1.start - 0.3, n1.start + 0.2);
    if (n2) a -= 0.35 * prog(t, n2.start - 0.3, n2.start + 0.2);
    return a;
  }

  /** Screen position of the orb: under the word being said (or the last one said in this plate). */
  head(t: number): [number, number] | null {
    let best: KWord | null = null;
    for (const k of this.kw) if (k.w.start <= t) best = k;
    if (!best || t > best.w.end + 0.6) return null;
    const p = Lyrics.wordProgress(best.w, t);
    const wpx = (best.lay.width / 100) * best.size;
    return w2s(this.cam.at(t), best.x + wpx * p, best.y + 16);
  }

  override render(f: Frame, out: THREE.WebGLRenderTarget): PostOverrides {
    const { renderer, comp } = this.ctx;
    const t = f.t, c = this.cam.at(t);
    setGrid(this.grid, c, { reveal: [0, 0, 1e5], ink: 0.6 });
    this.grid.render(renderer, out);
    const U = this.ui; U.clear();
    const ctx = U.ctx;
    drawKaraoke(ctx, c, t, this.kw, { pop: 0.04, alpha: (g, tt) => this.lineAlpha(g, tt) });
    // the plate's name, and a reminder that this is the rough cut
    label(ctx, String(this.ctx.params.fig ?? this.ctx.id).toUpperCase(), 56, 64, { size: 14, col: rgba('bone', 0.7) });
    label(ctx, 'ROUGH CUT · PROVISIONAL TIMING', 1864, 64, { size: 12, col: rgba('ash', 0.6), align: 'right' });
    comp.draw(renderer, U.upload(), out);
    const X = this.fx; X.clear();
    drawPen(X, t, (tt) => this.head(tt), { scale: 0.9, rate: 40 });
    X.render(renderer, out);
    const first = this.lines[0]?.start ?? this.ctx.start;
    return { bloom: 0.65, bloomThreshold: 0.7, halation: 0.3, zoom: 1 + 0.015 * pulse(t, first, 0.12) };
  }
}
