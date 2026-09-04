#!/usr/bin/env python3
"""Render teacher's guide pages (manual-style) from assembled plans."""
import json, html, re, os, sys
S = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(S, 'plans'))
from gpc import SEQ
def esc(t): return html.escape(str(t), quote=True)
def chain_html(ch):
    if not ch: return ''
    parts = [p.strip() for p in re.split(r'\s*→\s*', ch)]
    out = []
    for p in parts:
        if p.endswith('*'): out.append(f'<i>{esc(p[:-1])}</i>')
        else: out.append(esc(p))
    return '<span class="chain">' + ' <span class="arr">→</span> '.join(out) + '</span>'
def words(ws): return ', '.join(esc(w) for w in ws)
def sec(num, title, inner, sub=None):
    return f'<div class="sec"><h2>{num}: {esc(title)}</h2>{"<div class=sub>"+esc(sub)+"</div>" if sub else ""}<div class="body">{inner}</div></div>'
def two(l_title, l_html, r_title, r_html):
    return f'<div class="two"><div><div class="sub">{esc(l_title)}</div>{l_html}</div><div><div class="sub">{esc(r_title)}</div>{r_html}</div></div>'
def vd_chips(vd):
    return ''.join(f'<span class="chip" data-g="{esc(g)}" data-sounds=\'{json.dumps(s, ensure_ascii=False)}\'><b>{esc(g)}</b> <span class="s">({esc(", ".join(s))})</span></span>' for g, s in vd)
def ad_chips(ad):
    return ''.join(f'<span class="chip" data-ph="{esc(ph)}" data-sp=\'{json.dumps(sp, ensure_ascii=False)}\'><b class="s">{esc(ph)}</b> ({esc(", ".join(sp))})</span>' for ph, sp in ad)
def irr_html(items):
    if not items: return '<p>n/a</p>'
    out = []
    for w in items:
        note = (w.get('notes') or '').split('\n')
        note = [n for n in note if n.strip() and not n.startswith('The white rectangle') and not re.match(r'^Lessons?\s', n)]
        title = esc(' '.join(note)[:220])
        star = '*' if any('Temporarily' in n for n in note) else ''
        out.append(f'<span class="chip" title="{title}"><b>{esc(w["word"])}</b>{star}</span>')
    return ''.join(out)
