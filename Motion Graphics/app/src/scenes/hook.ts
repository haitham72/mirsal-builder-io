// HOOK: "What if one sentence could become a whole sticker pack… already moving, already in your chat?"
// A Mirsal chat window in the app's clean iOS look.
//  1. Close on the composer: the sentence types itself as it is said, a blue caret leading.
//  2. On "pack…" the send button is pressed: the text flies up into a blue outgoing bubble, the camera
//     eases back, and a cyan light rolls around the composer while Mirsal AI works.
//  3. On "already": a sticker sheet card arrives from Mirsal AI, its nine real stickers popping in one by one.
//  4. On "moving": every sticker starts its own little loop (bob, tilt, squash, wiggle).
//  5. On "already in your chat": the whole chat is in frame, the card gets its time and read ticks.
// Everything is a function of t, keyed to the words (lineOf / wordOf), so a new read re-times it.
import type * as THREE from 'three';
import { Scene, type Frame, type PostOverrides } from '../engine/scene';
import { Layer2D, clearRT } from '../engine/gl';
import { LIN, rgba } from '../engine/palette';
import { F, font, measure } from '../engine/type';
import { Lyrics, type Line, type Word } from '../engine/lyrics';
import { clamp, ease, lerp, prog, TAU } from '../engine/util';
import { Cam2D, setWorld, lineOf, wordOf, type Cam } from './_vo';
import { drawOrb } from './card';

// the window, in world px (y down), centred on 0,0
const WX = -420, WY = -470, WW = 840, WH = 940, WR = 44;
const HEAD = 100; // header height
const CY = 414; // composer centre line
const PX0 = -384, PX1 = 300, PH = 64; // composer pill
const SEND = { x: 350, y: CY, r: 30 };
// the sticker card (incoming)
const TILE = 140, GAP = 12, PAD = 28;
const CARD = { x: -384, y: -205, w: PAD * 2 + TILE * 3 + GAP * 2, h: PAD * 2 + TILE * 3 + GAP * 2 + 48 };
const BUB_MAXW = 500, BUB_FS = 26, BUB_LH = 34;

const rr = (c: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) => { c.beginPath(); c.roundRect(x, y, w, h, r); };

export default class Hook extends Scene {
  cam = new Cam2D();
  ui = new Layer2D();
  L!: Line;
  msgWords: Word[] = [];
  msg = '';
  bubbleLines: string[] = [];
  img: HTMLImageElement[] = [];
  tSend = 0; tCard = 0; tMove = 0; tChat = 0; tEnd = 0;

  override async init() {
    const ly = this.ctx.lyrics;
    this.L = lineOf(ly, 'What if one sentence');
    const pack = wordOf(this.L, 'pack');
    this.msgWords = this.L.words.slice(0, pack.index + 1);
    this.msg = this.msgWords.map((w) => w.w).join(' ');
    this.tSend = pack.end + 0.06;
    this.tCard = wordOf(this.L, 'already', 0).start - 0.12;
    this.tMove = wordOf(this.L, 'moving').start;
    this.tChat = wordOf(this.L, 'already', 1).start;
    this.tEnd = wordOf(this.L, 'chat').start;
    // the outgoing bubble's text, wrapped
    const fam = F.inter(500);
    let cur = '';
    for (const w of this.msg.split(' ')) {
      const next = cur ? `${cur} ${w}` : w;
      if (measure(next, fam, BUB_FS) > BUB_MAXW - 44 && cur) { this.bubbleLines.push(cur); cur = w; } else cur = next;
    }
    if (cur) this.bubbleLines.push(cur);
    // the stickers (real ones, from a library batch; app/public/stickers/, not committed)
    this.img = await Promise.all(Array.from({ length: 9 }, async (_, i) => {
      const im = new Image();
      im.src = `stickers/s${i + 1}.png`;
      await im.decode();
      return im;
    }));
    // camera: close on the composer while typing, ease back after the send, a slow push at the end
    const K = this.cam;
    K.key(0, -20, CY - 10, 2.25);
    K.key(this.tSend - 0.05, 10, CY - 16, 2.32, 0, ease.linear);
    K.key(this.tSend + 0.9, 0, 14, 1.06, 0, ease.inOutCubic);
    K.key(this.ctx.end, 0, 8, 1.1, 0, ease.linear);
  }

  /** How many characters of the message are typed at t (each word types itself while it is said). */
  typed(t: number) {
    let n = 0;
    for (const w of this.msgWords) {
      const p = Lyrics.wordProgress(w, t);
      n += Math.round(p * w.w.length);
      if (p < 1) return n;
      n += 1;
    }
    return this.msg.length;
  }

