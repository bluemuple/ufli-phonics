#!/usr/bin/env python3
"""Parse a UFLI pptx into a JSON slide model + deduplicated asset files.
Usage: parse_pptx.py <file.pptx> <out.json> <assets_dir>
"""
import sys, os, re, json, zipfile, hashlib, colorsys
from lxml import etree

NS = {'p':'http://schemas.openxmlformats.org/presentationml/2006/main',
      'a':'http://schemas.openxmlformats.org/drawingml/2006/main',
      'r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
P, A, R = NS['p'], NS['a'], NS['r']
def q(ns, tag): return '{%s}%s' % (NS[ns], tag)

class Deck:
    def __init__(self, path, assets_dir):
        self.z = zipfile.ZipFile(path)
        self.names = set(self.z.namelist())
        self.assets_dir = assets_dir
        self.asset_index = {}
        pres = self.xml('ppt/presentation.xml')
        sz = pres.find('p:sldSz', NS)
        self.cx, self.cy = int(sz.get('cx')), int(sz.get('cy'))
        prels = self.rels('ppt/presentation.xml')
        self.slide_parts = ['ppt/' + prels[s.get(q('r','id'))][0] for s in pres.find('p:sldIdLst', NS)]
        self.theme = self.load_theme()
        self._layout_cache = {}

    def xml(self, part):
        return etree.fromstring(self.z.read(part))

    def rels(self, part):
        d, b = os.path.split(part); rp = f"{d}/_rels/{b}.rels"; out = {}
        if rp in self.names:
            for r in self.xml(rp):
                out[r.get('Id')] = (r.get('Target'), r.get('Type').split('/')[-1], r.get('TargetMode'))
        return out

    def resolve(self, part, target):
        return os.path.normpath(os.path.join(os.path.dirname(part), target)).replace('\\','/')

    # ---------- theme colours ----------
    def load_theme(self):
        theme = {}
        for n in self.names:
            if re.match(r'ppt/theme/theme\d+\.xml$', n):
                t = self.xml(n)
                cs = t.find('.//a:clrScheme', NS)
                if cs is None: continue
                for c in cs:
                    nm = etree.QName(c).localname
                    v = c.find('a:srgbClr', NS)
                    if v is not None: theme[nm] = v.get('val')
                    else:
                        v = c.find('a:sysClr', NS)
                        if v is not None: theme[nm] = v.get('lastClr', '000000')
                break
        # colour map from master
        self.clrmap = {'bg1':'lt1','tx1':'dk1','bg2':'lt2','tx2':'dk2'}
        for n in self.names:
            if re.match(r'ppt/slideMasters/slideMaster\d+\.xml$', n):
                m = self.xml(n).find('p:clrMap', NS)
                if m is not None:
                    for k, v in m.attrib.items(): self.clrmap[k] = v
                break
        return theme

    def color(self, el):
        """el: element containing a colour child (srgbClr/schemeClr/prstClr/sysClr). returns css rgba or None"""
        if el is None: return None
        c = None
        for ch in el:
            tag = etree.QName(ch).localname
            if tag == 'srgbClr': c = ch.get('val')
            elif tag == 'schemeClr':
                v = ch.get('val'); v = self.clrmap.get(v, v); c = self.theme.get(v, '000000')
            elif tag == 'sysClr': c = ch.get('lastClr', '000000')
            elif tag == 'prstClr':
                c = {'black':'000000','white':'FFFFFF','red':'FF0000','blue':'0000FF','green':'00FF00'}.get(ch.get('val'), '000000')
            else: continue
            # modifiers
            r, g, b = int(c[0:2],16)/255, int(c[2:4],16)/255, int(c[4:6],16)/255
            alpha = 1.0
            h, l, s = colorsys.rgb_to_hls(r, g, b)
            for mod in ch:
                mt = etree.QName(mod).localname; val = mod.get('val')
                if val is None: continue
                val = int(val)/100000
                if mt == 'lumMod': l = l*val
                elif mt == 'lumOff': l = l+val
                elif mt == 'alpha': alpha = val
                elif mt == 'shade': l = l*val
                elif mt == 'tint': l = l + (1-l)*(1-val)
            l = max(0, min(1, l))
            r, g, b = colorsys.hls_to_rgb(h, l, s)
            css = '#%02x%02x%02x' % (round(r*255), round(g*255), round(b*255))
            if alpha < 1: css = 'rgba(%d,%d,%d,%.2f)' % (round(r*255), round(g*255), round(b*255), alpha)
            return css
        return None

    def fill(self, prop_el):
        """returns fill spec from spPr/rPr-like element: {'type':'solid','color':..} | {'type':'none'} | {'type':'grad', colors} | None (inherit)"""
        if prop_el is None: return None
        for ch in prop_el:
            tag = etree.QName(ch).localname
            if tag == 'solidFill': return {'type':'solid', 'color': self.color(ch)}
            if tag == 'noFill': return {'type':'none'}
            if tag == 'gradFill':
                cols = [self.color(gs) for gs in ch.findall('.//a:gs', NS)]
                return {'type':'grad', 'colors': [c for c in cols if c]}
            if tag == 'blipFill':
                blip = ch.find('a:blip', NS)
                return {'type':'img', 'rid': blip.get(q('r','embed')) if blip is not None else None}
        return None

    def line(self, spPr):
        ln = spPr.find('a:ln', NS) if spPr is not None else None
        if ln is None: return None
        w = int(ln.get('w', '9525'))/12700  # pt
        f = self.fill(ln)
        dash = ln.find('a:prstDash', NS)
        head = ln.find('a:headEnd', NS); tail = ln.find('a:tailEnd', NS)
        return {'w': round(w,2), 'fill': f, 'dash': dash.get('val') if dash is not None else None,
                'head': head.get('type') if head is not None else None, 'tail': tail.get('type') if tail is not None else None}

    # ---------- assets ----------
    def save_asset(self, part, rid, rels=None):
        rels = rels or self.rels(part)
        if rid not in rels: return None
        tgt, typ, mode = rels[rid]
        if mode == 'External': return None
        mpart = self.resolve(part, tgt)
        if mpart not in self.names: return None
        data = self.z.read(mpart)
        h = hashlib.md5(data).hexdigest()[:12]
        ext = os.path.splitext(mpart)[1].lower()
        fn = f"{h}{ext}"
        outp = os.path.join(self.assets_dir, fn)
        if not os.path.exists(outp):
            with open(outp, 'wb') as f: f.write(data)
        return fn

    # ---------- geometry ----------
    def xfrm(self, el):
        x = el.find('a:xfrm', NS)
        if x is None:
            x = el.find('.//a:xfrm', NS)
        if x is None: return None
        off = x.find('a:off', NS); ext = x.find('a:ext', NS)
        if off is None or ext is None: return None
        g = {'x': int(off.get('x')), 'y': int(off.get('y')), 'w': int(ext.get('cx')), 'h': int(ext.get('cy')),
             'rot': int(x.get('rot', '0'))/60000, 'flipH': x.get('flipH') == '1', 'flipV': x.get('flipV') == '1'}
        cho = x.find('a:chOff', NS); che = x.find('a:chExt', NS)
        if cho is not None and che is not None:
            g['chx'], g['chy'], g['chw'], g['chh'] = int(cho.get('x')), int(cho.get('y')), int(che.get('cx')), int(che.get('cy'))
        return g

    # ---------- text ----------
    def text_body(self, txBody, fontscale_hint=None):
        if txBody is None: return None
        bodyPr = txBody.find('a:bodyPr', NS)
        body = {'anchor': 'ctr', 'wrap': 'square', 'ins': [91440, 45720, 91440, 45720], 'fontScale': 1.0, 'lnRed': 0.0, 'paras': []}
        if bodyPr is not None:
            body['anchor'] = bodyPr.get('anchor', 't')
            body['wrap'] = bodyPr.get('wrap', 'square')
            body['ins'] = [int(bodyPr.get('lIns', 91440)), int(bodyPr.get('tIns', 45720)), int(bodyPr.get('rIns', 91440)), int(bodyPr.get('bIns', 45720))]
            na = bodyPr.find('a:normAutofit', NS)
            if na is not None:
                body['fontScale'] = int(na.get('fontScale', '100000'))/100000
                body['lnRed'] = int(na.get('lnSpcReduction', '0'))/100000
            if bodyPr.find('a:spAutoFit', NS) is not None: body['spAutoFit'] = True
            if bodyPr.get('vert') not in (None, 'horz'): body['vert'] = bodyPr.get('vert')
        # list style defaults (lvl1pPr etc.)
        lst = txBody.find('a:lstStyle', NS)
        lvl_defaults = {}
        if lst is not None:
            for lv in lst:
                m = re.match(r'lvl(\d)pPr', etree.QName(lv).localname)
                if m:
                    d = {}
                    dr = lv.find('a:defRPr', NS)
                    if dr is not None: d['rpr'] = self.run_props(dr)
                    d['algn'] = lv.get('algn')
                    lvl_defaults[int(m.group(1))] = d
        for p in txBody.findall('a:p', NS):
            para = {'runs': [], 'algn': None, 'lnSpc': None, 'spcBef': 0, 'spcAft': 0, 'bullet': None, 'indent': 0, 'marL': 0, 'lvl': 0}
            pPr = p.find('a:pPr', NS)
            if pPr is not None:
                para['algn'] = pPr.get('algn')
                para['lvl'] = int(pPr.get('lvl', '0'))
                para['indent'] = int(pPr.get('indent', '0')); para['marL'] = int(pPr.get('marL', '0'))
                ls = pPr.find('a:lnSpc', NS)
                if ls is not None:
                    pct = ls.find('a:spcPct', NS); pts = ls.find('a:spcPts', NS)
                    if pct is not None: para['lnSpc'] = {'pct': int(pct.get('val'))/100000}
                    elif pts is not None: para['lnSpc'] = {'pts': int(pts.get('val'))/100}
                for key, tag in (('spcBef','a:spcBef'), ('spcAft','a:spcAft')):
                    e = pPr.find(tag, NS)
                    if e is not None:
                        pts = e.find('a:spcPts', NS)
                        if pts is not None: para[key] = int(pts.get('val'))/100
                if pPr.find('a:buNone', NS) is not None: para['bullet'] = None
                else:
                    bc = pPr.find('a:buChar', NS); ba = pPr.find('a:buAutoNum', NS)
                    if bc is not None: para['bullet'] = bc.get('char')
                    elif ba is not None: para['bullet'] = 'auto:' + ba.get('type', 'arabicPeriod')
            lvd = lvl_defaults.get(para['lvl']+1, {})
            if para['algn'] is None: para['algn'] = lvd.get('algn')
            endPr = p.find('a:endParaRPr', NS)
            for ch in p:
                tag = etree.QName(ch).localname
                if tag == 'r':
                    t = ch.find('a:t', NS)
                    rp = self.run_props(ch.find('a:rPr', NS), lvd.get('rpr'))
                    para['runs'].append({'t': t.text if t is not None and t.text else '', **rp})
                elif tag == 'br':
                    para['runs'].append({'t': '\n', **self.run_props(ch.find('a:rPr', NS), lvd.get('rpr'))})
                elif tag == 'fld':
                    t = ch.find('a:t', NS)
                    rp = self.run_props(ch.find('a:rPr', NS), lvd.get('rpr'))
                    para['runs'].append({'t': t.text if t is not None and t.text else '', **rp})
            if not para['runs'] and endPr is not None:
                para['endsz'] = self.run_props(endPr).get('sz')
            body['paras'].append(para)
        return body

    def run_props(self, rPr, defaults=None):
        d = dict(defaults or {})
        if rPr is None: return d
        if rPr.get('sz'): d['sz'] = int(rPr.get('sz'))/100
        if rPr.get('b') is not None: d['b'] = rPr.get('b') == '1'
        if rPr.get('i') is not None: d['i'] = rPr.get('i') == '1'
        if rPr.get('u') not in (None, 'none'): d['u'] = True
        if rPr.get('strike') not in (None, 'noStrike'): d['strike'] = True
        if rPr.get('baseline'): d['baseline'] = int(rPr.get('baseline'))/1000
        if rPr.get('spc'): d['spc'] = int(rPr.get('spc'))/100
        if rPr.get('cap') == 'all': d['caps'] = True
        f = self.fill(rPr)
        if f and f.get('type') == 'solid': d['color'] = f['color']
        lat = rPr.find('a:latin', NS)
        if lat is not None and lat.get('typeface'): d['font'] = lat.get('typeface')
        hl = rPr.find('a:highlight', NS)
        if hl is not None: d['hl'] = self.color(hl)
        return d

    # ---------- shapes ----------
    def parse_shapes(self, tree, part, rels, base=None, out=None, ph_lookup=None):
        """tree: spTree element. base: group transform mapping or None."""
        out = out if out is not None else []
        for el in tree:
            tag = etree.QName(el).localname
            if tag in ('nvGrpSpPr', 'grpSpPr', 'extLst'): continue
            if tag == 'grpSp':
                g = self.xfrm(el.find('p:grpSpPr', NS))
                if g is None: continue
                # compose transform: map child coords -> parent coords
                def make_map(g, base):
                    def mp(x, y, w, h):
                        sx = g['w']/g['chw'] if g.get('chw') else 1.0
                        sy = g['h']/g['chh'] if g.get('chh') else 1.0
                        nx = g['x'] + (x - g.get('chx', 0))*sx
                        ny = g['y'] + (y - g.get('chy', 0))*sy
                        nw, nh = w*sx, h*sy
                        if base: return base(nx, ny, nw, nh)
                        return nx, ny, nw, nh
                    return mp
                self.parse_shapes(el, part, rels, make_map(g, base), out, ph_lookup)
                continue
            sh = self.parse_shape(el, tag, part, rels, base, ph_lookup)
            if sh: out.append(sh)
        return out

    def parse_shape(self, el, tag, part, rels, base, ph_lookup):
        nv = el.find('.//p:cNvPr', NS)
        sid = nv.get('id') if nv is not None else None
        name = nv.get('name', '') if nv is not None else ''
        hidden = nv is not None and nv.get('hidden') == '1'
        sh = {'id': sid, 'name': name, 'kind': tag}
        if hidden: sh['hidden'] = True
        spPr = el.find('p:spPr', NS)
        if spPr is None and tag == 'graphicFrame': spPr = None
        g = self.xfrm(spPr) if spPr is not None else self.xfrm(el)
        ph = el.find('.//p:nvPr/p:ph', NS)
        if ph is not None:
            sh['ph'] = {'type': ph.get('type', 'body'), 'idx': ph.get('idx')}
            if g is None and ph_lookup:
                g = ph_lookup(sh['ph'])
        if g is None:
            if tag == 'graphicFrame':
                x = el.find('p:xfrm', NS)
                if x is not None:
                    off = x.find('a:off', NS); ext = x.find('a:ext', NS)
                    g = {'x': int(off.get('x')), 'y': int(off.get('y')), 'w': int(ext.get('cx')), 'h': int(ext.get('cy')), 'rot': 0, 'flipH': False, 'flipV': False}
        if g is None:
            return None
        x, y, w, h = g['x'], g['y'], g['w'], g['h']
        if base: x, y, w, h = base(x, y, w, h)
        sh['x'] = round(100*x/self.cx, 3); sh['y'] = round(100*y/self.cy, 3)
        sh['w'] = round(100*w/self.cx, 3); sh['h'] = round(100*h/self.cy, 3)
        if g.get('rot'): sh['rot'] = g['rot']
        if g.get('flipH'): sh['flipH'] = True
        if g.get('flipV'): sh['flipV'] = True
        if tag in ('sp', 'cxnSp'):
            geom = spPr.find('a:prstGeom', NS) if spPr is not None else None
            sh['prst'] = geom.get('prst') if geom is not None else ('custom' if spPr is not None and spPr.find('a:custGeom', NS) is not None else 'rect')
            if geom is not None:
                avs = [(gd.get('name'), gd.get('fmla')) for gd in geom.findall('.//a:gd', NS)]
                if avs: sh['adj'] = avs
            f = self.fill(spPr)
            sh['fill'] = f
            sh['line'] = self.line(spPr)
            # style refs (when fill/line inherit from style)
            style = el.find('p:style', NS)
            if style is not None:
                fr = style.find('a:fillRef', NS); lr = style.find('a:lnRef', NS); fontr = style.find('a:fontRef', NS)
                if f is None and fr is not None and int(fr.get('idx', '0')) > 0:
                    c = self.color(fr)
                    if c: sh['fill'] = {'type': 'solid', 'color': c}
                if sh['line'] is None and lr is not None and int(lr.get('idx', '0')) > 0:
                    c = self.color(lr)
                    if c: sh['line'] = {'w': 0.75, 'fill': {'type': 'solid', 'color': c}, 'dash': None, 'head': None, 'tail': None}
                if fontr is not None:
                    c = self.color(fontr)
                    if c: sh['styleFontColor'] = c
            tx = el.find('p:txBody', NS)
            if tx is not None:
                body = self.text_body(tx)
                if body and (any(r['t'] for p in body['paras'] for r in p['runs'])):
                    sh['text'] = body
        elif tag == 'pic':
            blip = el.find('.//a:blip', NS)
            if blip is not None:
                rid = blip.get(q('r','embed'))
                sh['img'] = self.save_asset(part, rid, rels)
                src = el.find('.//a:srcRect', NS)
                if src is not None and any(src.get(k) for k in ('l','t','r','b')):
                    sh['crop'] = {k: int(src.get(k, '0'))/100000 for k in ('l','t','r','b')}
                # alpha
                am = blip.find('a:alphaModFix', NS)
                if am is not None: sh['alpha'] = int(am.get('amt', '100000'))/100000
            geom = spPr.find('a:prstGeom', NS) if spPr is not None else None
            if geom is not None and geom.get('prst') not in ('rect', None): sh['prst'] = geom.get('prst')
            sh['line'] = self.line(spPr)
            if el.find('.//p:nvPr/a:videoFile', NS) is not None or el.find('.//p:nvPr/a:audioFile', NS) is not None:
                sh['media'] = True
        elif tag == 'graphicFrame':
            tbl = el.find('.//a:tbl', NS)
            if tbl is not None:
                sh['table'] = self.parse_table(tbl)
            else:
                # could be chart/diagram/ole - try to find an embedded image fallback
                sh['unsupported'] = True
        else:
            return None
        return sh

    def parse_table(self, tbl):
        cols = [int(gc.get('w')) for gc in tbl.findall('a:tblGrid/a:gridCol', NS)]
        rows = []
        for tr in tbl.findall('a:tr', NS):
            row = {'h': int(tr.get('h', '0')), 'cells': []}
            for tc in tr.findall('a:tc', NS):
                cell = {'text': self.text_body(tc.find('a:txBody', NS))}
                tcPr = tc.find('a:tcPr', NS)
                if tcPr is not None:
                    cell['fill'] = self.fill(tcPr)
                    cell['anchor'] = tcPr.get('anchor')
                    cell['ins'] = [int(tcPr.get('marL', 91440)), int(tcPr.get('marT', 45720)), int(tcPr.get('marR', 91440)), int(tcPr.get('marB', 45720))]
                    borders = {}
                    for side in ('lnL','lnR','lnT','lnB'):
                        ln = tcPr.find('a:'+side, NS)
                        if ln is not None:
                            borders[side] = {'w': int(ln.get('w', '12700'))/12700, 'fill': self.fill(ln)}
                    if borders: cell['borders'] = borders
                if tc.get('gridSpan'): cell['colspan'] = int(tc.get('gridSpan'))
                if tc.get('rowSpan'): cell['rowspan'] = int(tc.get('rowSpan'))
                if tc.get('hMerge') == '1' or tc.get('vMerge') == '1': cell['merged'] = True
                row['cells'].append(cell)
            rows.append(row)
        tblPr = tbl.find('a:tblPr', NS)
        style = None
        if tblPr is not None:
            sid = tblPr.find('a:tableStyleId', NS)
            style = {'firstRow': tblPr.get('firstRow') == '1', 'bandRow': tblPr.get('bandRow') == '1', 'id': sid.text if sid is not None else None}
        return {'cols': cols, 'rows': rows, 'style': style}

    # ---------- background ----------
    def background(self, tree, part, rels):
        bg = tree.find('.//p:cSld/p:bg', NS)
        if bg is None: return None
        bgPr = bg.find('p:bgPr', NS)
        if bgPr is not None:
            f = self.fill(bgPr)
            if f and f['type'] == 'img':
                return {'type': 'img', 'img': self.save_asset(part, f['rid'], rels)}
            return f
        ref = bg.find('p:bgRef', NS)
        if ref is not None:
            c = self.color(ref)
            return {'type': 'solid', 'color': c or '#ffffff'}
        return None

    # ---------- layouts ----------
    def layout_info(self, laypart):
        if laypart in self._layout_cache: return self._layout_cache[laypart]
        t = self.xml(laypart); rels = self.rels(laypart)
        name = t.find('.//p:cSld', NS).get('name')
        tree = t.find('.//p:spTree', NS)
        # placeholders for lookup
        phs = {}
        for el in tree:
            ph = el.find('.//p:nvPr/p:ph', NS)
            if ph is not None:
                g = self.xfrm(el.find('p:spPr', NS))
                if g: phs[(ph.get('type', 'body'), ph.get('idx'))] = g
        masterpart = None
        for v in rels.values():
            if v[1] == 'slideMaster': masterpart = self.resolve(laypart, v[0])
        mphs = {}
        if masterpart:
            mt = self.xml(masterpart)
            for el in mt.find('.//p:spTree', NS):
                ph = el.find('.//p:nvPr/p:ph', NS)
                if ph is not None:
                    g = self.xfrm(el.find('p:spPr', NS))
                    if g: mphs[(ph.get('type', 'body'), ph.get('idx'))] = g
        def lookup(phd):
            key = (phd['type'], phd['idx'])
            for d in (phs, mphs):
                if key in d: return d[key]
                for k, v in d.items():
                    if k[0] == phd['type']: return v
                for k, v in d.items():
                    if k[1] == phd['idx'] and phd['idx'] is not None: return v
            return None
        # non-placeholder shapes on layout (logos, decorative), with showMasterSp consideration
        shapes = [s for s in self.parse_shapes(tree, laypart, rels) if 'ph' not in s]
        bg = self.background(t, laypart, rels)
        info = {'name': name, 'shapes': shapes, 'bg': bg, 'lookup': lookup}
        self._layout_cache[laypart] = info
        return info

    # ---------- animations ----------
    def animations(self, tree):
        timing = tree.find('p:timing', NS)
        if timing is None: return []
        steps = []
        seq = timing.find('.//p:seq', NS)
        if seq is None: return []
        main = seq.find('p:cTn/p:childTnLst', NS)
        if main is None: return []
        for par in main.findall('p:par', NS):
            step = []
            for ctn in par.iter(q('p','cTn')):
                pc = ctn.get('presetClass')
                if not pc: continue
                tgt = ctn.find('.//p:spTgt', NS)
                if tgt is None: continue
                act = {'spid': tgt.get('spid'), 'cls': pc, 'preset': ctn.get('presetID'), 'node': ctn.get('nodeType')}
                prg = tgt.find('.//p:pRg', NS)
                if prg is not None: act['para'] = [int(prg.get('st')), int(prg.get('end'))]
                step.append(act)
            if step: steps.append(step)
        return steps

    # ---------- notes ----------
    def notes(self, part, rels):
        for v in rels.values():
            if v[1] == 'notesSlide':
                npart = self.resolve(part, v[0])
                if npart in self.names:
                    t = self.xml(npart)
                    texts = []
                    for sp in t.iter(q('p','sp')):
                        ph = sp.find('.//p:nvPr/p:ph', NS)
                        if ph is not None and ph.get('type') == 'body':
                            for p in sp.findall('.//a:p', NS):
                                texts.append(''.join(x.text or '' for x in p.iter(q('a','t'))))
                    return '\n'.join(texts).strip()
        return ''

    # ---------- slides ----------
    def parse(self):
        slides = []
        for idx, part in enumerate(self.slide_parts, 1):
            t = self.xml(part); rels = self.rels(part)
            laypart = None
            for v in rels.values():
                if v[1] == 'slideLayout': laypart = self.resolve(part, v[0])
            lay = self.layout_info(laypart) if laypart else {'name': '', 'shapes': [], 'bg': None, 'lookup': None}
            tree = t.find('.//p:spTree', NS)
            shapes = self.parse_shapes(tree, part, rels, None, None, lay['lookup'])
            bg = self.background(t, part, rels) or lay['bg']
            show_master = t.find('p:cSld', NS).get('showMasterSp', '1') != '0'
            slide = {'n': idx, 'layout': lay['name'], 'bg': bg, 'layoutShapes': lay['shapes'] if show_master else [],
                     'shapes': shapes, 'anims': self.animations(t), 'notes': self.notes(part, rels)}
            if t.get('show') == '0': slide['hidden'] = True
            slides.append(slide)
        return {'cx': self.cx, 'cy': self.cy, 'slides': slides}

if __name__ == '__main__':
    src, out, assets = sys.argv[1:4]
    os.makedirs(assets, exist_ok=True)
    d = Deck(src, assets)
    model = d.parse()
    model['source'] = os.path.basename(src)
    with open(out, 'w') as f: json.dump(model, f, ensure_ascii=False)
    n = len(model['slides'])
    print(f"{os.path.basename(src)}: {n} slides, {sum(len(s['shapes']) for s in model['slides'])} shapes, {sum(len(s['anims']) for s in model['slides'])} anim steps")