def para(s): return ''.join(f'<p>{esc(p)}</p>' for p in s) if isinstance(s, list) else f'<p>{esc(s)}</p>'
def render(plan, deck_href):
    if plan.get('gr'): return render_gr(plan, deck_href)
    L = plan
    lesson = L.get('lesson', ''); concept = L.get('concept', '')
    head = f'<div class="hdr"><span>UFLI Foundations <span class="tag">AUS · reconstructed guide</span></span><span><b>{esc(lesson)}</b> | <i>{esc(concept)}</i></span></div>'
    banner = f'<div class="banner"><span class="big">{esc(concept)}:</span> {esc(L.get("tag", ""))}</div>'
    # ---- left column ----
    left = []
    if L.get('notes'):
        left.append(f'<div class="sec"><h2>Instructional Notes</h2><div class="body notes">{"".join(f"<p>{esc(n)}</p>" for n in L["notes"])}</div></div>')
    pa = L.get('pa')
    if pa:
        left.append(sec('1', 'Phonemic Awareness', two('Blend', ''.join(f'<p>{esc(x)}</p>' for x in pa['blend']), 'Segment', ''.join(f'<p>{esc(x)}</p>' for x in pa['segment']))))
    if L.get('vd'):
        left.append('<div class="two">' +
            f'<div><div class="sec"><h2>2: Visual Drill</h2><div class="sub">Graphemes</div><div class="body">{vd_chips(L["vd"])}<p style="margin-top:6px;color:#666;font-size:11.5px">Click a grapheme for sounds and 2-3 easy example words.</p></div></div></div>' +
            f'<div><div class="sec"><h2>3: Auditory Drill</h2><div class="sub">Phonemes</div><div class="body">{ad_chips(L["ad"])}<p style="margin-top:6px;color:#666;font-size:11.5px">Click a sound for example words per spelling.</p></div></div></div></div>')
    bd = L.get('bd')
    if bd:
        grid = bd.get('grid') or {}
        gh = '<div class="grid">' + ''.join(f'<div><b>{k}</b>' + ''.join(f'<span class="tile">{esc(t)}</span>' for t in grid.get(k, []) if t) + '</div>' for k in ('initial','medial','final')) + '</div>'
        note = f'<p style="color:#666;font-size:12px;margin-top:4px">{esc(bd["note"])}</p>' if bd.get('note') else ''
        left.append(sec('4', 'Blending Drill', f'<p>{chain_html(bd["chain"])}</p>{gh}{note}<p style="color:#666;font-size:11.5px;margin-top:5px">Use word chains from previous lessons to review blending with previously taught concepts. Provide ample practice with a variety of vowel patterns.</p>'))
    elif pa:
        left.append(sec('4', 'Blending Drill', '<p>Not yet used in this lesson (begins in Lesson 5).</p>'))
    nc = ''
    if L.get('intro'):
        nc += '<div class="sub">Introduction</div><div class="script">' + ''.join(f'<p>{esc(p)}</p>' for p in L['intro']) + '</div>'
    if L.get('placement'):
        nc += '<div class="sub">Grapheme placement (slides)</div><p>' + ' ; '.join(esc('/'.join(p)) for p in L['placement']) + '</p>'
    if L.get('gesture'):
        nc += f'<div class="sub">Articulatory Gesture</div><p class="script">{esc(L["gesture"])}</p>'
    if L.get('soundwall'):
        nc += f'<div class="sub">Sound Wall</div><p>{esc(L["soundwall"])}</p>'
    if L.get('formation'):
        nc += f'<div class="sub">Letter Formation</div><p>{esc(L["formation"])}</p>'
    left.append(f'<div class="sec"><h2>5: New Concept</h2><div class="body">{nc}</div></div>')
    # ---- right column ----
    right = []
    rd = L.get('read', {}); sp = L.get('spell', {})
    rs = two('Read', f'<p><b>I do:</b> {words(rd.get("ido", []))}</p><p><b>We do:</b> {words(rd.get("wedo", []))}</p>' + (f'<p><b>Day 2 review:</b> {words(L["review_read"])}</p>' if L.get('review_read') else ''),
             'Spell', f'<p><b>I do:</b> {words(sp.get("ido", []))}</p><p><b>We do:</b> {words(sp.get("wedo", []))}</p>')
    right.append(f'<div class="sec"><h2>5: New Concept <span>(continued)</span></h2><div class="body">{rs}</div></div>')
    ww = L.get('ww')
    if ww:
        inner = ''
        if ww.get('text'): inner += f'<p>{esc(ww["text"])}</p>'
        if ww.get('chain'): inner += f'<p>{chain_html(ww["chain"])}</p>'
        if L.get('tables'):
            for t in L['tables'][:2]:
                rows = ''.join('<tr>' + ''.join(f'<td style="border:1px solid #bbb;padding:2px 5px">{esc(c)}</td>' for c in r) + '</tr>' for r in t if any(r))
                inner += f'<table style="border-collapse:collapse;margin:4px 0;font-size:12px">{rows}</table>'
        right.append(sec('6', 'Word Work', inner, ww.get('type')))
    irr_r = L.get('irr_review', []); irr_t = L.get('irr_teach', [])
    right.append(f'<div class="sec"><h2>7: Irregular Words</h2><div class="body">{two("Review", irr_html(irr_r), "Teach", irr_html(irr_t))}<p style="color:#666;font-size:11.5px;margin-top:4px">*Temporarily irregular. Hover a word to see why it is irregular (from the slide notes).</p></div></div>')
    ct = two('Read', ''.join(f'<p class="sent">{esc(s)}</p>' for s in L.get('sent_read', [])) or '<p>n/a</p>',
             'Spell', ''.join(f'<p class="sent">{esc(s)}</p>' for s in L.get('text_spell', [])) or '<p>n/a</p>')
    dt = f'<div class="sub">Decodable Text</div><p><b>{esc(L.get("passage_title") or "See Decodable Text Guide")}</b> (in the lesson slides)</p>'
    right.append(f'<div class="sec"><h2>8: Connected Text</h2><div class="body">{ct}{dt}</div></div>')
    page1 = f'<div class="page">{head}{banner}<div class="cols"><div>{"".join(left)}</div><div>{"".join(right)}</div></div><div class="foot"><span>Reconstructed from the UFLI Foundations lesson structure for personal use · slides: <a href="{deck_href}">{esc(lesson)} deck</a></span><span>{esc(lesson)} · p.1</span></div></div>'
    # ---- page 2 ----
    p2 = [f'<div class="hdr"><span>UFLI Foundations</span><span><b>{esc(lesson)}</b> | <i>{esc(concept)}</i> (continued)</span></div>{banner}']
    if L.get('chains'):
        p2.append('<div class="sec"><h2>Word Work Chains</h2><div class="body">' + ''.join(f'<div class="sub" style="margin:4px -8px 3px">{esc(lbl)}</div><p>{chain_html(ch) if "→" in ch else esc(ch)}</p>' for lbl, ch in L['chains']) + '</div></div>')
    hf = L.get('hf') or {}
    p2.append(f'<div class="sec"><h2>High Frequency Words Addressed</h2><div class="body">{two("Dolch", "<p>"+(words(hf.get("dolch", [])) or "n/a")+"</p>", "Fry", "<p>"+(words(hf.get("fry", [])) or "n/a")+"</p>")}</div></div>')
    if L.get('lists'):
        p2.append('<div class="sec"><h2>Word Lists</h2><div class="body"><div class="lists">' + ''.join(f'<div><h4>{esc(k)}</h4><ul>' + ''.join(f'<li>{esc(w)}</li>' for w in v) + '</ul></div>' for k, v in L['lists'].items()) + '</div></div></div>')
    if L.get('passage'):
        p2.append(f'<div class="sec"><h2>Decodable Text <span>(from the slides)</span></h2><div class="body"><p><b>{esc(L.get("passage_title",""))}</b></p><div class="passage">{esc(chr(10).join(L["passage"]))}</div></div></div>')
    page2 = f'<div class="page">{"".join(p2)}<div class="foot"><span>Word chains and lists are reconstructed to match the graphemes taught so far.</span><span>{esc(lesson)} · p.2</span></div></div>'
    return page1 + page2