  override render(f: Frame, out: THREE.WebGLRenderTarget): PostOverrides {
    const { renderer, comp } = this.ctx;
    const t = f.t, c = this.cam.at(t);
    clearRT(renderer, out, LIN.bone);
    const U = this.ui; U.clear();
    const x = U.ctx;
    // the stage: a faint blue wash
    const bg = x.createRadialGradient(1600, -100, 50, 1600, -100, 1500);
    bg.addColorStop(0, 'rgba(59,130,246,0.11)'); bg.addColorStop(1, 'rgba(59,130,246,0)');
    x.fillStyle = bg; x.fillRect(0, 0, 1920, 1080);

    const intro = ease.outCubic(prog(t, 0, 0.45));
    x.globalAlpha = intro;
    this.drawWindow(x, c, t, intro);
    x.globalAlpha = 1;
    comp.draw(renderer, U.upload(), out);
    return { zoom: 1 + 0.01 * Math.exp(-Math.max(0, t - this.tSend) / 0.08) * (t >= this.tSend ? 1 : 0) };
  }

  drawWindow(x: CanvasRenderingContext2D, c: Cam, t: number, intro: number) {
    const z = c.z;
    // the window: white, soft shadow, rising 24 px as it fades in
    setWorld(x, c, 0, (1 - intro) * 24);
    x.save();
    x.shadowColor = 'rgba(15,23,42,0.10)'; x.shadowBlur = 60 * z; x.shadowOffsetY = 18 * z;
    x.fillStyle = '#FFFFFF'; rr(x, WX, WY, WW, WH, WR); x.fill();
    x.restore();
    x.save();
    rr(x, WX, WY, WW, WH, WR); x.clip();
    // conversation background
    x.fillStyle = '#F5F8FC'; x.fillRect(WX, WY + HEAD, WW, CY - 50 - (WY + HEAD));
    this.drawHeader(x, t);
    this.drawComposer(x, t);
    this.drawBubble(x, t);
    this.drawCard(x, c, t);
    x.restore();
    x.setTransform(1, 0, 0, 1, 0, 0);
  }

  drawHeader(x: CanvasRenderingContext2D, t: number) {
    // hairline under the header
    x.fillStyle = '#E2E8F0'; x.fillRect(WX, WY + HEAD - 1, WW, 1);
    // the orb avatar, with a cyan arc rolling round it while Mirsal AI works
    const ox = WX + 66, oy = WY + HEAD / 2;
    const working = prog(t, this.tSend, this.tSend + 0.2) * (1 - prog(t, this.tChat, this.tChat + 0.3));
    drawOrb(x, ox, oy, 25);
    if (working > 0.01) {
      x.save();
      x.strokeStyle = rgba('ember', 0.9 * working); x.lineWidth = 3; x.lineCap = 'round';
      x.shadowColor = rgba('ember', 0.6 * working); x.shadowBlur = 10;
      const a = t * 5.5;
      x.beginPath(); x.arc(ox, oy, 32, a, a + 1.6); x.stroke();
      x.restore();
    }
    x.font = font(F.inter(600), 26); x.fillStyle = rgba('ink', 1);
    x.fillText('Mirsal AI', ox + 46, oy - 3);
    // verified tick
    const tw = measure('Mirsal AI', F.inter(600), 26);
    x.fillStyle = rgba('signal', 1); x.beginPath(); x.arc(ox + 46 + tw + 16, oy - 12, 10, 0, TAU); x.fill();
    x.strokeStyle = '#fff'; x.lineWidth = 2.4; x.lineCap = 'round'; x.lineJoin = 'round';
    x.beginPath(); x.moveTo(ox + 46 + tw + 11, oy - 12); x.lineTo(ox + 46 + tw + 15, oy - 8); x.lineTo(ox + 46 + tw + 21, oy - 16); x.stroke();
    // status: online / creating your pack… / online
    x.font = font(F.inter(400), 19);
    if (working > 0.5) {
      x.fillStyle = rgba('signal', 1);
      x.fillText('creating your pack', ox + 46, oy + 24);
      const dw = measure('creating your pack', F.inter(400), 19);
      for (let i = 0; i < 3; i++) {
        const k = 0.35 + 0.65 * Math.max(0, Math.sin(t * 9 - i * 0.9));
        x.fillStyle = rgba('signal', k); x.beginPath(); x.arc(ox + 46 + dw + 9 + i * 9, oy + 18, 2.6, 0, TAU); x.fill();
      }
    } else {
      x.fillStyle = rgba('graphite', 1);
      x.fillText('online', ox + 46, oy + 24);
    }
  }

