// REEL: the 30-second fast-cut ad for the Mirsal Creator (Haitham, 2026-10-04: "30 seconds, very very fast
// cuts, amazing visuals; prioritise the chat box, the sticker being created and the particles").
// 64 beats at 128 BPM = 30 s. Every cut sits on the beat grid (B(n)); the soundtrack is composed to the same
// grid (analysis/reel_music.py), so the picture and the music agree by construction.
// The look is the Mirsal app's clean iOS style (README §4). Real pictures: the G103 sheet (raw, then keyed),
// stickers from three library batches, particle sprites from P001/P009 (app/public/, not committed).
import type * as THREE from 'three';
import { Scene, type Frame, type PostOverrides } from '../engine/scene';
import { Layer2D, clearRT } from '../engine/gl';
import { LIN, rgba } from '../engine/palette';
import { F, font, measure } from '../engine/type';
import { clamp, ease, hash, lerp, TAU } from '../engine/util';
import { drawOrb } from './card';

export const BPM = 128, BEAT = 60 / BPM;
const B = (n: number) => n * BEAT;
const CX = 960, CY = 540;
const BLUE = '#3B82F6', INK = '#1E293B', GREY = '#64748B', GREEN = '#10B981', ORANGE = '#F97316';
const PASTEL = ['#DBEAFE', '#CFFAFE', '#EDE9FE', '#FCE7F3', '#FEF3C7', '#DCFCE7', '#E0F2FE', '#FFE4E6'];
const EMOJI = ['❤️', '⭐', '✨', '💖', '🎉', '💥', '🔥', '💙'];
const PROMPT = 'make me a superhero sticker pack';
const T_TYPE0 = B(1), T_TYPE1 = B(6.4);

type X = CanvasRenderingContext2D;
interface S { t: number; lt: number; len: number; p: number; i: number }
interface Shot { b0: number; b1: number; bg?: string; enter?: 'punch' | 'whip' | 'drop' | 'none'; draw: (x: X, s: S) => void }

const rr = (x: X, px: number, py: number, w: number, h: number, r: number) => { x.beginPath(); x.roundRect(px, py, w, h, r); };
const sat = (v: number) => clamp(v);
const outExpo = ease.outExpo, outBack = ease.outBack, outCubic = ease.outCubic;
const prog = (t: number, a: number, b: number) => clamp((t - a) / Math.max(1e-4, b - a));

export default class Reel extends Scene {
  ui = new Layer2D();
  s: HTMLImageElement[] = []; // superhero (G103)
  a: HTMLImageElement[] = []; // angel (G001)
  o: HTMLImageElement[] = []; // old man (G004)
  part: HTMLImageElement[] = [];
  sheet!: HTMLImageElement;
  keyed!: HTMLImageElement;
  shots: Shot[] = [];

  override async init() {
    const load = async (src: string) => { const im = new Image(); im.src = src; await im.decode(); return im; };
    const nine = (p: string) => Promise.all(Array.from({ length: 9 }, (_, i) => load(`stickers/${p}${i + 1}.png`)));
    [this.s, this.a, this.o, this.part, this.sheet, this.keyed] = await Promise.all([
      nine('s'), nine('a'), nine('o'),
      Promise.all([1, 2, 3, 5, 6, 7, 8].map((n) => load(`particles/p${n}.png`))), // p4 (a dark belt buckle) reads as dirt
      load('stickers/sheet.png'), load('stickers/keyed.png'),
    ]);
    this.shots = this.buildShots();
  }

  /** Any sticker by a running index over the three packs. */
  st(i: number) { const packs = [this.s, this.a, this.o]; const k = ((i % 27) + 27) % 27; return packs[Math.floor(k / 9)]![k % 9]!; }

  // ================================================================= drawing helpers
  /** A huge word punching in (Inter 800), centred; the full stop in Mirsal blue on light frames. */
  word(x: X, text: string, lt: number, o: { col?: string; dot?: string; size?: number; y?: number; drift?: number } = {}) {
    const fam = F.inter(800);
    let size = o.size ?? 230;
    const trk = -0.035;
    while (measure(text, fam, size, trk * size) > 1640 && size > 60) size -= 6;
    const punch = 1 + 0.42 * (1 - outExpo(sat(lt / 0.24)));
    const drift = 1 + (o.drift ?? 0.06) * lt;
    x.save();
    x.translate(CX, o.y ?? CY);
    x.scale(punch * drift, punch * drift);
    x.font = font(fam, size);
    x.letterSpacing = `${trk * size}px`;
    x.textAlign = 'left'; x.textBaseline = 'middle';
    const w = measure(text, fam, size, trk * size);
    const dotted = text.endsWith('.') && o.dot;
    const body = dotted ? text.slice(0, -1) : text;
    x.fillStyle = o.col ?? INK;
    x.globalAlpha = sat(lt / 0.05);
    x.fillText(body, -w / 2, size * 0.04);
    if (dotted) { x.fillStyle = o.dot!; x.fillText('.', -w / 2 + measure(body, fam, size, trk * size), size * 0.04); }
    x.restore();
    x.letterSpacing = '0px';
  }

