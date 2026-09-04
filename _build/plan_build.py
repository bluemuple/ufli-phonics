#!/usr/bin/env python3
"""Assemble complete lesson plans: authored data + deck-extracted content + derived drills."""
import json, os, re, sys
S = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(S, 'plans'))
from gpc import SEQ, IDX, sounds_at, auditory_from_visual
import plans_a, plans_b, plans_c, plans_d, plans_e, plans_f, plans_g
AUTH = {}
for m in (plans_a, plans_b, plans_c, plans_d, plans_e, plans_f, plans_g): AUTH.update(m.P)
GR = None
def load_graphemes():
    global GR
    if GR: return GR
    import subprocess
    js_path = os.path.join(S, 'shared', 'graphemes.js')
    out = subprocess.run(['node', '-e', "global.window={}; require(process.argv[1]); process.stdout.write(JSON.stringify(window.GRAPHEMES));", js_path], capture_output=True, text=True, check=True)
    GR = json.loads(out.stdout)
    return GR
def title_parts(content):
    t = content.get('title', '')
    m = re.match(r'^(Lesson\s+\S+(?:\s+AUS)?|Getting Ready Lesson \S+)\s*(.*)$', t)
    return (m.group(1), m.group(2)) if m else (t, '')
def build(id_):
    cpath = os.path.join(S, 'content', id_ + '.json')
    content = json.load(open(cpath)) if os.path.exists(cpath) else {}
    a = AUTH.get(id_, {})
    lesson_no, concept = title_parts(content)
    plan = {'id': id_, 'lesson': lesson_no, 'concept': concept or a.get('title', ''), 'title': content.get('title', ''), 'nslides': content.get('nslides', 0)}
    plan.update({k: v for k, v in a.items()})
    if a.get('gr'):
        plan['gr'] = True
        plan['lesson'] = f'Getting Ready Lesson {id_}'
        plan['concept'] = a.get('title', '')
        plan['title'] = f"Getting Ready Lesson {id_} · {a.get('title', '')}"
        return plan
    vd = content.get('graphemes', [])
    plan['vd'] = [(g, sounds_at(g, id_) or [s['ph'] for s in load_graphemes().get(g, {}).get('sounds', [])][:1]) for g in vd]
    plan['ad'] = auditory_from_visual(vd, id_) if vd else []
    rw = content.get('read_words', [])
    if not a.get('read'):
        plan['read'] = {'ido': rw[:1], 'wedo': rw[1:]} if rw else {'ido': [], 'wedo': []}
    plan['review_read'] = content.get('review_words', [])
    plan['placement'] = content.get('placement', [])[: max(1, len(content.get('placement', []))//2)]
    plan['irr_review'] = content.get('irregular_review', [])
    plan['irr_teach'] = content.get('irregular_teach', [])
    plan['sent_read'] = content.get('sentences', [])
    plan['passage_title'] = content.get('passage_title', '')
    plan['passage'] = content.get('passage', [])
    plan['tables'] = content.get('tables', [])
    return plan
def build_all():
    return {id_: build(id_) for id_ in SEQ}
if __name__ == '__main__':
    allp = build_all()
    json.dump(allp, open(os.path.join(S, 'plans_all.json'), 'w'), ensure_ascii=False, indent=0)
    p = allp['12']
    print(json.dumps({k: p[k] for k in ('lesson','concept','vd','ad','read','review_read','irr_teach','sent_read','passage_title')}, ensure_ascii=False)[:1500])
    print(len(allp), 'plans;', sum(1 for v in allp.values() if 'pa' in v), 'core plans with PA')
