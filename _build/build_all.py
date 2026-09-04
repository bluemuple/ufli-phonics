#!/usr/bin/env python3
"""Build everything into the output folder: decks, guides, index, shared, fonts, assets."""
import json, os, sys, shutil, re, html
S = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, S); sys.path.insert(0, os.path.join(S, 'plans'))
from gpc import SEQ
import render_deck, render_guide, plan_build
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(S, 'out')
def esc(t): return html.escape(str(t), quote=True)
os.makedirs(os.path.join(OUT, 'decks'), exist_ok=True); os.makedirs(os.path.join(OUT, 'guide'), exist_ok=True)
os.makedirs(os.path.join(OUT, 'shared'), exist_ok=True); os.makedirs(os.path.join(OUT, 'fonts'), exist_ok=True); os.makedirs(os.path.join(OUT, 'assets'), exist_ok=True)
for f in os.listdir(os.path.join(S, 'shared')):
    if os.path.abspath(os.path.join(S, 'shared', f)) != os.path.abspath(os.path.join(OUT, 'shared', f)): shutil.copy(os.path.join(S, 'shared', f), os.path.join(OUT, 'shared', f))
FONTSRC = '/Applications/Microsoft PowerPoint.app/Contents/Resources/DFonts'
for src, dst in (('Century Gothic.ttf','CenturyGothic.ttf'),('Century Gothic Bold.ttf','CenturyGothic-Bold.ttf'),('Century Gothic Italic.ttf','CenturyGothic-Italic.ttf'),('Century Gothic Bold Italic.ttf','CenturyGothic-BoldItalic.ttf')):
    sp, dp = os.path.join(FONTSRC, src), os.path.join(OUT, 'fonts', dst)
    if os.path.exists(sp) and not os.path.exists(dp): shutil.copy(sp, dp)
if os.path.abspath(os.path.join(S, 'out', 'assets')) != os.path.abspath(os.path.join(OUT, 'assets')):
    for f in os.listdir(os.path.join(S, 'out', 'assets')):
        dp = os.path.join(OUT, 'assets', f)
        if not os.path.exists(dp): shutil.copy(os.path.join(S, 'out', 'assets', f), dp)
plans = plan_build.build_all()
json.dump(plans, open(os.path.join(S, 'plans_all.json'), 'w'), ensure_ascii=False)
# ---- decks ----
titles = {}
for id_ in SEQ:
    jp = os.path.join(S, 'json', id_ + '.json')
    if not os.path.exists(jp): print('missing deck json', id_); continue
    model = json.load(open(jp))
    plan = plans.get(id_)
    title = plan.get('title') or f'Lesson {id_}'
    titles[id_] = title
    meta = {'id': f'lesson_{id_}', 'title': title}
    helpers = render_deck.build_helpers(plan)
    html_out = render_deck.render_deck(model, meta, plan=render_deck.plan_panel(plan), helpers=helpers, vd_sounds={g: s for g, s in plan.get('vd', [])})
    open(os.path.join(OUT, 'decks', f'lesson_{id_}.html'), 'w').write(html_out)
# user's own decks
own = [('own_111_charlie', "/Users/moonleon/Documents/Phonics program/pptx for interactive html/UFLI_Foundations_Lesson_111(Charlie).pptx", "Lesson 111 (Charlie's version)"),
       ('own_111_copy', "/Users/moonleon/Documents/Phonics program/pptx for interactive html/Copy of Copy of UFLI_Foundations_Lesson_111.pptx", "Lesson 111 (own copy)"),
       ('own_123_us', "/Users/moonleon/Documents/Phonics program/pptx for interactive html/Copy of Copy of 123_Slides_UFLIFoundations.pptx", "Lesson 123 -y (US copy)")]
