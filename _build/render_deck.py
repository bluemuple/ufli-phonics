#!/usr/bin/env python3
"""Render a parsed deck JSON into an interactive HTML file."""
import json, os, re, html, sys, math

PX_PER_EMU = 1000/9144000        # slide width 1000px
PT2PX = 750/540                  # slide height 750px = 540pt
ASSET_REL = '../assets/'

def esc(t): return html.escape(t, quote=True)

def css_len_pt(pt): return f"{pt*PT2PX:.2f}px"

# ---------------- text ----------------
def render_text(body, default_color=None, extra_class='', anim_paras=None, font_scale_override=None):
    """body: parsed text body; returns inner html for paragraphs"""
    fs = body.get('fontScale', 1.0)
    if font_scale_override: fs = font_scale_override
    lnred = body.get('lnRed', 0.0)
    out = []
    last_sz = None
    for pi, p in enumerate(body['paras']):
        algn = {'ctr':'center','r':'right','just':'justify','l':'left'}.get(p.get('algn') or 'l', 'left')
        lh = 1.2
        if p.get('lnSpc'):
            if 'pct' in p['lnSpc']: lh = 1.2*p['lnSpc']['pct']
        lh = lh*(1-lnred) if lnred else lh
        style = f"text-align:{algn};line-height:{lh:.2f};"
        if p.get('spcBef'): style += f"margin-top:{css_len_pt(p['spcBef'])};"
        if p.get('spcAft'): style += f"margin-bottom:{css_len_pt(p['spcAft'])};"
        if p.get('marL') or p.get('indent'):
            ml = p.get('marL',0)*PX_PER_EMU; ind = p.get('indent',0)*PX_PER_EMU
            style += f"padding-left:{ml:.1f}px;text-indent:{ind:.1f}px;"
        runs_html = []
        for r in p['runs']:
            sz = r.get('sz') or last_sz or 18
            last_sz = sz
            rs = f"font-size:{sz*fs*PT2PX:.2f}px;"
            if r.get('b'): rs += "font-weight:700;"
            elif r.get('b') is False: rs += "font-weight:400;"
            if r.get('i'): rs += "font-style:italic;"
            if r.get('u'): rs += "text-decoration:underline;"
            if r.get('strike'): rs += "text-decoration:line-through;"
            col = r.get('color') or default_color
            if col: rs += f"color:{col};"
            if r.get('font'): rs += f"font-family:'{r['font']}','Century Gothic',sans-serif;"
            if r.get('spc'): rs += f"letter-spacing:{r['spc']*PT2PX:.2f}px;"
            if r.get('caps'): rs += "text-transform:uppercase;"
            if r.get('baseline'):
                rs += f"vertical-align:{'super' if r['baseline']>0 else 'sub'};font-size:{sz*fs*PT2PX*0.65:.2f}px;"
            if r.get('hl'): rs += f"background:{r['hl']};"
            t = r['t']
            if t == '\n': runs_html.append('<br>')
            else: runs_html.append(f'<span style="{rs}">{esc(t)}</span>')
        if not p['runs']:
            sz = p.get('endsz') or last_sz or 18
            runs_html.append(f'<span style="font-size:{sz*fs*PT2PX:.2f}px">&nbsp;</span>')
        bu = ''
        if p.get('bullet'):
            ch = p['bullet']
            if ch.startswith('auto:'): ch = f"{pi+1}."
            sz = (p['runs'][0].get('sz') if p['runs'] and p['runs'][0].get('sz') else last_sz or 18)
            bu = f'<span class="bu" style="font-size:{sz*fs*PT2PX:.2f}px">{esc(ch)}</span>'
        anim = ''
        if anim_paras and pi in anim_paras:
            anim = f' data-anim="{anim_paras[pi]}"'
        out.append(f'<div class="p" style="{style}"{anim}>{bu}{"".join(runs_html)}</div>')
    return ''.join(out)

def body_text_plain(body):
    return '\n'.join(''.join(r['t'] for r in p['runs']) for p in body['paras']).strip()

# ---------------- shapes ----------------
def fill_css(f):
    if not f or f.get('type') == 'none': return 'transparent'
    if f['type'] == 'solid': return f['color'] or 'transparent'
    if f['type'] == 'grad' and f.get('colors'): return f"linear-gradient(180deg,{','.join(f['colors'])})"
    return 'transparent'

def line_css(l):
    if not l or not l.get('fill') or l['fill'].get('type') in (None, 'none'): return None
    col = l['fill'].get('color') or '#000'
    w = max(0.5, l.get('w', 0.75))*PT2PX
    dash = {'dash':'dashed','sysDash':'dashed','dot':'dotted','sysDot':'dotted','lgDash':'dashed','dashDot':'dashed'}.get(l.get('dash'), 'solid')
    return f"{w:.2f}px {dash} {col}"