  /** The Mirsal composer: white pill, the orb button, the text with a blue caret, the send button. */
  pill(x: X, cx: number, cy: number, w: number, h: number, text: string, t: number, o: { fs?: number; working?: number; caret?: boolean; press?: number } = {}) {
    const fs = o.fs ?? 44, fam = F.inter(400);
    x.save();
    x.shadowColor = 'rgba(15,23,42,0.10)'; x.shadowBlur = 40; x.shadowOffsetY = 14;
    x.fillStyle = '#FFFFFF'; rr(x, cx - w / 2, cy - h / 2, w, h, h / 2); x.fill();
    x.restore();
    x.strokeStyle = '#E2E8F0'; x.lineWidth = 1.5; rr(x, cx - w / 2, cy - h / 2, w, h, h / 2); x.stroke();
    // the AI's rolling cyan light
    const wk = o.working ?? 0;
    if (wk > 0.01) {
      const per = 2 * (w - h) + Math.PI * h;
      x.save();
      x.strokeStyle = rgba('ember', wk); x.lineWidth = 5; x.lineCap = 'round';
      x.shadowColor = rgba('ember', 0.8 * wk); x.shadowBlur = 24;
      x.setLineDash([per * 0.18, per * 0.82]); x.lineDashOffset = -t * per * 1.1;
      rr(x, cx - w / 2, cy - h / 2, w, h, h / 2); x.stroke();
      x.lineDashOffset = -t * per * 1.1 - per * 0.5; x.stroke();
      x.restore();
    }
    drawOrb(x, cx - w / 2 + h * 0.55, cy, h * 0.27);
    const tx = cx - w / 2 + h * 1.05;
    x.font = font(fam, fs); x.textBaseline = 'middle';
    if (text) { x.fillStyle = INK; x.fillText(text, tx, cy + 2); }
    else { x.fillStyle = 'rgba(100,116,139,0.75)'; x.fillText('Message', tx, cy + 2); }
    if (o.caret !== false && (Math.sin(t * TAU * 1.8) > -0.3 || (t > T_TYPE0 && t < T_TYPE1))) {
      x.fillStyle = BLUE; x.fillRect(tx + (text ? measure(text, fam, fs) : 0) + 3, cy - fs * 0.62, 4, fs * 1.24);
    }
    x.textBaseline = 'alphabetic';
    // send button
    const pr = o.press ?? 1;
    x.save();
    x.translate(cx + w / 2 - h * 0.55, cy); x.scale(pr, pr);
    x.fillStyle = text ? BLUE : '#CBD5E1';
    x.beginPath(); x.arc(0, 0, h * 0.36, 0, TAU); x.fill();
    this.arrow(x, h * 0.36);
    x.restore();
  }

  arrow(x: X, r: number) {
    x.strokeStyle = '#fff'; x.lineWidth = r * 0.17; x.lineCap = 'round'; x.lineJoin = 'round';
    x.beginPath(); x.moveTo(0, r * 0.42); x.lineTo(0, -r * 0.42); x.moveTo(-r * 0.36, -r * 0.08); x.lineTo(0, -r * 0.42); x.lineTo(r * 0.36, -r * 0.08); x.stroke();
  }

  typed(t: number) { return PROMPT.slice(0, Math.floor(sat((t - T_TYPE0) / (T_TYPE1 - T_TYPE0)) * PROMPT.length)); }

  /** A sticker with its own little loop (hop, tilt, squash, wiggle, spin), centred at cx, cy. */
  sticker(x: X, im: HTMLImageElement, cx: number, cy: number, size: number, t: number, o: { kind?: number; live?: number; pop?: number; rot?: number } = {}) {
    const live = o.live ?? 1, pop = o.pop ?? 1, k = o.kind ?? 0, w = TAU * 1.9 * t + k * 1.3;
    let dy = 0, rot = o.rot ?? 0, sx = 1, sy = 1;
    switch (k % 5) {
      case 0: dy = -size * 0.07 * Math.abs(Math.sin(w * 0.5)); sy = 1 + 0.04 * Math.cos(w); break;
      case 1: rot += 0.16 * Math.sin(w); break;
      case 2: sx = 1 + 0.07 * Math.sin(w); sy = 1 - 0.07 * Math.sin(w); break;
      case 3: rot += 0.09 * Math.sin(w * 1.7); dy = -size * 0.03 * Math.sin(w); break;
      case 4: rot += 0.25 * Math.sin(w * 0.5); dy = -size * 0.05 * Math.abs(Math.sin(w)); break;
    }
    if (pop <= 0) return;
    x.save();
    x.translate(cx, cy + dy * live);
    x.rotate(rot * live);
    x.scale(pop * lerp(1, sx, live), pop * lerp(1, sy, live));
    x.drawImage(im, -size / 2, -size / 2, size, size);
    x.restore();
  }

  /** A particle burst from (cx, cy) at t0: real sprites and emoji, flying out with drag and gravity. */
  burst(x: X, cx: number, cy: number, t0: number, t: number, o: { n?: number; seed?: number; power?: number; size?: number; g?: number; emoji?: string[]; ring?: boolean } = {}) {
    const age = t - t0;
    if (age < 0 || age > 2) return;
    const n = o.n ?? 40, seed = o.seed ?? 1, pw = o.power ?? 1, em = o.emoji ?? EMOJI;
    if (o.ring !== false && age < 0.35) {
      const r = 40 + 900 * pw * outExpo(age / 0.35);
      x.strokeStyle = `rgba(59,130,246,${0.5 * (1 - age / 0.35)})`; x.lineWidth = 14 * (1 - age / 0.35) + 1;
      x.beginPath(); x.arc(cx, cy, r, 0, TAU); x.stroke();
    }
    x.textAlign = 'center'; x.textBaseline = 'middle';
    for (let i = 0; i < n; i++) {
      const h = (j: number) => hash(i, seed, j);
      const life = 0.8 + 0.8 * h(3);
      if (age > life) continue;
      const ang = h(1) * TAU, sp = (650 + 1500 * h(2)) * pw, kd = 3.4;
      const d = (sp * (1 - Math.exp(-kd * age))) / kd;
      const px = cx + Math.cos(ang) * d, py = cy + Math.sin(ang) * d * 0.85 + 0.5 * 1100 * (o.g ?? 1) * age * age;
      const sz = (34 + 74 * h(4)) * (o.size ?? 1) * outBack(sat(age / 0.16));
      const a = 1 - clamp((age - life * 0.6) / (life * 0.4));
      x.save();
      x.globalAlpha = a;
      x.translate(px, py); x.rotate((h(5) - 0.5) * 9 * age);
      if (h(6) < 0.42) {
        const im = this.part[Math.floor(h(7) * this.part.length)]!;
        const sc = sz / Math.max(im.width, im.height);
        x.drawImage(im, (-im.width * sc) / 2, (-im.height * sc) / 2, im.width * sc, im.height * sc);
      } else {
        x.font = `${Math.round(sz)}px "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", sans-serif`;
        x.fillText(em[Math.floor(h(8) * em.length)]!, 0, 0);
      }
      x.restore();
    }
    x.textAlign = 'left'; x.textBaseline = 'alphabetic';
  }