import parse_pptx
for oid, path, title in own:
    if not os.path.exists(path): continue
    d = parse_pptx.Deck(path, os.path.join(OUT, 'assets')); model = d.parse()
    pid = '111' if '111' in oid else '123'
    plan = plans.get(pid)
    html_out = render_deck.render_deck(model, {'id': oid, 'title': title}, plan=render_deck.plan_panel(plan), helpers=render_deck.build_helpers(plan), vd_sounds={g: s for g, s in plan.get('vd', [])})
    open(os.path.join(OUT, 'decks', f'{oid}.html'), 'w').write(html_out)
# ---- guides ----
ids = [i for i in SEQ if i in plans]
for k, id_ in enumerate(ids):
    p = plans[id_]
    if id_ in "ABCDEFGHIJ": p['lesson'] = f'Getting Ready Lesson {id_}'; p['title2'] = p.get('concept', '')
    prev_href = f'lesson_{ids[k-1]}.html' if k > 0 else ''
    next_href = f'lesson_{ids[k+1]}.html' if k < len(ids)-1 else ''
    open(os.path.join(OUT, 'guide', f'lesson_{id_}.html'), 'w').write(render_guide.page_html(p, f'../decks/lesson_{id_}.html', prev_href, next_href))
# ---- index ----
groups = [("Getting Ready A–J", list("ABCDEFGHIJ")), ("Lessons 1–34 · Alphabet", [str(i) for i in range(1,35)]),
          ("Lessons 35–41 · Short vowel reviews", ["35a","35b","35c","36a","36b","37a","37b","38a","38b","39a","39b","40a","40b","41a","41b","41c"]),
          ("Lessons 42–53 · Digraphs", [str(i) for i in range(42,54)]), ("Lessons 54–62 · VCe", [str(i) for i in range(54,63)]),
          ("Lessons 63–68 · Reading longer words", ["63","64","65","66","67a","67b","68"]), ("Lessons 69–76 · Ending patterns", [str(i) for i in range(69,77)]),
          ("Lessons 77–83 · R-controlled vowels", ["77","77AUS","78","79","80","80AUS","81","82","83"]), ("Lessons 84–88 · Long vowel teams", [str(i) for i in range(84,89)]),
          ("Lessons 89–94 · Other vowel teams", [str(i) for i in range(89,95)]), ("Lessons 95–98 · Diphthongs & silent letters", [str(i) for i in range(95,99)]),
          ("Lessons 99–106 · Suffixes & prefixes", [str(i) for i in range(99,107)]), ("Lessons 107–110 · Suffix spelling changes", [str(i) for i in range(107,111)]),
          ("Lessons 111–118 · Low frequency spellings", [str(i) for i in range(111,119)]), ("Lessons 119–128 · Additional affixes", [str(i) for i in range(119,129)])]
def concept_of(id_):
    t = titles.get(id_, ''); m = re.match(r'^(Lesson\s+\S+(?:\s+AUS)?|Getting Ready Lesson \S+)\s*[·]?\s*(.*)$', t)
    return (m.group(1), m.group(2)) if m else (t, '')
rows = []
for gname, gids in groups:
    cards = ''
    for id_ in gids:
        if id_ not in titles: continue
        lesson, concept = concept_of(id_)
        cards += f'<div class="card"><div class="l">{esc(lesson.replace("Lesson ","").replace("Getting Ready Lesson ",""))}</div><div class="c">{esc(concept or lesson)}</div><div class="links"><a class="deck" href="decks/lesson_{id_}.html">▶ Slides</a><a class="guide" href="guide/lesson_{id_}.html">📖 Guide</a></div></div>'
    rows.append(f'<section><h2>{esc(gname)}</h2><div class="cards">{cards}</div></section>')