SVG_SHAPES = {
    'heart': "M50 88 C20 65 0 48 0 28 C0 12 12 2 26 2 C36 2 45 8 50 16 C55 8 64 2 74 2 C88 2 100 12 100 28 C100 48 80 65 50 88 Z",
    'star5': "M50 2 L61 36 L98 36 L68 58 L79 94 L50 72 L21 94 L32 58 L2 36 L39 36 Z",
    'triangle': "M50 0 L100 100 L0 100 Z",
    'rtTriangle': "M0 0 L100 100 L0 100 Z",
    'diamond': "M50 0 L100 50 L50 100 L0 50 Z",
    'rightArrow': "M0 25 L60 25 L60 0 L100 50 L60 100 L60 75 L0 75 Z",
    'leftArrow': "M100 25 L40 25 L40 0 L0 50 L40 100 L40 75 L100 75 Z",
    'upArrow': "M25 100 L25 40 L0 40 L50 0 L100 40 L75 40 L75 100 Z",
    'downArrow': "M25 0 L25 60 L0 60 L50 100 L100 60 L75 60 L75 0 Z",
    'homePlate': "M0 0 L80 0 L100 50 L80 100 L0 100 Z",
    'chevron': "M0 0 L75 0 L100 50 L75 100 L0 100 L25 50 Z",
    'plus': "M35 0 L65 0 L65 35 L100 35 L100 65 L65 65 L65 100 L35 100 L35 65 L0 65 L0 35 L35 35 Z",
    'pentagon': "M50 0 L100 38 L81 100 L19 100 L0 38 Z",
    'hexagon': "M25 0 L75 0 L100 50 L75 100 L25 100 L0 50 Z",
    'octagon': "M29 0 L71 0 L100 29 L100 71 L71 100 L29 100 L0 71 L0 29 Z",
    'parallelogram': "M20 0 L100 0 L80 100 L0 100 Z",
    'trapezoid': "M20 0 L80 0 L100 100 L0 100 Z",
    'cloud': "M25 85 C10 85 2 72 6 60 C0 50 8 38 20 40 C18 25 32 15 45 22 C52 8 72 8 78 22 C92 18 100 32 94 44 C104 55 96 70 84 70 C84 84 68 90 60 80 C52 90 34 90 25 85 Z",
    'smileyFace': None, 'ellipse': None, 'roundRect': None, 'rect': None,
}