  /** An iOS-style chat (phone proportions): header "Mirsal AI", conversation, composer. */
  chat(x: X, t: number, o: { scale?: number; bubble?: string; working?: number; sticker?: HTMLImageElement; stickerT?: number; hearts?: number[]; building?: number }) {
    const sc = o.scale ?? 1, W = 760, H = 960;
    x.save();
    x.translate(CX, CY); x.scale(sc, sc); x.translate(-W / 2, -H / 2);
    x.save();
    x.shadowColor = 'rgba(15,23,42,0.13)'; x.shadowBlur = 70; x.shadowOffsetY = 24;
    x.fillStyle = '#FFFFFF'; rr(x, 0, 0, W, H, 54); x.fill();
    x.restore();
    x.save(); rr(x, 0, 0, W, H, 54); x.clip();
    x.fillStyle = '#F5F8FC'; x.fillRect(0, 110, W, H - 230);
    x.fillStyle = '#E2E8F0'; x.fillRect(0, 110, W, 1.5); x.fillRect(0, H - 120, W, 1.5);
    // header
    const wk = o.working ?? 0;
    drawOrb(x, 70, 56, 28);
    if (wk > 0.01) {
      x.save(); x.strokeStyle = rgba('ember', wk); x.lineWidth = 4; x.lineCap = 'round'; x.shadowColor = rgba('ember', 0.7); x.shadowBlur = 12;
      x.beginPath(); x.arc(70, 56, 37, t * 6, t * 6 + 1.8); x.stroke(); x.restore();
    }
    x.font = font(F.inter(600), 30); x.fillStyle = INK; x.fillText('Mirsal AI', 118, 52);
    x.font = font(F.inter(400), 21); x.fillStyle = wk > 0.5 ? BLUE : GREY;
    x.fillText(wk > 0.5 ? 'creating your pack…' : 'online', 118, 82);
    // the outgoing bubble
    if (o.bubble) {
      const fam = F.inter(500), fs = 30;
      const bw = Math.min(560, measure(o.bubble, fam, fs) + 52), bx = W - 36 - bw;
      x.save(); x.shadowColor = 'rgba(37,99,235,0.2)'; x.shadowBlur = 20; x.shadowOffsetY = 6;
      x.fillStyle = BLUE; rr(x, bx, 146, bw, 70, 32); x.fill(); x.restore();
      x.font = font(fam, fs); x.fillStyle = '#fff'; x.fillText(o.bubble, bx + 26, 191);
      x.font = font(F.inter(400), 18); x.fillStyle = GREY; x.textAlign = 'right'; x.fillText('9:41', W - 64, 244); x.textAlign = 'left';
      this.ticks(x, W - 50, 238);
    }
    // Mirsal AI typing, and the sticker card building tile by tile
    if (o.building !== undefined) {
      const tb = o.building;
      x.fillStyle = '#FFFFFF'; rr(x, 36, 280, 150, 64, 32); x.fill();
      for (let i = 0; i < 3; i++) { x.fillStyle = `rgba(59,130,246,${0.35 + 0.65 * Math.max(0, Math.sin(t * 10 - i))})`; x.beginPath(); x.arc(78 + i * 32, 312, 8, 0, TAU); x.fill(); }
      x.save(); x.shadowColor = 'rgba(15,23,42,0.08)'; x.shadowBlur = 30; x.shadowOffsetY = 8;
      x.fillStyle = '#FFFFFF'; rr(x, 36, 372, 460, 460, 36); x.fill(); x.restore();
      for (let i = 0; i < 9; i++) {
        const k = sat((t - tb - i * 0.09) / 0.25), px = 36 + 30 + (i % 3) * 138, py = 372 + 30 + Math.floor(i / 3) * 138;
        x.fillStyle = '#EEF2F7'; rr(x, px, py, 124, 124, 22); x.fill();
        if (k > 0) { x.save(); x.globalAlpha = 0.5 + 0.5 * Math.sin(t * 8 + i); x.fillStyle = 'rgba(59,130,246,0.18)'; rr(x, px, py, 124 * k, 124, 22); x.fill(); x.restore(); }
      }
    }
    // a big sticker message
    if (o.sticker) {
      const k = outBack(sat((t - (o.stickerT ?? 0)) / 0.3));
      this.sticker(x, o.sticker, 250, 470, 400 * k, t, { kind: 1, live: 1 });
      if (o.hearts) for (const [i, h0] of o.hearts.entries()) this.burst(x, 250, 420, h0, t, { n: 22, seed: 40 + i, power: 0.45, size: 0.8, g: -0.5, emoji: ['❤️', '💖', '💙'], ring: false });
    }
    // composer
    x.fillStyle = '#FFFFFF'; x.fillRect(0, H - 118, W, 118);
    this.pill(x, W / 2, H - 60, W - 60, 76, '', t, { fs: 28, working: wk, caret: false });
    x.restore();
    x.restore();
  }

