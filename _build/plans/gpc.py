# Scope & sequence (AUS toolbox order) and grapheme-phoneme introduction table
SEQ = list("ABCDEFGHIJ") + [str(i) for i in range(1, 35)] + ["35a","35b","35c","36a","36b","37a","37b","38a","38b","39a","39b","40a","40b","41a","41b","41c"] \
    + [str(i) for i in range(42, 67)] + ["67a","67b"] + [str(i) for i in range(68, 78)] + ["77AUS","78","79","80","80AUS"] + [str(i) for i in range(81, 129)]
IDX = {k: i for i, k in enumerate(SEQ)}
def idx(l): return IDX[str(l)]

# (grapheme, phoneme, lesson introduced). Phoneme labels use UFLI/AUS notation.
GPC = [
 ("a","/ă/","1"),("a","/ā/","66"),("a","/ar/","77AUS"),("a","/ŏ/","94"),
 ("m","/m/","2"),("s","/s/","3"),("s","/z/","21"),("t","/t/","4"),("p","/p/","6"),("f","/f/","7"),
 ("i","/ĭ/","8"),("i","/ī/","66"),("n","/n/","9"),("o","/ŏ/","12"),("o","/ō/","66"),("d","/d/","13"),
 ("c","/k/","14"),("c","/s/","60"),("u","/ŭ/","15"),("u","/ū/","66"),("u","/yū/","66"),("u","/oo/","89"),
 ("g","/g/","16"),("g","/j/","61"),("b","/b/","17"),("e","/ĕ/","18"),("e","/ē/","66"),
 ("-s","/s/","20"),("-s","/z/","21"),("k","/k/","22"),("h","/h/","23"),("r","/r/","24"),("l","/l/","26"),("w","/w/","28"),
 ("j","/j/","29"),("y","/y/","30"),("y","/ī/","73"),("y","/ē/","74"),("x","/ks/","31"),("qu","/kw/","32"),("v","/v/","33"),("z","/z/","34"),
 ("ff","/f/","42"),("ll","/l/","42"),("ss","/s/","42"),("zz","/z/","42"),
 ("ck","/k/","44"),("sh","/sh/","45"),("th","/th/","46"),("th","/th/ (unvoiced)","47"),("ch","/ch/","48"),("ch","/sh/","118"),("ch","/k/","118"),
 ("wh","/w/","50"),("ph","/f/","50"),("ng","/ŋ/","51"),("nk","/ŋk/","52"),
 ("a_e","/ā/","54"),("i_e","/ī/","55"),("o_e","/ō/","56"),("e_e","/ē/","57"),("u_e","/ū/","58"),("u_e","/yū/","58"),("_ce","/s/","60"),("_ge","/j/","61"),
 ("-es","/ĕz/","63"),("-ed","/t/","64"),("-ed","/d/","64"),("-ed","/əd/","64"),("-ing","/ĭng/","65"),
 ("tch","/ch/","69"),("dge","/j/","70"),("-le","/əl/","75"),
 ("ar","/ar/","77"),("ar","/ə/","111"),("or","/or/","78"),("or","/er/","82"),("or","/ə/","111"),("ore","/or/","78"),
 ("er","/er/","80"),("er","/ə/","80AUS"),("ir","/er/","81"),("ur","/er/","81"),("our","/or/","73"),
 ("ai","/ā/","84"),("ay","/ā/","84"),("ee","/ē/","85"),("ea","/ē/","85"),("ea","/ĕ/","94"),("ea","/ā/","114"),("ey","/ē/","85"),("ey","/ā/","114"),
 ("oa","/ō/","86"),("ow","/ō/","86"),("ow","/ow/","96"),("oe","/ō/","86"),("ie","/ī/","87"),("igh","/ī/","87"),
 ("oo","/oo/","89"),("oo","/ū/","90"),("ew","/ū/","91"),("ew","/yū/","115"),("ui","/ū/","91"),("ue","/ū/","91"),("ue","/yū/","115"),("eu","/ū/","115"),("eu","/yū/","115"),
 ("au","/or/","93"),("aw","/or/","93"),("augh","/or/","93"),("oi","/oi/","95"),("oy","/oi/","95"),("ou","/ow/","96"),("ou","/ū/","115"),
 ("kn","/n/","98"),("wr","/r/","98"),("mb","/m/","98"),
 ("air","/air/","112"),("are","/air/","112"),("ear","/air/","112"),("ear","/ear/","113"),
 ("ei","/ā/","114"),("eigh","/ā/","114"),("aigh","/ā/","114"),("ough","/or/","116"),("ough","/ō/","116"),
 ("gn","/n/","118"),("gh","/g/","118"),
]
def sounds_at(g, lesson):
    """phonemes of grapheme g known at lesson (in intro order)"""
    L = idx(lesson)
    return [p for (gg, p, l) in GPC if gg == g and idx(l) <= L]
def auditory_from_visual(vd, lesson):
    """AD list: phoneme -> spellings, ordered by recency of graphemes in vd (most recent first)"""
    order = []
    for g in vd:
        for p in sounds_at(g, lesson):
            if p not in order: order.append(p)
    out = []
    for p in order:
        sp = [g for g in vd if p in sounds_at(g, lesson)]
        out.append((p, sp))
    return out
# spelling graphemes for the decodability validator (all single letters + multi-letter units)
UNITS = sorted({g for (g,_,_) in GPC if not g.startswith('-') and not g.endswith('_e') and '_' not in g} | set("abcdefghijklmnopqrstuvwxyz"), key=lambda s: -len(s))