def shape_html(sh, anim_map, features, slide_ctx):
    x, y, w, h = sh['x']*10, sh['y']*7.5, sh['w']*10, sh['h']*7.5  # px in 1000x750
    kind = sh['kind']
    anim = anim_map.get(sh['id'])
    anim_attr = f' data-anim="{anim}"' if anim and not any(a.get('para') is not None for a in slide_ctx['acts_of'].get(sh['id'], [])) else ''
    tf = ''
    if sh.get('rot') or sh.get('flipH') or sh.get('flipV'):
        parts = []
        if sh.get('rot'): parts.append(f"rotate({sh['rot']:.2f}deg)")
        if sh.get('flipH'): parts.append("scaleX(-1)")
        if sh.get('flipV'): parts.append("scaleY(-1)")
        tf = f"transform:{' '.join(parts)};"
    base_style = f"left:{x:.2f}px;top:{y:.2f}px;width:{w:.2f}px;height:{h:.2f}px;{tf}"
    if sh.get('hidden'): return ''
    if kind == 'pic':
        if not sh.get('img'): return ''
        src = ASSET_REL + sh['img']
        style = base_style
        if sh.get('alpha') is not None and sh['alpha'] < 1: style += f"opacity:{sh['alpha']:.2f};"
        bl = line_css(sh.get('line'))
        if bl: style += f"border:{bl};"
        if sh.get('prst') == 'ellipse': style += "border-radius:50%;overflow:hidden;"
        elif sh.get('prst') == 'roundRect': style += f"border-radius:{min(w,h)*0.1667:.1f}px;overflow:hidden;"
        crop = sh.get('crop')
        if crop and any(crop.values()):
            l, t, r, b = crop['l'], crop['t'], crop['r'], crop['b']
            iw = 100/(1-l-r) if (1-l-r) > 0 else 100
            ih = 100/(1-t-b) if (1-t-b) > 0 else 100
            inner = f'<div class="cropwrap"><img src="{src}" style="width:{iw:.2f}%;height:{ih:.2f}%;left:{-l*iw:.2f}%;top:{-t*ih:.2f}%" alt=""></div>'
        else:
            inner = f'<img class="pic" src="{src}" alt="">'
        return f'<div class="sh pic" style="{style}"{anim_attr}>{inner}</div>'
    if kind == 'graphicFrame' and sh.get('table'):
        return table_html(sh, base_style, anim_attr)
    if kind in ('sp', 'cxnSp'):
        prst = sh.get('prst', 'rect')
        fill = sh.get('fill'); line = sh.get('line')
        fc = fill_css(fill); lc = line_css(line)
        cls = 'sh'
        style = base_style
        inner = ''
        is_line = prst in ('line', 'straightConnector1', 'bentConnector2', 'bentConnector3', 'curvedConnector3') or kind == 'cxnSp'
        if is_line:
            col = (line or {}).get('fill', {}) or {}
            col = col.get('color') if col.get('type') == 'solid' else '#000'
            lw = max(0.75, (line or {}).get('w', 0.75))*PT2PX
            dash = (line or {}).get('dash')
            da = ' stroke-dasharray="8 6"' if dash in ('dash','sysDash','lgDash','dashDot') else (' stroke-dasharray="2 4"' if dash in ('dot','sysDot') else '')
            x1, y1, x2, y2 = 0, 0, w, h
            if sh.get('flipV'): y1, y2 = h, 0
            if sh.get('flipH'): x1, x2 = w, 0
            markers = ''
            mk = ''
            if (line or {}).get('tail') not in (None, 'none'):
                markers += f'<marker id="m{slide_ctx["n"]}_{sh["id"]}t" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0 0 L6 3 L0 6 Z" fill="{col}"/></marker>'
                mk += f' marker-end="url(#m{slide_ctx["n"]}_{sh["id"]}t)"'
            if (line or {}).get('head') not in (None, 'none'):
                markers += f'<marker id="m{slide_ctx["n"]}_{sh["id"]}h" markerWidth="6" markerHeight="6" refX="1" refY="3" orient="auto-start-reverse" markerUnits="strokeWidth"><path d="M0 0 L6 3 L0 6 Z" fill="{col}"/></marker>'
                mk += f' marker-start="url(#m{slide_ctx["n"]}_{sh["id"]}h)"'
            # remove the flip transform for lines (handled in coords)
            style = f"left:{x:.2f}px;top:{y:.2f}px;width:{max(w,0.1):.2f}px;height:{max(h,0.1):.2f}px;"
            inner = f'<svg viewBox="0 0 {max(w,0.1):.2f} {max(h,0.1):.2f}" preserveAspectRatio="none"><defs>{markers}</defs><line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{col}" stroke-width="{lw:.2f}"{da}{mk} stroke-linecap="round"/></svg>'
            return f'<div class="{cls}" style="{style}"{anim_attr}>{inner}</div>'
        if prst in ('rect', 'roundRect', 'ellipse', 'snip1Rect', 'flowChartProcess', 'wedgeRectCallout', 'custom', 'flowChartAlternateProcess') or prst not in SVG_SHAPES or SVG_SHAPES.get(prst) is None:
            style += f"background:{fc};"
            if lc: style += f"border:{lc};"
            if prst == 'ellipse': style += "border-radius:50%;"
            elif prst in ('roundRect', 'flowChartAlternateProcess'):
                adj = 16667
                for a in sh.get('adj') or []:
                    if a[0] == 'adj' and a[1].startswith('val '): adj = int(a[1].split()[1])
                style += f"border-radius:{min(w,h)*adj/100000:.1f}px;"
        else:
            path = SVG_SHAPES[prst]
            stroke = ''
            if lc:
                col = line['fill'].get('color') or '#000'; lw = max(0.5, line.get('w', 0.75))*PT2PX
                stroke = f' stroke="{col}" stroke-width="{lw:.2f}" vector-effect="non-scaling-stroke"'
            inner += f'<svg viewBox="0 0 100 100" preserveAspectRatio="none"><path d="{path}" fill="{fc}"{stroke}/></svg>'
        # text
        if sh.get('text'):
            body = sh['text']
            ins = [v*PX_PER_EMU for v in body.get('ins', [91440, 45720, 91440, 45720])]
            anchor = {'t':'flex-start','ctr':'center','b':'flex-end'}.get(body.get('anchor','t'), 'flex-start')
            tstyle = f"padding:{ins[1]:.1f}px {ins[2]:.1f}px {ins[3]:.1f}px {ins[0]:.1f}px;justify-content:{anchor};"
            cls += ' txt'
            nowrap = body.get('wrap') == 'none'
            if nowrap:
                cls += ' nowrap'
                algn = body['paras'][0].get('algn') if body['paras'] else 'l'
                if algn == 'ctr':
                    style = f"left:{x+w/2:.2f}px;top:{y:.2f}px;height:{h:.2f}px;min-width:{w:.2f}px;transform:translateX(-50%) {tf.replace('transform:','').replace(';','')};"
                elif algn == 'r':
                    style = f"right:{1000-(x+w):.2f}px;top:{y:.2f}px;height:{h:.2f}px;min-width:{w:.2f}px;{tf}"
                else:
                    style = f"left:{x:.2f}px;top:{y:.2f}px;height:{h:.2f}px;min-width:{w:.2f}px;{tf}"
                style += f"background:{fc};" + (f"border:{lc};" if lc else '')
            anim_paras = {}
            for a in slide_ctx['acts_of'].get(sh['id'], []):
                if a.get('para') is not None:
                    for pi in range(a['para'][0], a['para'][1]+1):
                        anim_paras[pi] = (anim_paras.get(pi) + ',' if pi in anim_paras else '') + f"{'e' if a['cls']=='entr' else 'x'}:{a['step']}"
            plain = body_text_plain(body)
            extra_attr = ''
            feat = features.get(sh['id'])
            if feat:
                if feat['type'] == 'grapheme':
                    snds = (slide_ctx.get('vd_sounds') or {}).get(feat['g'], [])
                    cls += ' gr'; extra_attr = f' data-grapheme="{esc(feat["g"])}" data-sounds=\'{json.dumps(snds, ensure_ascii=False)}\' data-nsounds="{len(snds)}" title="Click: sounds & example words (E) · H = hint"'
                elif feat['type'] == 'speak':
                    cls += ' spk'; extra_attr = f' data-say="{esc(feat["say"])}" title="Click to hear (S)"'
            inner += f'<div class="{cls}" style="{style}{tstyle}"{anim_attr}{extra_attr}>{render_text(body, sh.get("styleFontColor"), anim_paras=anim_paras)}</div>'
            if inner.startswith('<svg'):
                # svg shape + text overlay: wrap
                return f'<div class="sh" style="{base_style}">{inner}</div>'
            return inner
        return f'<div class="{cls}" style="{style}"{anim_attr}>{inner}</div>'
    return ''