  ticks(x: X, cx: number, cy: number) {
    x.strokeStyle = BLUE; x.lineWidth = 2.4; x.lineCap = 'round'; x.lineJoin = 'round';
    for (const d of [-6, 0]) { x.beginPath(); x.moveTo(cx - 8 + d, cy); x.lineTo(cx - 3 + d, cy + 5); x.lineTo(cx + 6 + d, cy - 6); x.stroke(); }
  }

  check(x: X, cx: number, cy: number, r: number, k: number, col = GREEN) {
    if (k <= 0) return;
    x.save(); x.translate(cx, cy); x.scale(outBack(sat(k)), outBack(sat(k)));
    x.fillStyle = col; x.beginPath(); x.arc(0, 0, r, 0, TAU); x.fill();
    x.strokeStyle = '#fff'; x.lineWidth = r * 0.22; x.lineCap = 'round'; x.lineJoin = 'round';
    x.beginPath(); x.moveTo(-r * 0.42, 0); x.lineTo(-r * 0.1, r * 0.32); x.lineTo(r * 0.46, -r * 0.34); x.stroke();
    x.restore();
  }

  tile(x: X, cx: number, cy: number, size: number, col = '#FFFFFF', shadow = true) {
    x.save();
    if (shadow) { x.shadowColor = 'rgba(15,23,42,0.10)'; x.shadowBlur = 30; x.shadowOffsetY = 10; }
    x.fillStyle = col; rr(x, cx - size / 2, cy - size / 2, size, size, size * 0.16); x.fill();
    x.restore();
  }

  checker(x: X, px: number, py: number, w: number, h: number, cell = 28) {
    x.save(); x.beginPath(); x.rect(px, py, w, h); x.clip();
    x.fillStyle = '#FFFFFF'; x.fillRect(px, py, w, h);
    x.fillStyle = '#EEF2F7';
    for (let yy = 0; yy * cell < h; yy++) for (let xx = (yy % 2); xx * cell < w; xx += 2) x.fillRect(px + xx * cell, py + yy * cell, cell, cell);
    x.restore();
  }

