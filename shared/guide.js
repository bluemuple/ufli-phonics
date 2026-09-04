(function(){
  const GR = window.GRAPHEMES || {};
  const pop = document.getElementById('pop');
  function esc(t){ return String(t).replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c])); }
  function norm(ph){ return ph.replace(/\s*\(.*?\)\s*/g,'').replace(/[\/\s]/g,'').toLowerCase(); }
  function toks(ph){ return ph.replace(/\(.*?\)/g,'').split(/\s+/).map(x => x.replace(/\//g,'').toLowerCase()).filter(Boolean); }
  function matches(a, b){ const ta = toks(a), tb = toks(b); return ta.some(x => tb.includes(x)); }
  function mark(word, g){
    const core = g.replace(/^-|-$/g,'').replace(/_e$/,'').replace(/^_/,'');
    const i = word.toLowerCase().indexOf(core.toLowerCase());
    if (i < 0 || !core) return esc(word);
    return esc(word.slice(0,i)) + '<mark>' + esc(word.slice(i, i+core.length)) + '</mark>' + esc(word.slice(i+core.length));
  }
  function speak(text, el){
    try{ speechSynthesis.cancel(); const u = new SpeechSynthesisUtterance(text); const vs = speechSynthesis.getVoices();
      u.voice = vs.find(v => /en-(NZ|AU)/i.test(v.lang)) || vs.find(v => /en-GB/i.test(v.lang)) || null; u.rate = 0.8; speechSynthesis.speak(u); }catch(e){}
  }
  window.gSpeak = speak;
  function exSpans(words, g){ return words.map(w => '<span onclick="gSpeak(\'' + w.replace(/'/g,"\\'") + '\')">' + mark(w, g) + '</span>').join(''); }
  function openGrapheme(g, sounds){
    const info = GR[g] || GR[g.toLowerCase()] || GR[g.replace(/^-/,'')];
    let html = '<button class="x" onclick="document.getElementById(\'pop\').classList.remove(\'open\')">×</button><div class="g">' + esc(g) + '</div>';
    if (!info){ html += '<div class="tip">No example data for this grapheme yet.</div>'; }
    else {
      let list = info.sounds;
      if (sounds && sounds.length){ const f = list.filter(s => sounds.some(w => matches(w, s.ph))); if (f.length) list = f; }
      for (const s of list) html += '<div class="snd"><div class="ph">' + esc(s.ph) + '</div><div class="ex">' + exSpans(s.ex.slice(0,3), g) + '</div></div>';
      if (info.tip) html += '<div class="tip">' + info.tip + '</div>';
    }
    pop.querySelector('.card').innerHTML = html; pop.classList.add('open');
  }
  function openPhoneme(ph, spellings){
    let html = '<button class="x" onclick="document.getElementById(\'pop\').classList.remove(\'open\')">×</button><div class="g" style="color:#e05436">' + esc(ph) + '</div>';
    html += '<div class="tip" style="margin:0 0 8px">Say the sound; the student writes each spelling. Click a spelling\'s words to hear them.</div>';
    for (const sp of spellings){
      const info = GR[sp] || GR[sp.replace(/^-/,'')];
      let ex = [];
      if (info){ const m = info.sounds.find(s => matches(s.ph, ph)) || info.sounds.find(s => norm(s.ph).startsWith(norm(ph).slice(0,3))) || info.sounds[0]; ex = m ? m.ex.slice(0,2) : []; }
      html += '<div class="snd"><div class="ph" style="color:#2c629f">' + esc(sp) + '</div><div class="ex">' + exSpans(ex, sp) + '</div></div>';
    }
    pop.querySelector('.card').innerHTML = html; pop.classList.add('open');
  }
  document.addEventListener('click', e => {
    const c = e.target.closest('.chip');
    if (!c) return;
    if (c.dataset.g) openGrapheme(c.dataset.g, JSON.parse(c.dataset.sounds || '[]'));
    else if (c.dataset.ph) openPhoneme(c.dataset.ph, JSON.parse(c.dataset.sp || '[]'));
  });
  pop.addEventListener('click', e => { if (e.target === pop) pop.classList.remove('open'); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') pop.classList.remove('open'); });
})();