def table_html(sh, base_style, anim_attr):
    t = sh['table']
    cols = t['cols']; total = sum(cols) or 1
    rows = []
    for r in t['rows']:
        cells = []
        for c in r['cells']:
            if c.get('merged'): continue
            st = ''
            f = c.get('fill')
            if f and f.get('type') == 'solid': st += f"background:{f['color']};"
            b = c.get('borders') or {}
            for side, css in (('lnL','border-left'), ('lnR','border-right'), ('lnT','border-top'), ('lnB','border-bottom')):
                if side in b:
                    lf = b[side].get('fill')
                    if lf and lf.get('type') == 'solid': st += f"{css}:{max(0.75,b[side]['w'])*PT2PX:.2f}px solid {lf['color']};"
                    elif lf and lf.get('type') == 'none': st += f"{css}:0;"
                    else: st += f"{css}:1px solid #000;"
                else:
                    st += f"{css}:1px solid #000;"
            ins = [v*PX_PER_EMU for v in c.get('ins', [91440,45720,91440,45720])]
            anchor = {'t':'flex-start','ctr':'center','b':'flex-end'}.get(c.get('anchor') or 't', 'flex-start')
            inner = render_text(c['text']) if c.get('text') else ''
            span = ''
            if c.get('colspan'): span += f' colspan="{c["colspan"]}"'
            if c.get('rowspan'): span += f' rowspan="{c["rowspan"]}"'
            cells.append(f'<td style="{st}"{span}><div class="cell" style="padding:{ins[1]:.1f}px {ins[2]:.1f}px {ins[3]:.1f}px {ins[0]:.1f}px;justify-content:{anchor}">{inner}</div></td>')
        hstyle = f' style="height:{r["h"]*PX_PER_EMU*0.75:.1f}px"' if r.get('h') else ''
        rows.append(f'<tr{hstyle}>{"".join(cells)}</tr>')
    colgroup = ''.join(f'<col style="width:{100*c/total:.2f}%">' for c in cols)
    return f'<table class="tbl" style="{base_style}"{anim_attr}><colgroup>{colgroup}</colgroup>{"".join(rows)}</table>'

# ---------------- step detection ----------------
STEP_TITLES = {'1':'Step 1 · Phonemic Awareness','2':'Step 2 · Visual Drill','3':'Step 3 · Auditory Drill','4':'Step 4 · Blending Drill',
               '5':'Step 5 · New Concept','5R':'Step 5 · New Concept Review','6':'Step 6 · Word Work','7':'Step 7 · Irregular Words',
               '8':'Step 8 · Connected Text','8S':'Step 8 · Spell sentences','8D':'Step 8 · Decodable text','0':'Intro','GR':'Getting Ready'}

def detect_steps(slides):
    step = '0'; seen5 = False
    labels = []
    for s in slides:
        n = (s.get('notes') or '')
        texts = [body_text_plain(sh['text']) for sh in s['shapes'] if sh.get('text')]
        joined = ' '.join(texts)
        m = re.search(r'Step (\d)', n)
        if m:
            st = m.group(1)
            if st == '5':
                if 'review' in n.lower() and seen5: step = '5R'
                else: step = '5'; seen5 = True
            elif st == '8':
                if 'sentences to write' in n.lower(): step = '8S'
                else: step = '8'
            else: step = st
        elif 'decodable text' in n.lower() and step.startswith('8'): step = '8D'
        elif 'Getting Ready' in n: step = 'GR'
        if re.search(r'^Lesson\s+\S+', joined) and 'Day' not in joined and step != '0' and len(s['shapes']) == 1 and not re.search(r'Step', n):
            pass
        s['step'] = step
        labels.append(step)
    return labels

# ---------------- feature detection ----------------
def detect_features(slides):
    """mark grapheme slides, speakable words/sentences, irregular-word why buttons"""
    feats = {}
    for s in slides:
        f = {}
        texts = [(sh, body_text_plain(sh['text'])) for sh in s['shapes'] if sh.get('text')]
        step = s.get('step')
        if step == '2' and s['layout'] == 'logo_slideshow' and len(texts) == 1 and len(texts[0][1]) <= 5 and ' ' not in texts[0][1].strip():
            f[texts[0][0]['id']] = {'type':'grapheme', 'g': texts[0][1].strip()}
        else:
            for sh, t in texts:
                t2 = t.strip()
                if not t2 or t2.startswith('Insert brief') or re.match(r'^Lesson\s', t2) or t2 in ('New Concept Review','Teach','Review'): continue
                words = re.findall(r"[A-Za-z][A-Za-z'\-]*", t2)
                if not words: continue
                # a word or short phrase or sentence/passage -> speakable
                if len(words) <= 60 and not re.search(r'^\d', t2) and not re.search(r'http', t2):
                    if step in ('2',) : continue
                    f[sh['id']] = {'type':'speak', 'say': t2}
        feats[s['n']] = f
    return feats

