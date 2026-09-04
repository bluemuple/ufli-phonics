import re, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from gpc import GPC, idx, UNITS
def taught_units(lesson):
    L = idx(lesson)
    units = {g for (g,p,l) in GPC if idx(l) <= L and not g.startswith('-') and '_' not in g}
    # VCe patterns: allow final e when a_e etc. taught
    return units
def decodable(word, lesson, heart=()):
    w = word.lower().strip("*.,!?;:\"'()").replace("’","'")
    if not w or w in heart: return True
    if "'" in w: w = w.replace("'s","s").replace("n't","nt").replace("'","")
    units = taught_units(lesson)
    L = idx(lesson)
    vce = idx("54") <= L
    suf_es = idx("63") <= L; suf_ed = idx("64") <= L; suf_ing = idx("65") <= L; le = idx("75") <= L
    # strip common suffixes if taught
    stems = [w]
    if suf_ing and w.endswith("ing"): stems.append(w[:-3])
    if suf_ed and w.endswith("ed"): stems.append(w[:-2]); stems.append(w[:-1])
    if suf_es and w.endswith("es"): stems.append(w[:-2])
    if idx("20") <= L and w.endswith("s"): stems.append(w[:-1])
    if le and w.endswith("le"): stems.append(w[:-2])
    if idx("100") <= L and (w.endswith("er") or w.endswith("est")): stems.append(re.sub(r'(er|est)$','',w))
    if idx("101") <= L and w.endswith("ly"): stems.append(w[:-2])
    if idx("102") <= L: stems += [re.sub(r'(less|ful)$','',w)]
    if idx("103") <= L: stems += [re.sub(r'^(un|pre|re|dis)','',w)]
    if idx("119") <= L: stems += [re.sub(r'(tion|sion|ture|ist|ish|ness|ment|able|ible|y)$','',w)]
    for st in stems:
        if seg(st, units, vce, L): return True
    return False
def seg(w, units, vce, L):
    if not w: return True
    # VCe: consonant + e at end -> allowed if vce
    if vce and len(w) >= 3 and w[-1] == 'e' and w[-2] not in 'aeiou' and w[-3] in 'aeiou': 
        w = w[:-1]
    if vce and w.endswith('ve') : w = w[:-1]
    if idx("60") <= L and w.endswith('ce'): w = w[:-1]
    if idx("61") <= L and w.endswith('ge'): w = w[:-1]
    n = len(w); i = 0
    memo = {}
    def rec(i):
        if i == n: return True
        if i in memo: return memo[i]
        for u in UNITS:
            if w.startswith(u, i) and u in units:
                if rec(i+len(u)): memo[i] = True; return True
        memo[i] = False; return False
    return rec(0)
