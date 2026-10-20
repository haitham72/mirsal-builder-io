/* Super reaction sandbox (Reactions 2.0, Haitham 2026-10-20): #/super. Two resizable screens, a desktop window with its menus and an iPhone; hold the
   reaction in either one's emoji box and small copies stream up, release and the whole screen plays: the dropped Lottie rising from the bottom, the
   screen lit with its colour, the big pop in the middle. The animation is made for THAT screen's shape (POST /api/particles/super with its
   width / height: the engine picks the nearest bucket, the player crops the rest with xMidYMid slice), so resizing a frame changes what it gets.
   Sources: the files in mirsal/lottie, listed by name on every visit (GET /api/particles/super). Engine: engine/super_reaction.py. */
const SUP = {files: [], file: '', glow: 'auto', color: '#ff5a1f', c2: '#ffd23f', set: {}, start: {}, cache: {}, docs: {}, err: ''};
const SUP_SETS = [['count', 'Amount', 4, 160, 1], ['rise', 'Rise', 0.2, 1.4, 0.05], ['float', 'Float', 0, 0.8, 0.05], ['sway', 'Sway', 0, 1.5, 0.05],
  ['spread', 'Spread', 10, 120, 1], ['glow_strength', 'Glow', 0, 1, 0.05]];
let supLib = null;
const supLottie = () => supLib || (supLib = typeof lsLib !== 'undefined' && lsLib ? lsLib : new Promise((ok, no) => {
  if (window.lottie) return ok(window.lottie);
  const s = document.createElement('script'); s.src = '/ui/vendor/lottie-5.12.2.min.js'; s.onload = () => ok(window.lottie); s.onerror = no; document.head.appendChild(s);
}));
const supClone = d => JSON.parse(JSON.stringify(d));

/* what the server is asked for one screen: the source, the screen's shape, the glow, the moved sliders */
function supBody(aspect) {
  const b = {file: SUP.file, aspect, glow: SUP.glow, settings: {...SUP.set, pop: SUP.set.pop ?? 1}};
  if (SUP.glow === 'solid') b.color = SUP.color;
  if (SUP.glow === 'gradient') b.colors = [SUP.color, SUP.c2];
  return b;
}
/* the nearest bucket name for a shape, from the listing (the server decides; this only labels the frame) */
function supBucket(aspect) {
  let best = '', d = 1e9;
  for (const [k, v] of Object.entries(SUP.buckets || {})) { const e = Math.abs(Math.log(v / aspect)); if (e < d) { d = e; best = k } }
  return best;
}
async function supFetch(aspect) {
  const b = supBody(aspect), key = JSON.stringify({...b, aspect: supBucket(aspect)});
  if (!SUP.cache[key]) SUP.cache[key] = post('/api/particles/super', b).then(r => {
    if (!r.ok) { delete SUP.cache[key]; throw new Error(r.j.error || 'Could not make the super reaction') }
    return r.j;
  });
  return SUP.cache[key];
}
/* the source itself (the hold stream and the button): the dropped file, as is */
async function supDoc(file) {
  if (!SUP.docs[file]) SUP.docs[file] = api('/api/particles/reaction-handpicked/' + encodeURIComponent(file)).then(r => r.ok ? r.j : null);
  return SUP.docs[file];
}

/* the two screens follow the Mirsal app (ref/ref-only.jpg: the desktop app and the phone) and reuse the Chat screen's own pieces (.chat, .chh,
   .chm bubbles, the .chc "Type a message" bar): the reaction sits in the bar where the app has its quick action */
const SUP_CHATS = [['Mirsal', 'New in version 10.1.89', '7:22 AM'], ['Haitham (You)', 'Envato: 21 October', '7:22 AM'], ['Arif Hh', 'https://higgsfield.ai/me…', '7:19 AM'],
  ['Rashid Khalfan Hh', 'Video', '25/09'], ['Sameer Hh', 'python py file', '24/09'], ['Nasir Hh', 'Video', '28/08']];