# ---------------- deck HTML ----------------
def render_deck(model, meta, plan=None, grapheme_js='../shared/graphemes.js', helpers=None, vd_sounds=None):
    slides = model['slides']
    detect_steps(slides)
    feats = detect_features(slides)
    out = []
    menu_items = []
    last_step = None
    day = 0
    total = 0
    for s in slides:
        if s.get('hidden'): continue
        total += 1
    idx = 0
    used_before = set()
    for s in slides:
        if s.get('hidden'): continue
        # helper slides inserted BEFORE this slide (e.g. spelling list before 'Watch me spell')
        if helpers:
            for bi, (rx, hs) in enumerate(helpers.get('before_notes', [])):
                if bi not in used_before and re.search(rx, s.get('notes') or ''):
                    used_before.add(bi)
                    out.append(f'<section class="slide" data-n="{idx+1}" data-steps="0" data-step="{esc(s.get("step") or "")}" data-label="{esc(STEP_TITLES.get(s.get("step"), ""))} · helper">{hs}</section>')
                    idx += 1
        # anim maps
        acts_of = {}
        anim_map = {}
        for si, step in enumerate(s['anims'], 1):
            for a in step:
                a2 = dict(a); a2['step'] = si
                acts_of.setdefault(a['spid'], []).append(a2)
        for spid, acts in acts_of.items():
            if any(a.get('para') is not None for a in acts): continue
            anim_map[spid] = ','.join(f"{'e' if a['cls']=='entr' else 'x'}:{a['step']}" for a in acts if a['cls'] in ('entr','exit'))
        ctx = {'n': s['n'], 'acts_of': acts_of, 'vd_sounds': vd_sounds or {}}
        parts = []
        bg = s.get('bg')
        bgstyle = ''
        if bg and bg.get('type') == 'img' and bg.get('img'):
            parts.append(f'<img class="bg" src="{ASSET_REL}{bg["img"]}" alt="">')
        elif bg and bg.get('type') == 'solid' and bg.get('color'):
            bgstyle = f' style="background:{bg["color"]}"'
        for sh in s.get('layoutShapes', []):
            parts.append(shape_html(sh, {}, {}, ctx))
        for sh in s['shapes']:
            parts.append(shape_html(sh, anim_map, feats.get(s['n'], {}), ctx))
        # irregular word "why" button
        notes = s.get('notes') or ''
        texts = [body_text_plain(sh['text']) for sh in s['shapes'] if sh.get('text')]
        if s['layout'] == 'logo_normal' and s.get('step') == '7' and texts and len(texts[0].split()) <= 2 and 'represents' in notes:
            why = re.sub(r'\n*The white rectangle.*', '', notes, flags=re.S).strip()
            parts.append(f'<button class="qbtn" data-why="{esc(why)}" data-word="{esc(texts[0].strip())}" title="Why is this a heart word?">?</button>')
        # passage / sentence speaker button
        long_texts = [t for t in texts if len(t.split()) >= 4 and not t.startswith('Insert brief')]
        if long_texts:
            say = ' '.join(long_texts)
            parts.append(f'<button class="spkbtn" data-say="{esc(say)}" title="Read aloud (S)">🔊</button>')
        nsteps = len(s['anims'])
        label = STEP_TITLES.get(s.get('step'), '')
        # title-ish slide for menu
        joined = ' | '.join(t.replace('\n',' ') for t in texts)
        if s.get('step') != last_step:
            menu_items.append((idx, label, ''))
            last_step = s.get('step')
        if re.match(r'^Lesson\s', joined) or re.match(r'^Getting Ready', joined):
            day += 1
            menu_items.append((idx, f'Day {day}' if day <= 2 else joined, 'day'))
        notes_html = f'<div class="notes" hidden>{esc(notes)}</div>' if notes else ''
        parts.append(notes_html)
        out.append(f'<section class="slide" data-n="{idx+1}" data-steps="{nsteps}" data-step="{esc(s.get("step") or "")}" data-label="{esc(label)}"{bgstyle}>{"".join(parts)}</section>')
        idx += 1
        # helper slides injection after header slides
        if helpers and s.get('step') in helpers.get('after_header', {}) and s['layout'] in ('BLANK','Blank') and re.search(r'Step \d', notes) and not s['shapes']:
            for hs in helpers['after_header'].pop(s['step']):
                out.append(f'<section class="slide" data-n="{idx+1}" data-steps="0" data-step="{esc(s.get("step"))}" data-label="{esc(label)} · helper">{hs}</section>')
                idx += 1
    menu_html = ''.join(f'<a href="#" data-go="{i}" class="{cls}">{esc(lbl)}<small>#{i+1}</small></a>' for i, lbl, cls in menu_items if lbl)
    plan_js = f"<script>window.LESSON_PLAN = {json.dumps(plan, ensure_ascii=False)};</script>" if plan else ''
    title = meta.get('title', 'UFLI Lesson')
    return f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>{esc(title)}</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Didact+Gothic&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../shared/deck.css">
<script>window.DECK_META = {json.dumps(meta, ensure_ascii=False)};</script>
<script src="{grapheme_js}"></script>
{plan_js}
</head><body>
<div id="stage"><div id="viewport">
{''.join(out)}
<div id="hint"></div>
</div></div>
<div id="details" title="Details mode (D): → shows example words on grapheme slides and steps through the auditory drill grapheme by grapheme"><span class="dot"></span><span class="lbl">Details OFF</span><small>D</small></div>
<div id="bar"></div>
<div id="hud">
  <button id="btnMenu" title="Steps (M)">☰ Steps</button>
  <button id="btnPrev" title="Previous (←)">◀</button>
  <button id="btnNext" title="Next (→)">▶</button>
  <span id="count"></span>
  <span class="step" id="steplbl"></span>
  <span class="sp"></span>
  <span style="color:#8a97a8">{esc(title)}</span>
  <button id="btnNotes" title="Teacher notes (N)">📝 Notes</button>
  <button id="btnFull" title="Fullscreen (F)">⛶ Full</button>
  <button id="btnHelp" title="Keyboard help (?)">?</button>
  <a href="../index.html" style="color:#8fd3cf;text-decoration:none;margin-left:6px">Index</a>
