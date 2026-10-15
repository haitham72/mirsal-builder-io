/* Shared preview presentation only. Controllers own units, requests and staged mutations. */
'use strict';
const TESTCARD = {
  open({id, apply, cancel, stageClass = '', stageExtra = '', controls = ''}) {
    let card = document.getElementById(id);
    if (card) return card;
    card = document.createElement('div'); card.id = id; card.className = 'test-card';
    card.setAttribute('role', 'dialog'); card.setAttribute('aria-label', 'Test preview');
    card.innerHTML = `<div class="egcimg bg-checker ${stageClass}"><img alt="Preview">${stageExtra}<span class=egbadge>test</span><span class=spin></span></div>${controls}<div class=egccap aria-live=polite></div><div class=egcbtn><button class="btn sm pri" data-act=${apply}>Apply</button><button class="btn sm" data-act=${cancel}>Cancel</button></div>`;
    document.body.appendChild(card); return card;
  },
  close(id) { const card = document.getElementById(id); if (card) card.remove(); },
  sync(card, {src, caption, busy = false, loading = false}) {
    const image = card.querySelector('img');
    if (src && image.getAttribute('src') !== src) image.src = src;
    card.querySelector('.spin').style.display = loading ? '' : 'none';
    card.querySelector('.egccap').textContent = caption;
    card.querySelectorAll('.egcbtn .btn').forEach(button => { button.disabled = busy; });
    card.setAttribute('aria-busy', String(busy || loading));
  },
  place(card, anchor, width = 320, reserve = 190) {
    const r = anchor ? anchor.getBoundingClientRect() : null, w = Math.min(width, innerWidth - 24);
    card.style.width = w + 'px';
    card.style.left = Math.max(12, Math.min(innerWidth - w - 12, r ? r.left : 12)) + 'px';
    // Controls wrap at 44px targets; the rendered height can exceed width + reserve.
    const h = Math.min(card.getBoundingClientRect().height || w + reserve, innerHeight - 24);
    card.style.top = Math.max(12, Math.min(innerHeight - h - 12, r ? r.bottom + 8 : 90)) + 'px';
  }
};