  drawComposer(x: CanvasRenderingContext2D, t: number) {
    // white bar with the pill
    x.fillStyle = '#FFFFFF'; x.fillRect(WX, CY - 50, WW, WY + WH - (CY - 50));
    x.fillStyle = '#E2E8F0'; x.fillRect(WX, CY - 50, WW, 1);
    x.fillStyle = '#F1F5F9'; rr(x, PX0, CY - PH / 2, PX1 - PX0, PH, PH / 2); x.fill();
    // the cyan light rolling round the pill while Mirsal AI works (a dash travelling along the stroke)
    const working = prog(t, this.tSend, this.tSend + 0.15) * (1 - prog(t, this.tCard + 0.3, this.tCard + 0.7));
    if (working > 0.01) {
      const per = 2 * (PX1 - PX0 - PH) + Math.PI * PH;
      x.save();
      x.strokeStyle = rgba('ember', working); x.lineWidth = 3; x.lineCap = 'round';
      x.shadowColor = rgba('ember', 0.7 * working); x.shadowBlur = 14;
      x.setLineDash([per * 0.16, per * 0.84]); x.lineDashOffset = -(t - this.tSend) * per * 0.9;
      rr(x, PX0, CY - PH / 2, PX1 - PX0, PH, PH / 2); x.stroke();
      x.restore();
    }
    // the text being typed (cleared on send), with a blue caret
    const sent = t >= this.tSend;
    const tx = PX0 + 30, fam = F.inter(400);
    x.font = font(fam, 26);
    if (!sent) {
      const s = this.msg.slice(0, this.typed(t));
      const inner = PX1 - PX0 - 60, sw = s ? measure(s, fam, 26) : 0;
      const off = Math.max(0, sw - inner); // like a real text field: the start scrolls out to the left
      x.save();
      rr(x, PX0 + 14, CY - PH / 2, PX1 - PX0 - 28, PH, 0); x.clip();
      if (s) { x.fillStyle = rgba('ink', 1); x.fillText(s, tx - off, CY + 9); }
      else { x.fillStyle = rgba('graphite', 0.8); x.fillText('Message', tx, CY + 9); }
      const typing = t > this.msgWords[0]!.start - 0.05 && t < this.msgWords[this.msgWords.length - 1]!.end;
      const blink = typing || Math.sin(t * TAU * 1.6) > -0.2;
      if (blink) { x.fillStyle = rgba('signal', 1); x.fillRect(tx + sw - off + 2, CY - 16, 2.5, 32); }
      x.restore();
    } else {
      x.fillStyle = rgba('graphite', 0.8 * prog(t, this.tSend + 0.15, this.tSend + 0.4)); x.fillText('Message', tx, CY + 9);
    }
    // the send button: grey until there is text, blue after; pressed on send
    const has = sent ? 1 - prog(t, this.tSend + 0.05, this.tSend + 0.3) : prog(t, this.msgWords[0]!.start, this.msgWords[0]!.start + 0.15);
    const press = t < this.tSend ? 1 : 1 - 0.16 * Math.sin(clamp((t - this.tSend) / 0.22) * Math.PI);
    x.save();
    x.translate(SEND.x, SEND.y); x.scale(press, press);
    x.fillStyle = has > 0.5 ? rgba('signal', 1) : '#CBD5E1';
    x.beginPath(); x.arc(0, 0, SEND.r, 0, TAU); x.fill();
    x.strokeStyle = '#fff'; x.lineWidth = 3.6; x.lineCap = 'round'; x.lineJoin = 'round';
    x.beginPath(); x.moveTo(0, 11); x.lineTo(0, -11); x.moveTo(-9, -2); x.lineTo(0, -11); x.lineTo(9, -2); x.stroke();
    x.restore();
  }

  /** The outgoing bubble: flies up from the composer on send, then sits top right. */
  drawBubble(x: CanvasRenderingContext2D, t: number) {
    if (t < this.tSend) return;
    const k = clamp((t - this.tSend) / 0.55);
    const fam = F.inter(500);
    const w = Math.min(BUB_MAXW, Math.max(...this.bubbleLines.map((l) => measure(l, fam, BUB_FS))) + 44);
    const h = this.bubbleLines.length * BUB_LH + 30;
    const x1 = WX + WW - 40, y0 = WY + HEAD + 34;
    const fy = lerp(CY - h / 2, y0, ease.outCubic(k));
    const fx = lerp(PX0 + w * 0.5, x1 - w, ease.outCubic(k));
    const s = lerp(0.82, 1, ease.outBack(k));
    x.save();
    x.translate(fx + w, fy + h); x.scale(s, s); x.translate(-w, -h);
    x.shadowColor = 'rgba(37,99,235,0.18)'; x.shadowBlur = 18; x.shadowOffsetY = 6;
    x.fillStyle = rgba('signal', 1); rr(x, 0, 0, w, h, 24); x.fill();
    x.shadowColor = 'transparent';
    x.font = font(fam, BUB_FS); x.fillStyle = '#FFFFFF';
    this.bubbleLines.forEach((l, i) => x.fillText(l, 22, 15 + BUB_LH * (i + 1) - 9));
    x.restore();
    // time and read ticks, once the chat is in frame
    const a = prog(t, this.tSend + 0.5, this.tSend + 0.8);
    if (a > 0) {
      x.font = font(F.inter(400), 16); x.fillStyle = rgba('graphite', a); x.textAlign = 'right';
      x.fillText('9:41', x1 - 30, y0 + h + 24);
      this.ticks(x, x1 - 6, y0 + h + 18, rgba('signal', a));
      x.textAlign = 'left';
    }
  }