</div>
<div id="panel"></div>
<div id="menu"><h3>Lesson steps</h3>{menu_html}</div>
<div id="pop"><div class="card"></div></div>
<div id="help"><div class="card">
<b style="font-size:17px">Keyboard shortcuts · 키보드 단축키</b><br>
<kbd>→</kbd> <kbd>Space</kbd> next (reveals hidden items first) · 다음 화면<br>
<kbd>←</kbd> previous · 이전 화면 &nbsp; <kbd>↓</kbd>/<kbd>↑</kbd> skip whole slide<br>
<kbd>F</kbd> fullscreen · 전체화면 &nbsp; <kbd>N</kbd> teacher notes panel · 교사 노트 &nbsp; <kbd>M</kbd> step menu · 단계 메뉴<br>
<kbd>S</kbd> read the word/sentence aloud · 소리 듣기 &nbsp; <kbd>E</kbd> grapheme examples popup · 예시 단어<br>
<kbd>D</kbd> Details mode on/off · 자세히 모드 (→ shows example words on grapheme cards; auditory drill goes grapheme by grapheme with words) &nbsp; <kbd>H</kbd> hint: how many sounds · 힌트<br>
<kbd>A</kbd> reveal all on this slide · 모두 보이기 &nbsp; <kbd>R</kbd> reset slide · 초기화 &nbsp; <kbd>G</kbd> go to slide number<br>
<kbd>Home</kbd>/<kbd>End</kbd> first/last slide &nbsp; <kbd>Esc</kbd> close panels &nbsp; <kbd>?</kbd> this help<br>
<span style="color:#8a97a8">Click the right side of a slide = next, left edge = previous. Click a word to hear it, click a grapheme card for example words.</span>
</div></div>
<script src="../shared/deck.js"></script>
</body></html>'''

if __name__ == '__main__':
    src, out = sys.argv[1], sys.argv[2]
    model = json.load(open(src))
    meta = {'id': os.path.basename(out).replace('.html',''), 'title': json.loads(sys.argv[3]) if len(sys.argv) > 3 else 'UFLI Lesson'}
    with open(out, 'w') as f: f.write(render_deck(model, meta))
    print('wrote', out)

# ======================= helper slides & plan panel (added) =======================
def _split_item(s):
    """'/m/ /ŏ/ /p/ (mop)' -> ('/m/ /ŏ/ /p/', 'mop'); 'caution (cau-tion): ...' -> ('caution', 'cau-tion ...')"""
    m = re.match(r'^(.*?)\s*\((.*?)\)\s*(.*)$', s)
    if m: return (m.group(1).strip(), (m.group(2) + (' ' + m.group(3) if m.group(3) else '')).strip())
    return (s, '')
def helper_items(title, subtitle, items, swap=False, cols=2, foot=''):
    rows = []
    for it in items:
        p, a = _split_item(it)
        if swap: p, a = a, p
        rows.append(f'<div class="item q"><span>{esc(p)}</span><span class="ans">{esc(a)}</span></div>')
    return f'<div class="helper"><span class="badge">HELPER · 도우미</span><h1>{esc(title)}</h1><h2>{esc(subtitle)}</h2><div class="grid" style="grid-template-columns:repeat({cols},1fr)">{"".join(rows)}</div><div class="foot">{esc(foot)}  ·  → or click = reveal next · A = reveal all · R = reset</div></div>'
def _diff_mark(prev, cur):
    if not prev: return esc(cur)
    a, b = prev.lower(), cur.lower()
    i = 0
    while i < min(len(a), len(b)) and a[i] == b[i]: i += 1
    j = 0
    while j < min(len(a), len(b)) - i and a[-1-j] == b[-1-j]: j += 1
    mid_end = len(cur) - j
    if i >= mid_end: 
        # deletion only: highlight nothing
        return esc(cur)
    return esc(cur[:i]) + '<span class="chg">' + esc(cur[i:mid_end]) + '</span>' + esc(cur[mid_end:])
def helper_chain(title, subtitle, chain, foot=''):
    ws = [w.strip() for w in re.split(r'\s*→\s*', chain) if w.strip()]
    spans = []
    prev = ''
    for w in ws:
        nonsense = w.endswith('*'); w2 = w.rstrip('*')
        spans.append(f'<span class="w{" ns" if nonsense else ""}" title="{"nonsense word" if nonsense else ""}">{_diff_mark(prev, w2)}</span>')
        prev = w2
    return f'<div class="helper"><span class="badge">HELPER · 도우미</span><h1>{esc(title)}</h1><h2>{esc(subtitle)}</h2><div class="big"></div><div class="chain">{"<span class=arrow>→</span>".join(spans)}</div><div class="foot">{esc(foot)}  ·  → or click a word = next word · ← = back · A = show all · R = reset</div></div>'
def helper_sentences(title, subtitle, sents, foot=''):
    return f'<div class="helper"><span class="badge">HELPER · 도우미</span><h1>{esc(title)}</h1><h2>{esc(subtitle)}</h2>' + ''.join(f'<div class="sent">{esc(s)}</div>' for s in sents) + f'<div class="foot">{esc(foot)}  ·  → or click = reveal next sentence · A = all · R = reset</div></div>'
def helper_grid_board(bd):
    grid = bd.get('grid') or {}
    cols = ''.join(f'<div class="item" style="flex-direction:column;align-items:flex-start;font-size:22px;min-height:0"><b style="font-size:14px;color:#5b6b7f;text-transform:uppercase;letter-spacing:.08em">{k}</b><div>{" ".join(f"<span style=\'display:inline-block;border:2px solid #cfd6de;border-radius:8px;padding:0 8px;margin:2px\'>{esc(t)}</span>" for t in grid.get(k, []) if t)}</div></div>' for k in ('initial','medial','final'))
    return cols
def build_helpers(plan):
    """returns dict: {'after_header': {step: [html,...]}, 'before_notes': [(regex, html)]}"""
    H = {'after_header': {}, 'before_notes': []}
    if not plan or plan.get('gr'): return H
    pa = plan.get('pa')
    if pa:
        H['after_header']['1'] = [helper_items('Phonemic Awareness', 'Blend: I say the sounds, you say the word.  |  Segment: I say the word, you say the sounds.',
            [f"{p} ({a})" for p, a in [_split_item(x) for x in pa['blend']]] + [f"{p} ({a})" for p, a in [_split_item(x) for x in pa['segment']]], cols=2, foot='Step 1 · 2 minutes')]
    if plan.get('ad'):
        H['after_header']['3'] = helper_auditory(plan['ad'])
    bd = plan.get('bd')
    if bd and bd.get('chain'):
        board = f'<div class="helper"><span class="badge">HELPER · 도우미</span><h1>Blending Board</h1><h2>Tiles for this lesson (initial · medial · final). Teacher builds the words; student reads.</h2><div class="grid" style="grid-template-columns:1fr 1fr 1fr">{helper_grid_board(bd)}</div><div class="foot">Step 4 · 5 minutes · say each sound, then blend: /sssaaat/ sat</div></div>'
        H['after_header']['4'] = [board, helper_chain('Blending Drill', 'Read each word. Only the changed letters are red.', bd['chain'], foot='Step 4 · 5 minutes')]
    sp = plan.get('spell') or {}
    if sp.get('ido') or sp.get('wedo'):
        items = [f"I do ({w})" for w in sp.get('ido', [])] + [f"We do ({w})" for w in sp.get('wedo', [])]
        H['before_notes'].append((r'Step 5 for words to spell', helper_items('Spell', 'Teacher says the word; student segments and writes it. Click to check.', items, cols=2, foot='Step 5 · Elkonin boxes or Pound-and-Sound')))
    ww = plan.get('ww')
    if ww:
        parts = []
        if ww.get('chain') and '→' in ww['chain']:
            parts.append(helper_chain('Word Work', ww.get('type', ''), ww['chain'], foot='Step 6 · 6 minutes · alternate: "Change X to Y" (spell) and "What word is it now?" (read)'))
        elif ww.get('chain'):
            parts.append(helper_items('Word Work', ww.get('type', ''), [x.strip() + ' ( )' if '(' not in x else x for x in re.split(r',\s*', ww['chain'])], cols=2, foot='Step 6'))
        if ww.get('text'):
            parts.append(f'<div class="helper"><span class="badge">HELPER · 도우미</span><h1>Word Work</h1><h2>{esc(ww.get("type",""))}</h2><div class="script">{esc(ww["text"])}</div><div class="foot">Step 6 · 6 minutes</div></div>')
        if parts: H['after_header']['6'] = parts
    if plan.get('text_spell'):
        H['after_header']['8S'] = [helper_sentences('Spell a sentence', 'Teacher dictates; student repeats, then writes. Check with CAPS: Capitals · Appearance · Punctuation · Spelling.', plan['text_spell'], foot='Step 8 · 6-8 minutes')]
    return H
def plan_panel(plan):
    """LESSON_PLAN object for the notes panel"""
    if not plan: return None
    def li(items): return '<ul style="margin:4px 0 8px 18px;padding:0">' + ''.join(f'<li>{esc(x)}</li>' for x in items) + '</ul>'
    steps = {}
    if plan.get('gr'):
        sw = plan.get('soundwall', {})
        steps['GR'] = {'title': 'Getting Ready', 'html': ''.join(f'<p>{esc(p)}</p>' for p in sw.get('intro', [])) + li([f"{s[0]} {s[1]} – {s[2]}" for s in sw.get('sounds', [])]) + '<p><b>Letters:</b> ' + esc(', '.join(plan.get('letters', []))) + '</p>' + li(plan.get('strokes', []))}
        return {'steps': steps, 'notesHtml': ''.join(f'<p>{esc(n)}</p>' for n in plan.get('notes', []))}
    pa = plan.get('pa')
    if pa: steps['1'] = {'title': 'Phonemic Awareness (2 min)', 'html': '<b>Blend</b>' + li(pa['blend']) + '<b>Segment</b>' + li(pa['segment'])}
    if plan.get('vd'): steps['2'] = {'title': 'Visual Drill (3 min)', 'html': '<p>Show each grapheme; student says the letter(s) and the sound(s):</p>' + li([f"{g} ({', '.join(s)})" for g, s in plan['vd']]) + '<p>Press <b>E</b> on a grapheme slide for example words.</p>'}
    if plan.get('ad'): steps['3'] = {'title': 'Auditory Drill (5 min)', 'html': '<p>Say the sound; student repeats and writes the spelling(s):</p>' + li([f"{ph} → {', '.join(sp)}" for ph, sp in plan['ad']])}
    bd = plan.get('bd')
    if bd: steps['4'] = {'title': 'Blending Drill (5 min)', 'html': f'<p><b>Chain:</b> {esc(bd["chain"])}</p>' + ''.join(f'<p><b>{k}:</b> {esc(", ".join(bd.get("grid", {}).get(k, [])))}</p>' for k in ('initial','medial','final')) + (f'<p><i>{esc(bd["note"])}</i></p>' if bd.get('note') else '')}
    nc = ''
    if plan.get('intro'): nc += '<b>Introduction</b>' + ''.join(f'<p>{esc(p)}</p>' for p in plan['intro'])
    if plan.get('gesture'): nc += f'<b>Articulatory gesture</b><p>{esc(plan["gesture"])}</p>'
    if plan.get('soundwall'): nc += f'<b>Sound wall</b><p>{esc(plan["soundwall"])}</p>'
    if plan.get('formation'): nc += f'<b>Letter formation</b><p>{esc(plan["formation"])}</p>'
    rd = plan.get('read', {}); sp = plan.get('spell', {})
    nc += f'<b>Read</b><p>I do: {esc(", ".join(rd.get("ido", [])))}<br>We do: {esc(", ".join(rd.get("wedo", [])))}</p><b>Spell</b><p>I do: {esc(", ".join(sp.get("ido", [])))}<br>We do: {esc(", ".join(sp.get("wedo", [])))}</p>'
    steps['5'] = {'title': 'New Concept (15 min)', 'html': nc}
    steps['5R'] = {'title': 'New Concept Review (3 min)', 'html': '<p>Repeat the introduction briefly, point to the grapheme on the sound wall, then read:</p><p>' + esc(', '.join(plan.get('review_read', []))) + '</p>' + nc}
    ww = plan.get('ww')
    if ww: steps['6'] = {'title': 'Word Work (6 min)', 'html': f'<p><b>{esc(ww.get("type",""))}</b></p>' + (f'<p>{esc(ww["text"])}</p>' if ww.get('text') else '') + (f'<p>{esc(ww["chain"])}</p>' if ww.get('chain') else '') + ''.join(f'<p><b>{esc(l)}:</b> {esc(c)}</p>' for l, c in plan.get('chains', []))}
    irr = ''
    for label, items in (('Review', plan.get('irr_review', [])), ('Teach', plan.get('irr_teach', []))):
        if items:
            irr += f'<b>{label}</b><ul style="margin:4px 0 8px 18px;padding:0">' + ''.join(f'<li><b>{esc(w["word"])}</b>: {esc(" ".join(n for n in (w.get("notes") or "").split(chr(10)) if n.strip() and not n.startswith("The white rectangle")))}</li>' for w in items) + '</ul>'
    steps['7'] = {'title': 'Irregular Words (6 min)', 'html': irr or '<p>Review previously taught irregular words as needed.</p>'}
    steps['8'] = {'title': 'Connected Text – read (2-3 min)', 'html': li(plan.get('sent_read', []))}
    steps['8S'] = {'title': 'Connected Text – spell (6-8 min)', 'html': li(plan.get('text_spell', []))}
    steps['8D'] = {'title': 'Decodable text (5-7 min)', 'html': f'<p><b>{esc(plan.get("passage_title",""))}</b></p><p>Echo read, then choral read. Ask a quick question about the meaning.</p>'}
    return {'steps': steps, 'notesHtml': ''.join(f'<p>{esc(n)}</p>' for n in plan.get('notes', []))}


# ---- auditory drill helper: sounds column + detail panel (graphemes and example words) ----
_GR = None
def _gr():
    global _GR
    if _GR is None:
        import plan_build; _GR = plan_build.load_graphemes()
    return _GR
def _toks(ph): return [x.replace('/', '').lower() for x in re.sub(r'\(.*?\)', '', str(ph)).split() if x.strip()]
def _examples(sp, ph):
    info = _gr().get(sp) or _gr().get(sp.lstrip('-')) or {}
    sounds = info.get('sounds', [])
    if not sounds: return []
    n1 = re.sub(r'\s+', '', ph).lower()
    m = next((s for s in sounds if re.sub(r'\s+', '', s['ph']).lower() == n1), None)
    if m is None:
        t = _toks(ph)
        m = next((s for s in sounds if any(x in _toks(s['ph']) for x in t)), sounds[0])
    ex = m['ex'][:3]
    if len(', '.join(ex)) > 24: ex = ex[:2]
    return ex
def _mark(word, g):
    core = re.sub(r'^-|-$', '', g).replace('_e', '').lstrip('_')
    i = word.lower().find(core.lower()) if core else -1
    if i < 0: return esc(word)
    return esc(word[:i]) + '<mark>' + esc(word[i:i+len(core)]) + '</mark>' + esc(word[i+len(core):])
def helper_auditory(ad, per_page=7):
    pages = [ad[i:i+per_page] for i in range(0, len(ad), per_page)] or [[]]
    out = []
    for pi, page in enumerate(pages):
        snds = ''.join(f'<div class="snd"><span>{esc(ph.replace(" (unvoiced)", " (quiet)"))}</span><span class="n">{len(sp)} spelling{"s" if len(sp)!=1 else ""}</span></div>' for ph, sp in page)
        groups = []
        for ph, sp in page:
            rows = ''.join(f'<div class="grow"><span class="gch">{esc(g)}</span><span class="gex">{" ".join(f"<span>{_mark(w, g)}</span>" + ("," if j < len(_examples(g, ph))-1 else "") for j, w in enumerate(_examples(g, ph)))}</span></div>' for g in sp)
            groups.append(f'<div class="sgroup"><div class="ph">{esc(ph)} — spellings ({len(sp)})</div>{rows}</div>')
        pg = f' ({pi+1}/{len(pages)})' if len(pages) > 1 else ''
        out.append(f'<div class="helper ad"><span class="badge">HELPER · 도우미</span><h1>Auditory Drill{pg}</h1><h2>I say the sound; you repeat it and write the spelling(s). Details ON: → grapheme, → its example words.</h2><div class="layout"><div class="sounds">{snds}</div><div class="detail">{"".join(groups)}</div></div><div class="foot">Step 3 · 5 minutes · whiteboard  ·  → next · ← back · A = show all for this sound · R = reset · D = Details on/off</div></div>')
    return out