  // ================================================================= the shots
  buildShots(): Shot[] {
    const sh: Shot[] = [];
    const add = (b0: number, b1: number, draw: Shot['draw'], o: Partial<Shot> = {}) => sh.push({ b0, b1, draw, ...o });

    // ---------- 1. the chat box: one sentence (beats 0-8, the build)
    add(0, 2, (x, s) => {
      const k = outExpo(sat(s.lt / 0.5));
      this.pill(x, CX, CY + (1 - k) * 80, 1440, 132, this.typed(s.t), s.t, { fs: 50 });
      x.globalAlpha = 1;
    }, { enter: 'none' });
    add(2, 3, (x, s) => { // macro on the caret
      const fs = 50, txt = this.typed(s.t);
      const caretX = CX - 720 + 132 * 1.05 + measure(txt, F.inter(400), fs);
      const z = 2.5 + 0.25 * s.p;
      x.save(); x.translate(CX, CY); x.scale(z, z); x.translate(-caretX + 120, -CY);
      this.pill(x, CX, CY, 1440, 132, txt, s.t, { fs });
      x.restore();
    });
    add(3, 4, (x, s) => { // tilted, pushing in
      x.save(); x.translate(CX, CY); x.rotate(-0.07 + 0.03 * s.p); x.scale(1.5 + 0.2 * s.p, 1.5 + 0.2 * s.p); x.translate(-CX + 260, -CY);
      this.pill(x, CX, CY, 1440, 132, this.typed(s.t), s.t, { fs: 50 });
      x.restore();
    });
    add(4, 5, (x, s) => this.word(x, 'One sentence.', s.lt, { col: '#FFFFFF' }), { bg: BLUE });
    add(5, 6, (x, s) => {
      x.save(); x.translate(CX, CY); x.scale(1.15 + 0.1 * s.p, 1.15 + 0.1 * s.p); x.translate(-CX - 200, -CY);
      this.pill(x, CX, CY, 1440, 132, this.typed(s.t), s.t, { fs: 50 });
      x.restore();
    });
    add(6, 7, (x, s) => { // the send button, pressed
      const press = s.lt < 0.18 ? 1 : 1 - 0.14 * Math.sin(sat((s.lt - 0.18) / 0.22) * Math.PI);
      for (let i = 0; i < 3; i++) {
        const a = s.lt - 0.18 - i * 0.07;
        if (a > 0) { x.strokeStyle = `rgba(59,130,246,${0.45 * (1 - sat(a / 0.5))})`; x.lineWidth = 6; x.beginPath(); x.arc(CX, CY, 190 + 420 * outExpo(sat(a / 0.5)), 0, TAU); x.stroke(); }
      }
      x.save(); x.translate(CX, CY); x.scale(press * (1 + 0.08 * s.p), press * (1 + 0.08 * s.p));
      x.shadowColor = 'rgba(37,99,235,0.35)'; x.shadowBlur = 60; x.shadowOffsetY = 20;
      x.fillStyle = BLUE; x.beginPath(); x.arc(0, 0, 190, 0, TAU); x.fill();
      x.shadowColor = 'transparent'; this.arrow(x, 190);
      x.restore();
    }, { bg: '#FFFFFF' });
    add(7, 8, (x, s) => { // the bubble flies up
      const k = outExpo(sat(s.lt / 0.32));
      const y = lerp(1300, CY, k), sc = lerp(0.7, 1.35, k) + 0.08 * s.p;
      const fam = F.inter(500), fs = 54, w = measure(PROMPT, fam, fs) + 90;
      x.save(); x.translate(CX, y); x.scale(sc, sc);
      x.shadowColor = 'rgba(37,99,235,0.3)'; x.shadowBlur = 40; x.shadowOffsetY = 16;
      x.fillStyle = BLUE; rr(x, -w / 2, -60, w, 120, 56); x.fill();
      x.shadowColor = 'transparent';
      x.font = font(fam, fs); x.fillStyle = '#fff'; x.textBaseline = 'middle'; x.fillText(PROMPT, -w / 2 + 45, 2); x.textBaseline = 'alphabetic';
      x.restore();
    });

    // ---------- 2. the drop: Mirsal AI gets to work (beats 8-12)
    add(8, 10, (x, s) => {
      this.chat(x, s.t, { scale: 1.06 + 0.06 * s.p, bubble: PROMPT, working: 1, building: B(8.5) });
    }, { enter: 'drop' });
    add(10, 11, (x, s) => { // the orb, working
      const r = 230 + 20 * s.p;
      for (let i = 0; i < 3; i++) {
        x.save(); x.strokeStyle = rgba('ember', 0.9 - i * 0.25); x.lineWidth = 12 - i * 3; x.lineCap = 'round';
        x.shadowColor = rgba('ember', 0.8); x.shadowBlur = 30;
        const a = s.t * (7 - i * 2) + i * 2;
        x.beginPath(); x.arc(CX, CY, r + 50 + i * 38, a, a + 1.4 + i * 0.4); x.stroke(); x.restore();
      }
      drawOrb(x, CX, CY, r);
      for (let i = 0; i < 14; i++) {
        const a = hash(i, 9) * TAU + s.t * (1.5 + hash(i, 10) * 2), d = r + 120 + 140 * hash(i, 11);
        x.fillStyle = `rgba(34,211,238,${0.5 + 0.5 * hash(i, 12)})`;
        x.beginPath(); x.arc(CX + Math.cos(a) * d, CY + Math.sin(a) * d, 4 + 6 * hash(i, 13), 0, TAU); x.fill();
      }
    }, { bg: '#FFFFFF' });
    add(11, 12, (x, s) => this.word(x, 'Creating…', s.lt, { dot: BLUE }), { bg: '#FFFFFF' });

    // ---------- 3. the sheet: generated, keyed, cut (beats 12-20)
    const SZ = 820;
    add(12, 14, (x, s) => {
      const k = outExpo(sat(s.lt / 0.22));
      const sc = lerp(1.35, 1, k) + 0.05 * s.p, rot = lerp(-0.08, 0, k);
      const sweep = sat((s.t - B(13)) / (B(14) - B(13) - 0.05));
      x.save(); x.translate(CX, CY); x.rotate(rot); x.scale(sc, sc);
      x.save(); x.shadowColor = 'rgba(15,23,42,0.18)'; x.shadowBlur = 60; x.shadowOffsetY = 24;
      x.fillStyle = '#fff'; rr(x, -SZ / 2 - 14, -SZ / 2 - 14, SZ + 28, SZ + 28, 40); x.fill(); x.restore();
      x.save(); rr(x, -SZ / 2, -SZ / 2, SZ, SZ, 28); x.clip();
      x.drawImage(this.sheet, -SZ / 2, -SZ / 2, SZ, SZ);
      if (sweep > 0) {
        const yy = -SZ / 2 + SZ * sweep;
        x.save(); x.beginPath(); x.rect(-SZ / 2, -SZ / 2, SZ, SZ * sweep); x.clip();
        this.checker(x, -SZ / 2, -SZ / 2, SZ, SZ);
        x.drawImage(this.keyed, -SZ / 2, -SZ / 2, SZ, SZ);
        x.restore();
        if (sweep < 1) {
          x.save(); x.shadowColor = rgba('ember', 1); x.shadowBlur = 40;
          x.fillStyle = rgba('ember', 1); x.fillRect(-SZ / 2, yy - 3, SZ, 6); x.restore();
        }
      }
      x.restore();
      x.restore();
      if (s.lt < 0.6) { x.font = font(F.inter(600), 30); x.fillStyle = GREY; x.textAlign = 'center'; x.fillText('Sheet · 3×3 · 2K', CX, CY + SZ / 2 + 80); x.textAlign = 'left'; }
    });
    add(14, 15, (x, s) => { // the cells split apart
      const k = outBack(sat(s.lt / 0.3), 1.4), gap = 90 * k, cell = SZ / 3, src = this.keyed.width / 3;
      for (let i = 0; i < 9; i++) {
        const c = i % 3 - 1, r = Math.floor(i / 3) - 1;
        const px = CX + c * (cell + gap), py = CY + r * (cell + gap);
        const rot = (hash(i, 3) - 0.5) * 0.25 * k;
        x.save(); x.translate(px, py); x.rotate(rot);
        this.tile(x, 0, 0, cell - 8, '#FFFFFF');
        x.drawImage(this.keyed, (i % 3) * src, Math.floor(i / 3) * src, src, src, -cell / 2 + 6, -cell / 2 + 6, cell - 12, cell - 12);
        x.restore();
      }
    });
    add(15, 16, (x, s) => this.word(x, 'Cut.', s.lt, { col: '#FFFFFF' }), { bg: BLUE });
    add(16, 18, (x, s) => { // nine stickers pop in on 16ths, each checked
      const size = 250, g = 26;
      for (let i = 0; i < 9; i++) {
        const c = i % 3 - 1, r = Math.floor(i / 3) - 1;
        const t0 = B(16) + i * B(0.25), pop = outBack(sat((s.t - t0) / 0.22), 2);
        if (pop <= 0) continue;
        const px = CX + c * (size + g), py = CY + r * (size + g);
        x.save(); x.translate(px, py); x.scale(pop, pop); this.tile(x, 0, 0, size); x.restore();
        this.sticker(x, this.s[i]!, px, py, size * 0.86, s.t, { kind: i, live: 0, pop });
        this.check(x, px + size / 2 - 26, py - size / 2 + 26, 24, (s.t - t0 - 0.14) / 0.18);
      }
    });
    add(18, 19, (x, s) => {
      this.word(x, 'Checked.', s.lt, { col: '#FFFFFF' });
    }, { bg: GREEN });
    add(19, 20, (x, s) => {
      const z = 1 + 0.12 * s.p;
      x.save(); x.translate(CX, CY); x.scale(z, z); x.translate(-CX, -CY);
      this.tile(x, CX, CY, 760);
      this.sticker(x, this.s[8]!, CX, CY, 660, s.t, { live: 0 });
      this.check(x, CX + 300, CY - 300, 62, s.lt / 0.2);
      x.restore();
    });

    // ---------- 4. animated: eight half-beat cuts, then the word, then the whole sheet (beats 20-28)
    for (let i = 0; i < 8; i++) {
      add(20 + i * 0.5, 20.5 + i * 0.5, (x, s) => {
        const z = 1.08 - 0.08 * s.p;
        this.sticker(x, this.st(i * 4 + 1), CX + (i % 2 ? 1 : -1) * 40 * s.p, CY, 700 * z, s.t + i, { kind: i, live: 1 });
      }, { bg: PASTEL[i % PASTEL.length], enter: i % 2 ? 'whip' : 'punch' });
    }
    add(24, 26, (x, s) => {
      for (let i = 0; i < 8; i++) {
        const a = (i / 8) * TAU + s.t * 1.1, rx = 700, ry = 330;
        this.sticker(x, this.st(i * 3 + 2), CX + Math.cos(a) * rx, CY + Math.sin(a) * ry, 230, s.t, { kind: i, live: 1, pop: outBack(sat((s.lt - i * 0.03) / 0.25)) });
      }
      this.word(x, 'Animated.', s.lt, { dot: BLUE, size: 210 });
    }, { bg: '#FFFFFF' });
    add(26, 28, (x, s) => {
      const z = lerp(1.3, 0.95, outCubic(s.p)), size = 250, g = 26;
      x.save(); x.translate(CX, CY); x.scale(z, z); x.translate(-CX, -CY);
      for (let i = 0; i < 9; i++) {
        const c = i % 3 - 1, r = Math.floor(i / 3) - 1, px = CX + c * (size + g), py = CY + r * (size + g);
        this.tile(x, px, py, size);
        this.sticker(x, this.s[i]!, px, py, size * 0.86, s.t, { kind: i, live: 1 });
      }
      x.restore();
    });

    // ---------- 5. particles (beats 28-40)
    add(28, 30, (x, s) => {
      const t0 = B(29);
      const squash = s.t < t0 ? 1 - 0.12 * sat((s.t - B(28.4)) / (t0 - B(28.4))) : 1 + 0.18 * Math.exp(-(s.t - t0) / 0.08);
      this.burst(x, CX, CY, t0, s.t, { n: 60, seed: 1, power: 1.2 });
      x.save(); x.translate(CX, CY + 260); x.scale(1 / Math.sqrt(squash), squash); x.translate(-CX, -CY - 260);
      this.sticker(x, this.s[8]!, CX, CY, 600, s.t, { kind: 0, live: 0.3 });
      x.restore();
    }, { bg: '#FFFFFF' });
    add(30, 31, (x, s) => {
      this.burst(x, CX, CY, B(30), s.t, { n: 70, seed: 2, power: 1.5, ring: false });
      this.word(x, 'Particles.', s.lt, { col: '#FFFFFF' });
    }, { bg: BLUE });
    for (let i = 0; i < 4; i++) {
      add(31 + i, 32 + i, (x, s) => {
        const t0 = B(31 + i);
        this.burst(x, CX, CY, t0, s.t, { n: 55, seed: 10 + i, power: 1.1 });
        this.burst(x, CX, CY, t0 + B(0.5), s.t, { n: 30, seed: 20 + i, power: 0.8, ring: false });
        this.sticker(x, this.st([2, 11, 19, 6][i]!), CX, CY, 560 * (1 + 0.15 * Math.exp(-s.lt / 0.1)), s.t, { kind: i + 1, live: 1 });
      }, { bg: i % 2 ? '#EFF6FF' : '#FFFFFF', enter: 'punch' });
    }
    add(35, 36, (x, s) => {
      const spots: [number, number][] = [[480, 380], [1440, 360], [960, 760]];
      spots.forEach(([px, py], j) => {
        const t0 = B(35) + j * B(0.25);
        this.burst(x, px, py, t0, s.t, { n: 40, seed: 30 + j, power: 0.9 });
        this.sticker(x, this.st(j * 9 + 4), px, py, 330, s.t, { kind: j, pop: outBack(sat((s.t - t0) / 0.2)) });
      });
    }, { bg: '#FFFFFF' });
    add(36, 39, (x, s) => {
      this.chat(x, s.t, { scale: 1.0 + 0.07 * s.p, bubble: PROMPT, sticker: this.s[2]!, stickerT: B(36), hearts: [B(37), B(37.5), B(38)] });
    }, { enter: 'drop' });
    add(39, 40, (x, s) => this.word(x, 'In your chat.', s.lt, { col: '#FFFFFF' }), { bg: BLUE });

    // ---------- 6. batching and no dead ends (beats 40-46)
    add(40, 42, (x, s) => {
      const packs = [this.s, this.a, this.o], names = ['Superhero Dubai', 'Angel reading', 'Old man, Pixar'];
      for (let j = 0; j < 3; j++) {
        const t0 = B(40) + j * B(0.5), k = outExpo(sat((s.t - t0) / 0.3));
        const cx = 360 + j * 600 + (1 - k) * 1400, cw = 520, chh = 660;
        x.save(); x.shadowColor = 'rgba(15,23,42,0.12)'; x.shadowBlur = 50; x.shadowOffsetY = 18;
        x.fillStyle = '#fff'; rr(x, cx - cw / 2, CY - chh / 2, cw, chh, 40); x.fill(); x.restore();
        for (let i = 0; i < 9; i++) {
          const ts = 140, px = cx - ts - 10 + (i % 3) * (ts + 10), py = CY - 170 + Math.floor(i / 3) * (ts + 10);
          x.fillStyle = '#F1F5F9'; rr(x, px - ts / 2, py - ts / 2, ts, ts, 22); x.fill();
          const ready = sat((s.t - t0 - 0.15 - i * 0.06) / 0.15);
          this.sticker(x, packs[j]![i]!, px, py, ts * 0.86, s.t, { kind: i, live: 0.6, pop: outBack(ready) });
        }
        x.font = font(F.inter(600), 28); x.fillStyle = INK; x.fillText(names[j]!, cx - cw / 2 + 36, CY + 250);
        const bar = sat((s.t - t0) / (B(1.6)));
        x.fillStyle = '#E2E8F0'; rr(x, cx - cw / 2 + 36, CY + 280, cw - 72, 12, 6); x.fill();
        x.fillStyle = bar >= 1 ? GREEN : BLUE; rr(x, cx - cw / 2 + 36, CY + 280, (cw - 72) * bar, 12, 6); x.fill();
      }
      x.font = font(F.inter(700), 34); x.fillStyle = BLUE; x.textAlign = 'center'; x.fillText('3 in flight', CX, 120); x.textAlign = 'left';
    }, { bg: '#F7F8FA' });
    add(42, 43, (x, s) => this.word(x, 'All at once.', s.lt, { col: '#FFFFFF' }), { bg: BLUE });
    add(43, 45, (x, s) => {
      const tap = B(44), allowed = sat((s.t - tap) / 0.2), size = 560;
      this.tile(x, CX, CY - 60, size);
      this.sticker(x, this.s[0]!, CX, CY - 60, size * 0.86, s.t, { kind: 2, live: allowed });
      x.save(); rr(x, CX - size / 2, CY - 60 - size / 2, size, size, size * 0.16); x.clip();
      x.globalAlpha = 1 - allowed;
      x.strokeStyle = 'rgba(249,115,22,0.35)'; x.lineWidth = 10;
      for (let d = -size; d < size * 2; d += 44) { x.beginPath(); x.moveTo(CX - size / 2 + d, CY - 60 - size / 2); x.lineTo(CX - size / 2 + d - size, CY - 60 + size / 2); x.stroke(); }
      x.restore();
      x.strokeStyle = allowed > 0.5 ? GREEN : ORANGE; x.lineWidth = 8; rr(x, CX - size / 2, CY - 60 - size / 2, size, size, size * 0.16); x.stroke();
      x.font = font(F.inter(500), 30); x.fillStyle = GREY; x.textAlign = 'center';
      x.fillText(allowed > 0.5 ? 'Allowed by you · Take it back' : 'The cape crosses the edge of its square.', CX, CY + 290);
      // the button, on the picture
      const press = s.t < tap ? 1 : 1 - 0.12 * Math.sin(sat((s.t - tap) / 0.2) * Math.PI);
      x.save(); x.translate(CX, CY + 150); x.scale(press, press);
      x.fillStyle = allowed > 0.5 ? GREEN : BLUE; rr(x, -170, -38, 340, 76, 38); x.fill();
      x.font = font(F.inter(600), 30); x.fillStyle = '#fff'; x.textBaseline = 'middle';
      x.fillText(allowed > 0.5 ? 'Allowed' : 'Use it anyway', 0, 2); x.textBaseline = 'alphabetic';
      x.restore(); x.textAlign = 'left';
      this.check(x, CX + size / 2 - 40, CY - 60 - size / 2 + 40, 40, (s.t - tap - 0.1) / 0.2);
    }, { bg: '#FFFFFF' });
    add(45, 46, (x, s) => this.word(x, 'No dead ends.', s.lt, { dot: BLUE }), { bg: '#FFFFFF' });

    // ---------- 7. hyper montage (beats 46-50): quarter-beat flashes, then bursts
    for (let i = 0; i < 8; i++) {
      add(46 + i * 0.25, 46.25 + i * 0.25, (x, s) => {
        this.sticker(x, this.st(i * 5 + 3), CX, CY, 820, s.t, { kind: i, live: 1, rot: (i % 2 ? 1 : -1) * 0.06 });
      }, { bg: PASTEL[(i + 3) % PASTEL.length], enter: 'none' });
    }
    for (let i = 0; i < 4; i++) {
      add(48 + i * 0.5, 48.5 + i * 0.5, (x, s) => {
        const t0 = B(48 + i * 0.5);
        this.burst(x, CX, CY, t0, s.t, { n: 50, seed: 60 + i, power: 1.3 });
        this.sticker(x, this.st(i * 7 + 8), CX, CY, 520, s.t, { kind: i, live: 1 });
      }, { bg: i % 2 ? BLUE : '#FFFFFF', enter: 'punch' });
    }

    // ---------- 8. the words (beats 50-56)
    add(50, 51, (x, s) => this.word(x, 'Your words.', s.lt, { dot: BLUE }), { bg: '#FFFFFF' });
    add(51, 52, (x, s) => this.word(x, 'Your taste.', s.lt, { col: '#FFFFFF' }), { bg: BLUE });
    add(52, 54, (x, s) => {
      for (let i = 0; i < 14; i++) {
        const fall = (s.lt * (500 + 300 * hash(i, 71)) + hash(i, 72) * 1300) % 1500 - 250;
        this.sticker(x, this.st(i * 2), 120 + hash(i, 73) * 1680, fall, 150 + 90 * hash(i, 74), s.t, { kind: i, rot: (hash(i, 75) - 0.5) * 1.2 });
      }
      x.save(); x.fillStyle = 'rgba(247,248,250,0.55)'; x.fillRect(0, 380, 1920, 320); x.restore();
      this.word(x, 'Your stickers.', s.lt, { dot: BLUE });
    }, { bg: '#FFFFFF' });
    add(54, 56, (x, s) => { // one more request, answered at once
      const txt = 'make me a falcon pack'.slice(0, Math.floor(sat(s.lt / B(0.9)) * 21));
      this.pill(x, CX, 840, 1300, 120, txt, s.t, { fs: 46, working: sat((s.t - B(55)) / 0.1), press: 1 });
      const t0 = B(55);
      for (let i = 0; i < 9; i++) {
        const pop = outBack(sat((s.t - t0 - i * B(0.125)) / 0.2), 2);
        const px = CX + ((i % 9) - 4) * 200, py = 400;
        if (pop > 0) { x.save(); x.translate(px, py); x.scale(pop, pop); this.tile(x, 0, 0, 180); x.restore(); this.sticker(x, this.st(9 + i), px, py, 160, s.t, { kind: i, pop }); }
      }
    }, { bg: '#F7F8FA' });

    // ---------- 9. the logo (beats 56-64)
    add(56, 60, (x, s) => {
      const pull = sat((s.t - B(58.5)) / (B(59.5) - B(58.5)));
      const orbR = 120 * outBack(sat(s.lt / 0.4)) * (1 + 0.25 * Math.exp(-Math.max(0, s.t - B(59.5)) / 0.12) * (s.t > B(59.5) ? 1 : 0));
      for (let i = 0; i < 12; i++) {
        const a = (i / 12) * TAU + s.t * 0.9, rad = lerp(420, 0, ease.inCubic(pull));
        if (pull >= 1) break;
        this.sticker(x, this.st(i * 2 + 1), CX + Math.cos(a) * rad * 1.5, CY + Math.sin(a) * rad, 180 * (1 - pull * 0.8), s.t, { kind: i, pop: outBack(sat((s.lt - i * 0.04) / 0.3)) });
      }
      if (s.t > B(59.5)) this.burst(x, CX, CY, B(59.5), s.t, { n: 70, seed: 90, power: 1.3, emoji: ['✨', '💙', '⭐', '💖'], ring: false });
      drawOrb(x, CX, CY, orbR);
    }, { bg: '#FFFFFF' });
    add(60, 64, (x, s) => {
      const k = outExpo(sat(s.lt / 0.5));
      const fam = F.inter(800), size = 150;
      x.font = font(fam, size); x.letterSpacing = `${-0.02 * size}px`;
      const w = measure('Mirsal Creator', fam, size, -0.02 * size);
      const total = w + 220, x0 = CX - total / 2;
      drawOrb(x, x0 + 85, CY - 70, 85 * outBack(sat(s.lt / 0.4)));
      x.fillStyle = INK; x.globalAlpha = k; x.textBaseline = 'middle';
      x.fillText('Mirsal Creator', x0 + 220 + (1 - k) * 60, CY - 70);
      x.letterSpacing = '0px'; x.globalAlpha = 1;
      // the one button
      const tap = B(62), press = s.t < tap ? 1 : 1 - 0.12 * Math.sin(sat((s.t - tap) / 0.22) * Math.PI);
      const ba = outBack(sat((s.lt - 0.35) / 0.35));
      x.save(); x.translate(CX, CY + 150); x.scale(press * ba, press * ba);
      x.shadowColor = 'rgba(37,99,235,0.35)'; x.shadowBlur = 40; x.shadowOffsetY = 14;
      x.fillStyle = BLUE; rr(x, -190, -50, 380, 100, 50); x.fill();
      x.shadowColor = 'transparent';
      x.font = font(F.inter(700), 40); x.fillStyle = '#fff'; x.textAlign = 'center';
      x.fillText('One click', 0, 3);
      x.restore(); x.textAlign = 'left'; x.textBaseline = 'alphabetic';
      if (s.t > tap) this.burst(x, CX, CY + 130, tap, s.t, { n: 16, seed: 99, power: 0.35, size: 0.55, g: -0.4, emoji: ['✨'], ring: false });
      // fade out to the stage at the very end
      const out = sat((s.t - (B(64) - 0.45)) / 0.45);
      if (out > 0) { x.fillStyle = `rgba(247,248,250,${out})`; x.fillRect(0, 0, 1920, 1080); }
    }, { bg: '#FFFFFF', enter: 'drop' });
    return sh;
  }

