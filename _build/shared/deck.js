/* UFLI interactive deck player (v2: Details toggle, hint, auditory-drill helper) */
(function(){
  const slides = Array.from(document.querySelectorAll('.slide'));
  const vp = document.getElementById('viewport');
  const hud = document.getElementById('hud');
  const panel = document.getElementById('panel');
  const menu = document.getElementById('menu');
  const pop = document.getElementById('pop');
  const help = document.getElementById('help');
  const count = document.getElementById('count');
  const stepLbl = document.getElementById('steplbl');
  const bar = document.getElementById('bar');
  const detailsBtn = document.getElementById('details');
  const hint = document.getElementById('hint');
  const meta = window.DECK_META || {};
  const GR = window.GRAPHEMES || {};
  const PLAN = window.LESSON_PLAN || null;
  let cur = 0, k = 0;            // slide index, animation step within slide
  let grPopShown = false;        // Details mode: example popup already shown on this grapheme slide
  let details = false;
  try{ details = localStorage.getItem('ufli.details') === '1'; }catch(e){}
  const stepsOf = s => parseInt(s.dataset.steps || '0', 10);

  function fit(){
    const w = window.innerWidth, h = window.innerHeight - 40;
    const sc = Math.min(w/1000, h/750);
    vp.style.transform = 'scale(' + sc + ')';
    vp.style.marginBottom = '40px';
  }
  window.addEventListener('resize', fit); fit();
  function setDetails(on){
    details = on; detailsBtn.classList.toggle('on', on);
    detailsBtn.querySelector('.lbl').textContent = on ? 'Details ON' : 'Details OFF';
    try{ localStorage.setItem('ufli.details', on ? '1' : '0'); }catch(e){}
  }
  detailsBtn.addEventListener('click', () => setDetails(!details));
  setDetails(details);

  function applyState(s, k){
    s.querySelectorAll('[data-anim]').forEach(el => {
      const acts = el.dataset.anim.split(',').map(a => a.split(':'));
      let vis = !acts.some(a => a[0] === 'e');
      acts.sort((a,b) => (+a[1]) - (+b[1]));
      for (const a of acts){ if (+a[1] <= k){ vis = (a[0] === 'e'); } }
      el.classList.toggle('hid', !vis);
    });
  }
  function show(i, stepK){
    i = Math.max(0, Math.min(slides.length-1, i));
    slides[cur].classList.remove('active');
    cur = i; k = stepK == null ? 0 : stepK; grPopShown = false;
    pop.classList.remove('open'); hint.classList.remove('show');
    const s = slides[cur];
    s.classList.add('active');
    applyState(s, k);
    s.querySelectorAll('img').forEach(im => { const a = im.getAttribute('src') || ''; if (/\.gif($|\?)/i.test(a)){ im.src = a.split('?')[0] + '?t=' + Date.now(); } });
    count.textContent = (cur+1) + ' / ' + slides.length;
    stepLbl.textContent = s.dataset.label || '';
    bar.style.width = (100*(cur+1)/slides.length) + '%';
    updatePanel();
    try{ localStorage.setItem('ufli.pos.' + meta.id, String(cur)); }catch(e){}
    stopAudio();
  }
  // ---------- auditory-drill helper stepping ----------
  function adGroups(h){ return [...h.querySelectorAll('.sgroup')]; }
  function adStack(h){ if (!h._stack) h._stack = []; return h._stack; }
  function adActivate(h, i){
    const gs = adGroups(h); const snds = [...h.querySelectorAll('.snd')];
    gs.forEach((g, j) => g.classList.toggle('on', j === i));
    snds.forEach((s, j) => { s.classList.toggle('cur', j === i); s.classList.toggle('done', j < i); });
  }
  function adNext(h){
    const gs = adGroups(h); if (!gs.length) return false;
    const st = adStack(h);
    let ci = gs.findIndex(g => g.classList.contains('on'));
    if (ci < 0){ adActivate(h, 0); st.push({t:'group', i:0}); if (!details) gs[0].querySelectorAll('.gch').forEach(e => e.classList.add('rev')); return true; }
    const g = gs[ci];
    if (details){
      for (const row of g.querySelectorAll('.grow')){
        const c = row.querySelector('.gch'), x = row.querySelector('.gex');
        if (c && !c.classList.contains('rev')){ c.classList.add('rev'); st.push({t:'el', el:c}); return true; }
        if (x && !x.classList.contains('rev')){ x.classList.add('rev'); st.push({t:'el', el:x}); return true; }
      }
    }
    if (ci + 1 < gs.length){
      adActivate(h, ci+1); st.push({t:'group', i:ci+1});
      if (!details) gs[ci+1].querySelectorAll('.gch').forEach(e => e.classList.add('rev'));
      return true;
    }
    return false; // finished: let the caller advance the slide
  }
  function adPrev(h){
    const st = adStack(h); if (!st.length) return false;
    const a = st.pop();
    if (a.t === 'el'){ a.el.classList.remove('rev'); return true; }
    const gs = adGroups(h);
    gs[a.i].classList.remove('on'); gs[a.i].querySelectorAll('.rev').forEach(e => e.classList.remove('rev'));
    if (a.i > 0) adActivate(h, a.i-1); else { h.querySelectorAll('.snd').forEach(s => s.classList.remove('cur','done')); }
    return true;
  }
  function adReset(h){ h._stack = []; h.querySelectorAll('.on,.rev').forEach(e => e.classList.remove('on','rev')); h.querySelectorAll('.snd').forEach(s => s.classList.remove('cur','done')); }
  function adAll(h){ const gs = adGroups(h); let ci = gs.findIndex(g => g.classList.contains('on')); if (ci < 0){ adActivate(h, 0); ci = 0; adStack(h).push({t:'group', i:0}); } gs[ci].querySelectorAll('.gch,.gex').forEach(e => { if (!e.classList.contains('rev')){ e.classList.add('rev'); adStack(h).push({t:'el', el:e}); } }); }

  function next(){
    const s = slides[cur];
    const h = s.querySelector('.helper');
    if (h && h.classList.contains('ad')){ if (adNext(h)) return; }
    else if (h){ const nxt = h.querySelector('.item.q:not(.rev), .sent:not(.rev), .chain .w:not(.rev)'); if (nxt){ nxt.click(); return; } }
    const gr = s.querySelector('.gr');
    if (details && gr && !grPopShown){ openGrapheme(gr); grPopShown = true; return; }
    if (pop.classList.contains('open')){ pop.classList.remove('open'); if (gr){ if (cur < slides.length-1) show(cur+1, 0); return; } }
    if (k < stepsOf(s)){ k++; applyState(s, k); return; }
    if (cur < slides.length-1) show(cur+1, 0);
  }
  function prev(){
    const s = slides[cur];
    const h = s.querySelector('.helper');
    if (h && h.classList.contains('ad')){ if (adPrev(h)) return; }
    else if (h){ const revs = [...h.querySelectorAll('.item.q.rev, .sent.rev, .chain .w.rev')]; if (revs.length){ const last = revs[revs.length-1]; last.classList.remove('rev'); if (last.classList.contains('w')){ last.classList.remove('cur'); const big = h.querySelector('.big'); const rest = [...h.querySelectorAll('.chain .w.rev')]; if (big) big.innerHTML = rest.length ? rest[rest.length-1].innerHTML : ''; if (rest.length) rest[rest.length-1].classList.add('cur'); } return; } }
    if (s.querySelector('.gr')){ pop.classList.remove('open'); if (cur > 0) show(cur-1, 0); return; }   // grapheme slides: go straight back, popup closed
    if (k > 0){ k--; applyState(s, k); return; }
    if (cur > 0) show(cur-1, stepsOf(slides[cur-1]));
  }
  function updatePanel(){
    const s = slides[cur];
    const n = s.querySelector('.notes');
    let html = '<h3>Slide notes · 슬라이드 노트</h3><div class="notes">' + (n ? n.innerHTML : '<span class="muted">(no notes)</span>') + '</div>';
    const st = s.dataset.step;
    if (PLAN && st && PLAN.steps && PLAN.steps[st]) html += '<h3>Lesson plan · ' + (PLAN.steps[st].title || st) + '</h3><div class="plan">' + PLAN.steps[st].html + '</div>';
    if (PLAN && PLAN.notesHtml) html += '<h3 style="margin-top:18px">Instructional notes</h3><div class="plan">' + PLAN.notesHtml + '</div>';
    panel.innerHTML = html;
  }
  // ---------- speech ----------
  const TTS_CFG = window.TTS_CONFIG || { url: 'https://sbatsnivlrlywpfytlio.supabase.co', anon: 'sb_publishable_vwZUKHhhtBEjAgXrZQTNFQ_bQeM8Ypc', voice: 'en-AU-Neural2-A', rate: 0.9 };
  const audioCache = new Map();
  let cloudOK = true;
  const audioEl = new Audio(); audioEl.preload = 'auto';
  let voice = null;
  function pickVoice(){
    const vs = speechSynthesis.getVoices();
    for (const lang of ['en-NZ','en-AU','en-GB','en-US']){
      const v = vs.find(v => /karen|catherine|hayley|moira|fiona|kate|serena|samantha/i.test(v.name) && (v.lang||'').replace('_','-').startsWith(lang)) || vs.find(v => (v.lang||'').replace('_','-').startsWith(lang));
      if (v){ voice = v; break; }
    }
  }
  pickVoice(); speechSynthesis.onvoiceschanged = pickVoice;
  function stopAudio(){ try{ audioEl.pause(); }catch(e){} speechSynthesis.cancel(); document.querySelectorAll('.speaking').forEach(x => x.classList.remove('speaking')); }
  function localSpeak(text, el){
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    if (voice) u.voice = voice;
    u.rate = text.split(/\s+/).length > 3 ? 0.9 : 0.8;
    if (el){ u.onend = u.onerror = () => el.classList.remove('speaking'); }
    speechSynthesis.speak(u);
  }
  async function cloudUrl(text){
    const key = TTS_CFG.voice + '|' + TTS_CFG.rate + '|' + text;
    if (audioCache.has(key)) return audioCache.get(key);
    const r = await fetch(TTS_CFG.url.replace(/\/+$/,'') + '/functions/v1/tts', { method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + TTS_CFG.anon, 'apikey': TTS_CFG.anon },
      body: JSON.stringify({ text, voice: TTS_CFG.voice, rate: TTS_CFG.rate }) });
    if (!r.ok) throw new Error('tts ' + r.status);
    const blob = await r.blob();
    if (!blob.size || !/audio|octet/.test(blob.type)) throw new Error('tts bad blob ' + blob.type);
    const url = URL.createObjectURL(blob); audioCache.set(key, url); return url;
  }
  let speakSeq = 0;
  async function speak(text, el){
    if (!text) return;
    text = text.replace(/[“”„‟"‘’‚‛]/g, '').replace(/\s+/g,' ').trim();
    const my = ++speakSeq;
    stopAudio();
    if (el) el.classList.add('speaking');
    if (cloudOK){
      try{
        const url = await cloudUrl(text);
        if (my !== speakSeq) return;
        audioEl.src = url; audioEl.onended = audioEl.onerror = () => { if (el) el.classList.remove('speaking'); };
        await audioEl.play(); return;
      }catch(err){ console.warn('Cloud TTS unavailable, using local voice:', err.message); cloudOK = false; }
    }
    if (my !== speakSeq) return;
    localSpeak(text, el);
  }
  window.uflSpeak = speak;
  // ---------- popups ----------
  function esc(t){ return String(t).replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c])); }
  function toks(ph){ return String(ph).replace(/\(.*?\)/g,'').split(/\s+/).map(x => x.replace(/\//g,'').toLowerCase()).filter(Boolean); }
  function matches(a, b){ const ta = toks(a), tb = toks(b); return ta.some(x => tb.includes(x)); }
  function mark(word, g){
    const core = g.replace(/^-|-$/g,'').replace(/_e$/,'').replace(/^_/,'');
    const i = word.toLowerCase().indexOf(core.toLowerCase());
    if (i < 0 || !core) return esc(word);
    return esc(word.slice(0,i)) + '<mark>' + esc(word.slice(i,i+core.length)) + '</mark>' + esc(word.slice(i+core.length));
  }
  function openGrapheme(elOrName){
    const g = typeof elOrName === 'string' ? elOrName : elOrName.dataset.grapheme;
    let want = []; try{ if (typeof elOrName !== 'string') want = JSON.parse(elOrName.dataset.sounds || '[]'); }catch(e){}
    const info = GR[g] || GR[g.toLowerCase()] || GR[g.replace(/^-/,'')];
    let html = '<button class="x" onclick="document.getElementById(\'pop\').classList.remove(\'open\')">×</button><div class="g">' + esc(g) + '</div>';
    if (!info){ html += '<div class="tip">No example data for this grapheme yet.</div>'; }
    else {
      let list = info.sounds;
      if (want.length){ const f = list.filter(s => want.some(w => matches(w, s.ph))); if (f.length) list = f; }
      for (const s of list) html += '<div class="snd"><div class="ph">' + esc(s.ph) + '</div><div class="ex">' + s.ex.slice(0,3).map(w => '<span onclick="uflSpeak(\'' + w.replace(/'/g,"\\'") + '\',this)">' + mark(w, g) + '</span>').join('') + '</div></div>';
      if (info.tip) html += '<div class="tip">' + info.tip + '</div>';
    }
    pop.querySelector('.card').innerHTML = html; pop.classList.add('open');
  }
  function openWhy(text, word){
    pop.querySelector('.card').innerHTML = '<button class="x" onclick="document.getElementById(\'pop\').classList.remove(\'open\')">×</button><div class="g" style="font-size:72px">' + esc(word||'') + '</div><div class="why">' + esc(text) + '</div>';
    pop.classList.add('open');
  }
  window.uflOpenGrapheme = openGrapheme; window.uflOpenWhy = openWhy;
  let hintTimer;
  function showHint(){
    const gr = slides[cur].querySelector('.gr'); if (!gr) return;
    let n = parseInt(gr.dataset.nsounds || '0', 10);
    if (!n){ const info = GR[gr.dataset.grapheme]; n = info ? info.sounds.length : 1; }
    hint.textContent = n + (n === 1 ? ' sound' : ' sounds');
    hint.classList.add('show'); clearTimeout(hintTimer); hintTimer = setTimeout(() => hint.classList.remove('show'), 3000);
  }
  pop.addEventListener('click', e => { if (e.target === pop) pop.classList.remove('open'); });
  help.addEventListener('click', e => { if (e.target === help) help.classList.remove('open'); });
  // ---------- clicks ----------
  document.addEventListener('click', e => {
    const t = e.target;
    if (t.closest('#hud') || t.closest('#panel') || t.closest('#menu') || t.closest('#pop') || t.closest('#help') || t.closest('#details')) return;
    const spk = t.closest('.spk');
    if (spk){ speak(spk.dataset.say || spk.textContent, spk); e.stopPropagation(); return; }
    const gex = t.closest('.gex span');
    if (gex){ speak(gex.textContent, gex); e.stopPropagation(); return; }
    const gr = t.closest('.gr');
    if (gr){ openGrapheme(gr); grPopShown = true; e.stopPropagation(); return; }
    const q = t.closest('.qbtn');
    if (q){ openWhy(q.dataset.why, q.dataset.word); e.stopPropagation(); return; }
    const sb = t.closest('.spkbtn');
    if (sb){ speak(sb.dataset.say, sb); e.stopPropagation(); return; }
    const hi = t.closest('.helper .item.q, .helper .sent, .helper .chain .w');
    if (hi){ hi.classList.toggle('rev'); if (hi.classList.contains('w')) { hi.parentElement.querySelectorAll('.w').forEach(x=>x.classList.remove('cur')); hi.classList.add('rev'); hi.classList.add('cur'); const big = hi.closest('.helper').querySelector('.big'); if (big) big.innerHTML = hi.innerHTML; } e.stopPropagation(); return; }
    if (t.closest('.helper.ad')){ next(); e.stopPropagation(); return; }
    if (t.closest('#viewport')){ if (e.clientX < window.innerWidth*0.15) prev(); else next(); }
  });
  // ---------- keys ----------
  document.addEventListener('keydown', e => {
    if (e.target.tagName === 'INPUT') return;
    const key = e.key;
    if (help.classList.contains('open')){ help.classList.remove('open'); return; }
    if (pop.classList.contains('open') && key === 'Escape'){ pop.classList.remove('open'); return; }
    switch(key){
      case 'ArrowRight': case ' ': case 'PageDown': case 'Enter': next(); e.preventDefault(); break;
      case 'ArrowLeft': case 'PageUp': case 'Backspace': prev(); e.preventDefault(); break;
      case 'ArrowDown': if (cur < slides.length-1) show(cur+1, 0); e.preventDefault(); break;
      case 'ArrowUp': if (cur > 0) show(cur-1, 0); e.preventDefault(); break;
      case 'Home': show(0,0); break;
      case 'End': show(slides.length-1, 0); break;
      case 'f': case 'F': toggleFull(); break;
      case 'n': case 'N': panel.classList.toggle('open'); break;
      case 'm': case 'M': menu.classList.toggle('open'); break;
      case 'd': case 'D': setDetails(!details); break;
      case 'h': case 'H': showHint(); break;
      case 's': case 'S': { const s = slides[cur]; const el = s.querySelector('.spk, .spkbtn'); if (el) speak(el.dataset.say || el.textContent, el); break; }
      case 'e': case 'E': { const g = slides[cur].querySelector('.gr'); if (g){ openGrapheme(g); grPopShown = true; } break; }
      case 'r': case 'R': { const s = slides[cur]; const h = s.querySelector('.helper.ad'); if (h) adReset(h); s.querySelectorAll('.rev').forEach(x => x.classList.remove('rev')); s.querySelectorAll('.cur').forEach(x=>x.classList.remove('cur')); const big=s.querySelector('.big'); if (big) big.innerHTML=''; k = 0; grPopShown = false; pop.classList.remove('open'); applyState(s, 0); break; }
      case 'a': case 'A': { const s = slides[cur]; const h = s.querySelector('.helper.ad'); if (h) adAll(h); s.querySelectorAll('.helper .item.q, .helper .sent, .helper .chain .w').forEach(x => x.classList.add('rev')); k = stepsOf(s); applyState(s, k); break; }
      case 'Escape': panel.classList.remove('open'); menu.classList.remove('open'); pop.classList.remove('open'); break;
      case '?': help.classList.toggle('open'); break;
      case 'g': case 'G': { const n = parseInt(prompt('Go to slide (1-' + slides.length + ')'), 10); if (n) show(n-1, 0); break; }
    }
  });
  function toggleFull(){ if (!document.fullscreenElement) document.documentElement.requestFullscreen && document.documentElement.requestFullscreen(); else document.exitFullscreen(); }
  document.getElementById('btnFull').onclick = toggleFull;
  document.getElementById('btnNotes').onclick = () => panel.classList.toggle('open');
  document.getElementById('btnMenu').onclick = () => menu.classList.toggle('open');
  document.getElementById('btnPrev').onclick = prev;
  document.getElementById('btnNext').onclick = next;
  document.getElementById('btnHelp').onclick = () => help.classList.toggle('open');
  menu.querySelectorAll('a[data-go]').forEach(a => a.addEventListener('click', e => { e.preventDefault(); show(parseInt(a.dataset.go,10), 0); menu.classList.remove('open'); }));
  let tmr; function wake(){ hud.classList.remove('fade'); clearTimeout(tmr); tmr = setTimeout(() => hud.classList.add('fade'), 3500); }
  document.addEventListener('mousemove', wake); wake();
  let start = 0;
  const hash = parseInt((location.hash||'').replace('#',''), 10);
  if (hash) start = hash-1;
  else { try{ const p = parseInt(localStorage.getItem('ufli.pos.' + meta.id), 10); if (p && p < slides.length && confirm('이전에 보던 슬라이드 ' + (p+1) + '번부터 이어서 볼까요?\nContinue from slide ' + (p+1) + '?')) start = p; }catch(e){} }
  show(start, 0);
})();