def render_gr(plan, deck_href):
    L = plan
    head = f'<div class="hdr"><span>UFLI Foundations <span class="tag">Getting Ready</span></span><span><b>{esc(L.get("lesson",""))}</b> | <i>{esc(L.get("title2", L.get("title", "")))}</i></span></div>'
    banner = f'<div class="banner"><span class="big">{esc(L.get("lesson",""))}:</span> {esc(L.get("tag", ""))}</div>'
    sw = L.get('soundwall', {})
    sounds = ''.join(f'<tr><td style="padding:3px 8px 3px 0;white-space:nowrap"><b class="heart">{esc(s[0])}</b></td><td style="padding:3px 8px">{esc(s[1])}</td><td style="padding:3px 0;color:#333">{esc(s[2])}</td></tr>' for s in sw.get('sounds', []))
    left = (('<div class="sec"><h2>Instructional Notes</h2><div class="body notes">' + ''.join(f'<p>{esc(n)}</p>' for n in L['notes']) + '</div></div>') if L.get('notes') else '') + \
        f'<div class="sec"><h2>1: Sound Wall</h2><div class="sub">{esc(sw.get("title", L.get("title2","")))}</div><div class="body script">' + ''.join(f'<p>{esc(p)}</p>' for p in sw.get('intro', [])) + f'<table style="border-collapse:collapse;font-size:13px;margin-top:4px">{sounds}</table></div></div>'
    letters = L.get('letters', [])
    right = f'<div class="sec"><h2>2: Alphabet Knowledge & Letter Formation</h2><div class="sub">Letters: {esc(", ".join(letters)) if letters else "pre-writing strokes"}</div><div class="body">' + ''.join(f'<p>{esc(s)}</p>' for s in L.get('strokes', [])) + '<p style="color:#666;font-size:12px">Use the letter-formation animations in the slides: "Watch me write", then "Let\'s write together". Practise with sky writing, tracing and whiteboards.</p></div></div>' + \
        '<div class="sec"><h2>Routines to establish</h2><div class="body"><p>Choral response signal; "My turn / Your turn"; whiteboard "3, 2, 1, show me"; hand gestures for continuous (stretch), stop (chop), voiced (touch throat) and unvoiced sounds.</p></div></div>'
    return f'<div class="page">{head}{banner}<div class="cols"><div>{left}</div><div>{right}</div></div><div class="foot"><span>Getting Ready lessons introduce the 44 phonemes and letter formation; mastery is not expected. Slides: <a href="{deck_href}">deck</a></span><span>{esc(L.get("lesson",""))}</span></div></div>'
def page_html(plan, deck_href, prev_href, next_href):
    body = render(plan, deck_href)
    title = f"{plan.get('lesson','')} {plan.get('concept','')} - Teacher's guide"
    return f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>{esc(title)}</title>
<meta name="viewport" content="width=device-width,initial-scale=1"><link href="https://fonts.googleapis.com/css2?family=Didact+Gothic&display=swap" rel="stylesheet"><link rel="stylesheet" href="../shared/guide.css"><script src="../shared/graphemes.js"></script></head><body>
<div class="topnav"><a href="../index.html">☰ Index</a>{('<a href="'+prev_href+'">◀ Prev</a>') if prev_href else ''}{('<a href="'+next_href+'">Next ▶</a>') if next_href else ''}<span class="sp"></span><span>교사용 지도서 · {esc(plan.get('lesson',''))} {esc(plan.get('concept',''))}</span><a href="{deck_href}" style="margin-left:14px">▶ Open lesson slides</a><button onclick="window.print()">Print / PDF</button></div>
{body}
<div id="pop"><div class="card"></div></div>
<script src="../shared/guide.js"></script></body></html>'''
if __name__ == '__main__':
    plans = json.load(open(os.path.join(S, 'plans_all.json')))
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(S, 'out', 'guide')
    os.makedirs(out, exist_ok=True)
    ids = [i for i in SEQ if i in plans]
    for k, id_ in enumerate(ids):
        p = plans[id_]
        if id_ in "ABCDEFGHIJ": p['lesson'] = f'Getting Ready Lesson {id_}'; p['title2'] = p.get('title', '')
        prev_href = f'lesson_{ids[k-1]}.html' if k > 0 else ''
        next_href = f'lesson_{ids[k+1]}.html' if k < len(ids)-1 else ''
        open(os.path.join(out, f'lesson_{id_}.html'), 'w').write(page_html(p, f'../decks/lesson_{id_}.html', prev_href, next_href))
    print('wrote', len(ids), 'guide pages to', out)