  ticks(x: CanvasRenderingContext2D, cx: number, cy: number, col: string) {
    x.strokeStyle = col; x.lineWidth = 2; x.lineCap = 'round'; x.lineJoin = 'round';
    for (const d of [-5, 0]) { x.beginPath(); x.moveTo(cx - 7 + d, cy); x.lineTo(cx - 3 + d, cy + 4); x.lineTo(cx + 5 + d, cy - 5); x.stroke(); }
  }

  /** The incoming sticker card: arrives on "already", stickers pop in one by one and start moving on "moving". */
  drawCard(x: CanvasRenderingContext2D, c: Cam, t: number) {
    if (t < this.tCard) return;
    const k = clamp((t - this.tCard) / 0.45);
    const s = lerp(0.92, 1, ease.outBack(k)), a = ease.outCubic(k);
    x.save();
    x.globalAlpha *= a;
    x.translate(CARD.x, CARD.y + (1 - ease.outCubic(k)) * 30);
    x.scale(s, s);
    x.shadowColor = 'rgba(15,23,42,0.08)'; x.shadowBlur = 30 * c.z; x.shadowOffsetY = 8 * c.z;
    x.fillStyle = '#FFFFFF'; rr(x, 0, 0, CARD.w, CARD.h, 28); x.fill();
    x.shadowColor = 'transparent';
    const live = ease.inOutCubic(prog(t, this.tMove - 0.05, this.tMove + 0.35));
    for (let i = 0; i < 9; i++) {
      const col = i % 3, row = Math.floor(i / 3);
      const cx = PAD + col * (TILE + GAP) + TILE / 2, cy = PAD + row * (TILE + GAP) + TILE / 2;
      const t0 = this.tCard + 0.12 + i * 0.055;
      const pop = ease.outBack(clamp((t - t0) / 0.32), 2.2);
      if (pop <= 0) continue;
      x.fillStyle = '#F1F5F9'; rr(x, cx - TILE / 2, cy - TILE / 2, TILE, TILE, 22); x.fill();
      // each sticker's own loop, ramping in on "moving"
      const ph = i * 1.37, fq = 1.5 + (i % 4) * 0.22, w = TAU * fq * (t - this.tMove) + ph;
      let dy = 0, rot = 0, sx = 1, sy = 1;
      switch (i % 4) {
        case 0: dy = -9 * Math.abs(Math.sin(w * 0.5)); break; // hop
        case 1: rot = 0.14 * Math.sin(w); break; // tilt
        case 2: sx = 1 + 0.06 * Math.sin(w); sy = 1 - 0.06 * Math.sin(w); break; // squash
        case 3: rot = 0.08 * Math.sin(w * 1.6); dy = -4 * Math.sin(w * 0.8); break; // wiggle
      }
      x.save();
      x.translate(cx, cy + dy * live);
      x.rotate(rot * live);
      x.scale(pop * lerp(1, sx, live), pop * lerp(1, sy, live));
      const im = this.img[i]!;
      x.drawImage(im, -TILE * 0.46, -TILE * 0.46, TILE * 0.92, TILE * 0.92);
      x.restore();
    }
    // caption
    const ca = prog(t, this.tCard + 0.4, this.tCard + 0.7);
    const yb = PAD + TILE * 3 + GAP * 2 + 34;
    x.globalAlpha *= ca;
    x.font = font(F.inter(600), 20); x.fillStyle = rgba('ink', 1);
    x.fillText('Superhero Dubai', PAD, yb);
    x.font = font(F.inter(400), 18); x.fillStyle = rgba('graphite', 1); x.textAlign = 'right';
    x.fillText('9 stickers · animated', CARD.w - PAD, yb);
    x.textAlign = 'left';
    x.restore();
  }
}