own_cards = ''.join(f'<div class="card"><div class="l">✎</div><div class="c">{esc(t)}</div><div class="links"><a class="deck" href="decks/{oid}.html">▶ Slides</a></div></div>' for oid, path, t in own if os.path.exists(path))
index = f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>UFLI Foundations · Interactive Lessons</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Didact+Gothic&display=swap" rel="stylesheet">
<style>
@font-face{{font-family:"Century Gothic";src:url("fonts/CenturyGothic.ttf");font-weight:400}} @font-face{{font-family:"Century Gothic";src:url("fonts/CenturyGothic-Bold.ttf");font-weight:700}}
body{{margin:0;font-family:"Century Gothic","Didact Gothic","Futura","Avenir Next",system-ui,sans-serif;background:#f3f5f8;color:#1c2430}}
header{{background:#1c2430;color:#e8edf3;padding:26px 34px}} header h1{{margin:0 0 4px;font-size:28px}} header p{{margin:0;color:#9fb0c3;font-size:14px}}
main{{max-width:1180px;margin:0 auto;padding:20px 24px 60px}}
.howto{{background:#fff;border-radius:14px;padding:16px 20px;margin:14px 0 22px;font-size:14px;line-height:1.6;box-shadow:0 2px 10px rgba(0,0,0,.05)}}
.howto kbd{{background:#e9edf3;border-radius:5px;padding:1px 7px;font-family:inherit}}
section h2{{font-size:17px;margin:22px 0 10px;color:#2c629f}}
.cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px}}
.card{{background:#fff;border-radius:12px;padding:12px 14px;box-shadow:0 2px 10px rgba(0,0,0,.05);display:flex;flex-direction:column;gap:6px}}
.card .l{{font-weight:700;color:#e05436;font-size:13px}} .card .c{{font-size:15px;font-weight:700;min-height:38px}}
.links{{display:flex;gap:8px;margin-top:auto}} .links a{{flex:1;text-align:center;text-decoration:none;font-size:13px;padding:6px 8px;border-radius:8px}}
.links .deck{{background:#2c629f;color:#fff}} .links .guide{{background:#e6f4f3;color:#1d6f6b}} .links a:hover{{filter:brightness(1.08)}}
</style></head><body>
<header><h1>UFLI Foundations · Interactive Lessons (Australian edition)</h1><p>Slides converted from the UFLI Foundations Toolbox (AUS) PowerPoints + reconstructed teacher's guides. Personal use.</p></header>
<main>
<div class="howto"><b>How to use · 사용법</b><br>
▶ <b>Slides</b>: open in Safari/Chrome, press <kbd>F</kbd> for full screen. <kbd>→</kbd> next (reveals hidden items first), <kbd>←</kbd> previous, <kbd>N</kbd> teacher notes &amp; lesson plan, <kbd>M</kbd> jump to a step, <kbd>S</kbd> read aloud, <kbd>E</kbd> example words for a grapheme, <kbd>?</kbd> all shortcuts.<br>
Click any word or sentence to hear it (Google NZ/AU voice via your Supabase function; falls back to the Mac voice). Grapheme cards in the Visual Drill open example words. Teal <b>HELPER</b> slides were added for the steps that the original slides leave to the manual (phonemic awareness, auditory drill, blending board, spelling, word work, dictation).<br>
📖 <b>Guide</b>: the lesson plan in the manual's format. Click a grapheme (Visual Drill) or a sound (Auditory Drill) for easy example words. Use Print for a PDF.</div>
{''.join(rows)}
<section><h2>Your own decks</h2><div class="cards">{own_cards}</div></section>
<p style="margin-top:34px;font-size:12px;color:#7c8a9c;line-height:1.5">Slides, images and passages are from the <a href="https://ufli.education.ufl.edu/foundations/toolbox-aus/" style="color:#2c629f">UFLI Foundations Toolbox (Australian edition)</a>, © University of Florida Literacy Institute, used and adapted under UFLI's terms (free for educational use with attribution; not for sale or commercial use). Teacher-guide text for most lessons is a reconstruction, not the official manual. Personal study site.</p>
</main></body></html>'''
open(os.path.join(OUT, 'index.html'), 'w').write(index)
print('built', len(titles), 'decks +', len(ids), 'guides into', OUT)