function supConvo(phone) {
  return `<div class="chat${phone ? ' mobile' : ''} sup-chat">
    <div class=chh>${phone ? `<span class=sup-back>${ic('back')}</span>` : ''}<div class="cv chav">A</div><div style="flex:1"><b>Arif Hh</b><small>online</small></div>
     <span class=sup-ico>${ic('search')}</span></div>
    <div class=chm>
     <div class="cm cin"><div class=bub>Did you see the new stickers?<span class=tm>01:22 PM</span></div></div>
     <div class="cm cout"><div class=bub>Hold the reaction in the bar 👇<span class=tm>01:23 PM</span></div></div>
    </div>
    <div class=chc><span class=sup-ico>${ic('sticker')}</span><span class=sup-input>Type a message</span>
     <span class=sup-ico>${ic('emoji')}</span><button class=sup-react aria-label="Hold for a super reaction" title="Hold, then release"><span class=sup-icon></span></button></div>
   </div>`;
}
function supFrame(kind) {
  const phone = kind === 'phone';
  if (phone) return `<div class="sup-dev sup-phone" data-sup=phone>
   <div class=sup-screen>
    <div class=sup-status><b>1:47</b><span class=sup-notch></span><span class=sup-sig><i></i><i></i><i></i><i></i></span></div>
    ${supConvo(true)}
    <div class=sup-fx aria-hidden=true></div>
   </div>
   <div class=sup-size></div>
  </div>`;
  return `<div class="sup-dev sup-desktop" data-sup=desktop>
   <div class=sup-bar><span class="cv chav sup-logo">M</span><b>Mirsal</b><span class=sp></span><i>–</i><i>▢</i><i>✕</i></div>
   <div class=sup-screen>
    <nav class=sup-rail>${['chat', 'emoji', 'star', 'lib', 'help'].map((n, i) => `<span class="sup-ico${i === 0 ? ' on' : ''}">${ic(n)}</span>`).join('')}</nav>
    <aside class=sup-menu><div class=sup-mh><b>Chats</b><span class=sup-ico>${ic('edit')}</span></div>
     <div class=sup-search>${ic('search')}<span>Search or start new chat</span></div>
     ${SUP_CHATS.map(([n, m, t], i) => `<div class="sup-row${i === 2 ? ' on' : ''}"><span class="cv chav">${esc(n[0])}</span><span class=sup-rt><b>${esc(n)}</b><small>${esc(m)}</small></span><small class=sup-t>${esc(t)}</small></div>`).join('')}
    </aside>
    ${supConvo(false)}
    <div class=sup-fx aria-hidden=true></div>
   </div>
   <div class=sup-size></div>
  </div>`;
}

