#!/usr/bin/env python3
"""Extract structured lesson content from parsed deck JSONs -> build/content/<id>.json + overview"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from render_deck import detect_steps, body_text_plain
S = os.path.dirname(os.path.abspath(__file__))
JD = os.path.join(S, 'json'); CD = os.path.join(S, 'content'); os.makedirs(CD, exist_ok=True)

def lesson_key(id_):
    m = re.match(r'^(\d+)([a-zA-Z]*)$', id_)
    if m: return (1, int(m.group(1)), m.group(2))
    return (0, ord(id_[0]), '')

def texts_of(s):
    return [(sh, body_text_plain(sh['text'])) for sh in s['shapes'] if sh.get('text') and body_text_plain(sh['text'])]

def extract(id_):
    m = json.load(open(os.path.join(JD, id_ + '.json')))
    slides = m['slides']
    detect_steps(slides)
    c = {'id': id_, 'source': m.get('source'), 'nslides': len(slides), 'title': '', 'concept': '', 'graphemes': [], 'concept_slides': [],
         'read_words': [], 'review_words': [], 'irregular_review': [], 'irregular_teach': [], 'sentences': [], 'passage_title': '', 'passage': [],
         'word_work': [], 'tables': [], 'placement': []}
    seen_words = set()
    for s in slides:
        tx = texts_of(s)
        joined = ' | '.join(t for _, t in tx)
        st = s.get('step')
        notes = s.get('notes') or ''
        if not c['title'] and re.match(r'^(Lesson|Getting Ready)', joined):
            lines = [l.strip() for l in tx[0][1].split('\n') if l.strip()]
            c['title'] = ' '.join(lines)
            c['concept'] = lines[1] if len(lines) > 1 else ''
        if st == '2' and s['layout'] == 'logo_slideshow' and len(tx) == 1 and len(tx[0][1].strip()) <= 6 and ' ' not in tx[0][1].strip():
            c['graphemes'].append(tx[0][1].strip())
        if st in ('5', '5R'):
            if s['layout'] in ('BLANK', 'Blank') and tx and all(len(t.split()) <= 3 for _, t in tx) and not any(t.startswith(('Insert','New Concept')) for _, t in tx):
                words = [t.strip() for _, t in tx]
                key = 'read_words' if st == '5' else 'review_words'
                for w in words:
                    if w not in seen_words or st == '5R':
                        c[key].append(w); seen_words.add(w)
            if s['layout'] == 'grapheme placement':
                c['placement'].append([t.strip() for _, t in tx])
            if s['layout'] in ('logo_slideshow', 'logo_presenter') and tx:
                c['concept_slides'].append({'n': s['n'], 'texts': [t.strip() for _, t in tx], 'notes': notes[:200]})
        if st == '7':
            if s['layout'] == 'logo_normal' and tx:
                w = tx[0][1].strip()
                info = {'word': w, 'notes': notes.replace('\n\n', '\n').strip()}
                # heuristics: Teach section begins after a slide with text 'Teach'
                c.setdefault('_irr', []).append(info)
            if tx and tx[0][1].strip() == 'Teach': c['_teach_marker'] = len(c.get('_irr', []))
            if tx and tx[0][1].strip() == 'Review': c['_review_marker'] = len(c.get('_irr', []))
        if st == '8' and s['layout'] in ('BLANK', 'Blank') and tx and len(tx) == 1 and len(tx[0][1].split()) >= 2 and not tx[0][1].startswith('Insert'):
            c['sentences'].append(tx[0][1].strip())
        if st == '8D' and tx:
            titles = []
            if not c['passage_title']:
                cands = [(sh, t) for sh, t in tx if len(t.split()) <= 7 and '\n' not in t.strip()]
                if cands:
                    cands.sort(key=lambda x: x[0]['y'])
                    titles = [cands[0][1]]
                    c['passage_title'] = cands[0][1].strip()
            bodies = [t for sh, t in tx if t not in titles]
            for b in bodies:
                if len(b.split()) >= 3 and not b.startswith('Insert'): c['passage'].append(b.strip())
        if st == '6':
            for sh in s['shapes']:
                if sh.get('table'):
                    rows = [[body_text_plain(cell['text']) if cell.get('text') else '' for cell in r['cells']] for r in sh['table']['rows']]
                    c['tables'].append(rows)
            if tx and s['layout'] not in ('BLANK','Blank'):
                c['word_work'].append([t.strip() for _, t in tx])
            elif tx and all(len(t.split()) <= 3 for _, t in tx) and not any(t.startswith('Insert') for _, t in tx):
                c['word_work'].append([t.strip() for _, t in tx])
    irr = c.pop('_irr', [])
    tm = c.pop('_teach_marker', None)
    c.pop('_review_marker', None)
    if tm is None:
        c['irregular_review'] = irr
    else:
        c['irregular_review'] = irr[:tm]; c['irregular_teach'] = irr[tm:]
    json.dump(c, open(os.path.join(CD, id_ + '.json'), 'w'), ensure_ascii=False, indent=1)
    return c

ids = sorted([f[:-5] for f in os.listdir(JD) if f.endswith('.json')], key=lesson_key)
overview = []
for id_ in ids:
    c = extract(id_)
    overview.append(c)
    print(f"{id_:>6} | {c['title'][:34]:34s} | n={c['nslides']:3d} | VD={len(c['graphemes']):2d} | read={len(c['read_words']):2d} rev={len(c['review_words']):2d} | irrR={len(c['irregular_review'])} irrT={len(c['irregular_teach'])} | sent={len(c['sentences'])} | pass={'Y' if c['passage'] else '-'} {c['passage_title'][:22]}")
json.dump(overview, open(os.path.join(S, 'content_overview.json'), 'w'), ensure_ascii=False)
