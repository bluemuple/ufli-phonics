import sys, os, re, importlib, json
sys.path.insert(0, os.path.dirname(__file__))
from validate import decodable
from gpc import idx
S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def heart_words_until(lesson):
    """all irregular words taught up to and including lesson (from deck content)"""
    hw = set()
    L = idx(lesson)
    for f in os.listdir(S + '/content'):
        c = json.load(open(S + '/content/' + f))
        if c['id'] not in __import__('gpc').IDX: continue
        if idx(c['id']) <= L:
            for w in c['irregular_teach'] + c['irregular_review']:
                hw.add(w['word'].lower())
    hw |= {"the","a","i","is","and","to","of","as"}
    return hw
def words_in(s):
    return re.findall(r"[A-Za-z][A-Za-z'’]*", s)
def check(modname):
    m = importlib.import_module(modname)
    problems = []
    for lid, p in m.P.items():
        hw = heart_words_until(lid)
        cand = []
        if p.get('bd'): cand += [(w, 'bd') for w in words_in(p['bd']['chain'])]
        if p.get('ww') and p['ww'].get('chain'): cand += [(w, 'ww') for w in words_in(p['ww']['chain'])]
        for k in ('ido', 'wedo'):
            if p.get('spell'): cand += [(w, 'spell') for w in p['spell'].get(k, [])]
            if p.get('read'): cand += [(w, 'read') for w in p['read'].get(k, [])]
        for s in p.get('text_spell', []): cand += [(w, 'sent') for w in words_in(s)]
        for lbl, ch in p.get('chains', []): cand += [(w, 'chain') for w in words_in(ch)]
        for lbl, ws in p.get('lists', {}).items(): cand += [(w, 'list') for w in ws]
        for w, src in cand:
            if not decodable(w, lid, hw): problems.append((lid, src, w))
    return problems
if __name__ == '__main__':
    for mod in sys.argv[1:]:
        pr = check(mod)
        print(mod, "problems:", len(pr))
        for x in pr: print("  ", x)