/* every host on the page: the #/super screen, or the Super Emojis tab of Reaction effects and Library > Reactions */
function supDraw() {
  document.querySelectorAll('.sup-root').forEach(supDrawIn);
}
function supDrawIn(el) {
  const opts = SUP.files.map(f => `<option value="${esc(f.file)}"${f.file === SUP.file ? ' selected' : ''}>${esc(f.name)}</option>`).join('');
  const glow = ['auto', 'solid', 'gradient', 'none'].map(g => `<button class="btn sm${SUP.glow === g ? ' pri' : ''}" data-supglow=${g}>${g[0].toUpperCase() + g.slice(1)}</button>`).join('');
  const sliders = SUP_SETS.map(([k, label, lo, hi, st]) => {
    const v = SUP.set[k] ?? SUP.start[k] ?? lo;
    return `<label class=sup-sl><span>${label} <em>${v}</em></span><input type=range min=${lo} max=${hi} step=${st} value="${v}" data-supset=${k}></label>`;
  }).join('');
  el.innerHTML = `<div class=sup-wrap>
   <div class=sup-head>${el.dataset.suptab ? '' : '<h1>Super reaction</h1>'}<span class=sup-mut>Hold the reaction in a screen, then release. Drag a screen's corner to resize it.</span></div>
   <div class=sup-tools>
    <label class=sup-src>Lottie <select id=sup-file>${opts || '<option value="">No files in mirsal/lottie</option>'}</select></label>
    <span class=sup-glow>Light ${glow}
     ${SUP.glow === 'solid' || SUP.glow === 'gradient' ? `<input type=color id=sup-c1 value="${SUP.color}" title="${SUP.glow === 'gradient' ? 'Bottom' : 'Colour'}">` : ''}
     ${SUP.glow === 'gradient' ? `<input type=color id=sup-c2 value="${SUP.c2}" title=Top>` : ''}
     <span class=sup-auto id=sup-auto></span></span>
    <button class="btn sm" data-supreset>Reset</button>
   </div>
   <div class=sup-sliders>${sliders}</div>
   ${SUP.err ? `<p class=sup-err>${esc(SUP.err)}</p>` : ''}
   <div class=sup-stage>${supFrame('desktop')}${supFrame('phone')}</div>
  </div>`;
  supIcons();
  el.querySelectorAll('.sup-dev').forEach(supWatch);
}

/* the emoji box's button shows the source itself, looping */
async function supIcons() {
  if (!SUP.file) return;
  const [L, doc] = await Promise.all([supLottie(), supDoc(SUP.file)]);
  document.querySelectorAll('.sup-root .sup-icon').forEach(box => {
    box.innerHTML = ''; if (!doc) return;
    L.loadAnimation({container: box, renderer: 'svg', loop: true, autoplay: true, animationData: supClone(doc)});
  });
}
/* the frame's size readout: px and the bucket it will get */
function supWatch(dev) {
  const scr = dev.querySelector('.sup-screen'), out = dev.querySelector('.sup-size');
  const show = () => { const w = scr.clientWidth, h = scr.clientHeight; if (w && h) out.textContent = `${w} × ${h} · ${supBucket(w / h)}` };
  show();
  if (window.ResizeObserver) new ResizeObserver(show).observe(scr);
}

/* hold: small copies of the source rise from the button, faster the longer it is held */
function supStream(btn) {
  const fx = btn.closest('.sup-screen').querySelector('.sup-fx'), t0 = performance.now();
  let alive = true, timer = 0;
  const spawn = async () => {
    if (!alive) return;
    const [L, doc] = await Promise.all([supLottie(), supDoc(SUP.file)]);
    if (!doc || !alive) return;
    const sr = fx.getBoundingClientRect(), br = btn.getBoundingClientRect(), d = document.createElement('div');
    const size = 26 + Math.random() * 18;
    d.className = 'sup-bit';
    d.style.cssText = `left:${br.left - sr.left + br.width / 2 - size / 2}px;top:${br.top - sr.top - size / 2}px;width:${size}px;height:${size}px;--dx:${(Math.random() - .5) * 90}px;--dy:${-(120 + Math.random() * Math.min(260, sr.height * .45))}px`;
    fx.appendChild(d);
    const a = L.loadAnimation({container: d, renderer: 'svg', loop: false, autoplay: true, animationData: supClone(doc)});
    setTimeout(() => { a.destroy(); d.remove() }, 1300);
    const held = performance.now() - t0;
    timer = setTimeout(spawn, Math.max(70, 220 - held / 8));
  };
  spawn();
  return () => { alive = false; clearTimeout(timer) };
}