  override render(f: Frame, out: THREE.WebGLRenderTarget): PostOverrides {
    const { renderer, comp } = this.ctx;
    const t = f.t;
    const i = this.shots.findIndex((s) => t >= B(s.b0) && t < B(s.b1));
    const shot = this.shots[i < 0 ? this.shots.length - 1 : i]!;
    const t0 = B(shot.b0), len = B(shot.b1) - t0, lt = t - t0;
    clearRT(renderer, out, LIN.bone);
    const U = this.ui;
    U.clear(shot.bg ?? '#F7F8FA');
    const x = U.ctx;
    x.save();
    const en = shot.enter ?? 'punch';
    if (en === 'punch' || en === 'drop') {
      const z = 1 + (en === 'drop' ? 0.12 : 0.06) * (1 - outExpo(sat(lt / 0.22)));
      x.translate(CX, CY); x.scale(z, z); x.translate(-CX, -CY);
    } else if (en === 'whip') {
      x.translate(700 * (1 - outExpo(sat(lt / 0.16))), 0);
    }
    shot.draw(x, { t, lt, len, p: sat(lt / len), i });
    x.restore();
    comp.draw(renderer, U.upload(), out);
    const drop = (b: number) => (t >= B(b) ? Math.exp(-(t - B(b)) / 0.09) : 0);
    return {
      zoom: 1 + 0.012 * Math.exp(-lt / 0.07),
      flash: 0.35 * drop(8) + 0.5 * drop(59.5) + 0.25 * drop(36),
    };
  }
}