/* release: the whole screen plays, made for this screen's shape */
async function supPlay(dev) {
  const scr = dev.querySelector('.sup-screen'), fx = scr.querySelector('.sup-fx');
  const aspect = scr.clientWidth / Math.max(1, scr.clientHeight);
  try {
    const [L, r] = await Promise.all([supLottie(), supFetch(aspect)]);
    const box = document.createElement('div');
    box.className = 'sup-full';
    fx.appendChild(box);
    const a = L.loadAnimation({container: box, renderer: 'svg', loop: false, autoplay: true, animationData: supClone(r.lottie),
      rendererSettings: {preserveAspectRatio: 'xMidYMid slice'}});
    a.addEventListener('complete', () => { a.destroy(); box.remove() });
    const auto = $('sup-auto');
    if (auto && r.color) auto.innerHTML = `<i style="background:${r.color}"></i>${SUP.glow === 'auto' ? 'auto ' : ''}${r.color}`;
  } catch (e) { toast(e.message || 'Could not play', 1) }
}

/* pointer handling on the emoji box buttons: a short tap is a bounce, a hold streams and releases the super reaction */
document.addEventListener('pointerdown', e => {
  const btn = e.target.closest && e.target.closest('.sup-root .sup-react');
  if (!btn || !SUP.file) return;
  e.preventDefault();
  const dev = btn.closest('.sup-dev'), scr = dev.querySelector('.sup-screen');
  supFetch(scr.clientWidth / Math.max(1, scr.clientHeight)).catch(() => 0);      // ready by the release
  btn.classList.add('held');
  const stop = supStream(btn), t0 = performance.now();
  btn.setPointerCapture && btn.setPointerCapture(e.pointerId);
  const end = ev => {
    btn.removeEventListener('pointerup', end); btn.removeEventListener('pointercancel', end);
    stop(); btn.classList.remove('held');
    const inside = ev.type === 'pointerup' && document.elementFromPoint(ev.clientX, ev.clientY) && btn.contains(document.elementFromPoint(ev.clientX, ev.clientY));
    if (inside && performance.now() - t0 >= 250) supPlay(dev);
  };
  btn.addEventListener('pointerup', end); btn.addEventListener('pointercancel', end);
});
document.addEventListener('contextmenu', e => { if (e.target.closest && e.target.closest('.sup-root .sup-react')) e.preventDefault() });
document.addEventListener('click', e => {
  const g = e.target.closest && e.target.closest('.sup-root [data-supglow]');
  if (g) { SUP.glow = g.dataset.supglow; return supDraw() }
  if (e.target.closest && e.target.closest('.sup-root [data-supreset]')) { SUP.set = {}; SUP.glow = 'auto'; return supDraw() }
});
document.addEventListener('input', e => {
  const t = e.target;
  if (t.dataset && t.dataset.supset) { SUP.set[t.dataset.supset] = +t.value; const em = t.parentElement.querySelector('em'); if (em) em.textContent = t.value }
  if (t.id === 'sup-c1') SUP.color = t.value;
  if (t.id === 'sup-c2') SUP.c2 = t.value;
});
document.addEventListener('change', e => { if (e.target.id === 'sup-file') { SUP.file = e.target.value; supDraw() } });

/* the folder is read on every visit: a file dropped in mirsal/lottie appears by its name */
async function supLoad() {
  const r = await api('/api/particles/super');
  if (!r.ok) { SUP.err = r.j.error || 'Could not list the Lottie files'; return }
  SUP.err = '';
  SUP.files = r.j.files || []; SUP.buckets = r.j.buckets || {}; SUP.start = r.j.start || {};
  if (!SUP.files.some(f => f.file === SUP.file)) SUP.file = (SUP.files[0] || {}).file || '';
}
/* a tab host (Reaction effects, Library > Reactions): drawn now from what is known, refreshed once the folder is read */
let supLoading = null;
function supMount() {
  supDraw();
  if (!supLoading) supLoading = supLoad().then(supDraw).finally(() => { supLoading = null });
}
const supTabHtml = () => '<div class=sup-root data-suptab=1></div>';

RENDER.super = async () => {
  const el = $('s-super');
  if (el && !el.querySelector('.sup-root')) el.innerHTML = '<div class=sup-root></div>';
  await supLoad();
  supDraw();
};
