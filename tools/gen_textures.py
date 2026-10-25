"""Generates creativeforge item textures (16x16, Create-style: darker edge, top-left light, flat tones, no AA).

Palettes are taken from Create's own item textures (see PAL comments). Usage:
    python3 tools/gen_textures.py [--preview DIR]
Writes src/main/resources/assets/creativeforge/textures/item/*.png; --preview also writes 16x upscaled copies.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import png

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src/main/resources/assets/creativeforge/textures/item')

def hx(s): return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)

# tone ramps dark -> light: [edge, shadow, mid, light, highlight]
MAT = {
    'B': [hx(c) for c in ('602f24', '995a3d', 'd3a155', 'fbcc68', 'fff9c7')],  # brass_sheet / brass_ingot
    'A': [hx(c) for c in ('2b3635', '4a5451', '6d7d73', 'a9afa1', 'c9caba')],  # andesite_alloy
    'Z': [hx(c) for c in ('213b3f', '506d63', '788273', 'a5c0a0', 'd6ffdc')],  # zinc_ingot
    'S': [hx(c) for c in ('140e2a', '2e2742', '4d4861', '605e6b', '665d78')],  # shadow_steel
    'T': [hx(c) for c in ('2e2742', '575366', '665d78', 'a2a98c', 'd5dec8')],  # shadow_steel top face, refined_radiance sheen
    'E': [hx(c) for c in ('140e2a', '1c162c', '2e2742', '38304d', '4d4861')],  # shadow_steel, dark end face
    'Q': [hx(c) for c in ('741a41', '913660', 'c83264', 'f74572', 'ff8585')],  # polished_rose_quartz
    'G': [hx(c) for c in ('353535', '5c6060', '878787', 'b0b0b0', 'd8d8d8')],  # electron_tube / iron_sheet metal
}
FIX = {
    'h': hx('fffef5'), 'w': hx('fffff6'), 'r': hx('d5dec8'),            # refined_radiance whites
    'y': hx('fbcc68'), 'l': hx('ffeb94'),                                # honey gold (brass highlights)
    'p': hx('f74572'), 'q': hx('ffbfa4'), 'k': hx('ff8585'),            # rose quartz glow
    'o': hx('ff8f00'), 'Y': hx('ffd800'),                                # transmitter accents
    'c': hx('d6ffdc'), 'C': hx('b9e9c1'), 'z': hx('a5c0a0'),            # zinc cool glow
    'u': hx('4a5451'), 'v': hx('5e6963'),                                # andesite, unlit cells
    'g': hx('878787'), 'x': hx('5c6060'),                                # unlit glass
    '1': hx('7f7f7f'), '2': hx('b7b7b7'), '3': hx('e4e4e4'),            # chromatic_compound greys
}
EMPTY = (0, 0, 0, 0)

def render(rows):
    assert len(rows) == 16 and all(len(r) == 16 for r in rows), rows
    at = lambda x, y: rows[y][x] if 0 <= x < 16 and 0 <= y < 16 else '.'
    # transparent pixels reachable from the border are "outside"; the rest are holes, shaded by the way they face
    outside, todo = set(), [(x, y) for x in range(16) for y in (0, 15)] + [(x, y) for y in range(16) for x in (0, 15)]
    while todo:
        x, y = todo.pop()
        if (x, y) in outside or not (0 <= x < 16 and 0 <= y < 16) or at(x, y) != '.': continue
        outside.add((x, y)); todo += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    out = [[EMPTY] * 16 for _ in range(16)]
    for y in range(16):
        for x in range(16):
            c = at(x, y)
            if c == '.': continue
            if c in FIX: out[y][x] = FIX[c]; continue
            t = MAT[c]
            edge = lambda dx, dy: (x + dx, y + dy) in outside or not (0 <= x + dx < 16 and 0 <= y + dy < 16)
            hole = lambda dx, dy: at(x + dx, y + dy) == '.' and not edge(dx, dy)
            other = lambda dx, dy: at(x + dx, y + dy) not in ('.', c)
            if edge(0, 1) or edge(1, 0): v = 0
            elif edge(0, -1) or edge(-1, 0): v = 1
            elif hole(0, 1) or hole(1, 0): v = 1
            elif other(0, 1) or other(1, 0): v = 2  # seam against another part: soft shadow only
            elif hole(0, -1) or hole(-1, 0) or other(0, -1) or other(-1, 0): v = 3
            else:
                tl = at(x, y - 1) != c or at(x, y - 2) == '.', at(x - 1, y) != c or at(x - 2, y) == '.'
                br = at(x, y + 2) == '.' or at(x + 2, y) == '.'
                v = 4 if all(tl) else 3 if any(tl) else 1 if br else 2
            out[y][x] = t[v]
    return out

def orb(cx, cy, r, mat, keep=lambda x, y: True):
    """Sphere lit from top-left, quantized to the ramp (flat bands, no AA)."""
    rows = [['.'] * 16 for _ in range(16)]
    px = [[EMPTY] * 16 for _ in range(16)]
    lx, ly, lz = -0.55, -0.55, 0.63
    for y in range(16):
        for x in range(16):
            dx, dy = (x + 0.5 - cx) / r, (y + 0.5 - cy) / r
            d2 = dx * dx + dy * dy
            if d2 > 1 or not keep(x, y): continue
            rows[y][x] = 'S'
            nz = math.sqrt(1 - d2)
            lum = dx * lx + dy * ly + nz * lz
            px[y][x] = MAT[mat][0] if d2 > 0.8 and lum < 0.35 else MAT[mat][min(4, max(1, int((lum + 0.2) * 3.4)))]
    return rows, px

def overlay(px, rows):
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c in FIX: px[y][x] = FIX[c]
    return px

# ---- designs ----------------------------------------------------------------------------------------------------

def lattice(built=lambda x, y: True):
    # brass grid (2px bars) riveted onto an andesite backing plate; unbuilt area is bare plate
    rows = []
    for y in range(16):
        r = ''
        for x in range(16):
            if not (1 <= x <= 14 and 1 <= y <= 14): r += '.'
            elif not built(x, y): r += 'A'
            elif (x - 1) % 4 < 2 or (y - 1) % 4 < 2:
                r += 'l' if (x, y) in ((5, 5), (9, 9), (5, 9), (9, 5)) else 'B'
            else: r += 'u'
        rows.append(r)
    return rows

TUBE = [
    '................',
    '......QQQQ......',
    '.....QqqqqQ.....',
    '....QqlhhlkQ....',
    '....QqlhhlqQ....',
    '....QqyllypQ....',
    '....QqpyypkQ....',
    '....QqkppkqQ....',
    '....QQqkkqQQ....',
    '...BBBBBBBBBB...',
    '...BBoBBBBYBB...',
    '....BBBBBBBB....',
    '.....Z.ZZ.Z.....',
    '.....Z.ZZ.Z.....',
    '................',
    '................',
]

def dim_tube():
    # glass and brass base fitted, no glow yet, zinc pins missing
    lit = {'h': 'g', 'l': 'g', 'y': 'x', 'p': 'x', 'k': 'g', 'q': 'g', 'o': 'B', 'Y': 'B'}
    rows = [''.join(lit.get(c, c) for c in r) for r in TUBE]
    rows[12] = rows[13] = '................'
    return rows

INGOT = [
    '................',
    '................',
    '................',
    '......TTTTTTT...',
    '.....TwwrTTTTT..',
    '....TwrTTTTTTTT.',
    '...TrTTTTTTTTTE.',
    '..TTTTTTTTTTTEE.',
    '..SSSSSSSSSSSEE.',
    '.SSSSSSSSSSSSEE.',
    '.SSSSSSSSSSSSE..',
    '.SSSSSSSSSSSS...',
    '..SSSSSSSSSSS...',
    '................',
    '................',
    '................',
]

def matrix(lit=lambda cx, cy: True):
    # denser than the lattice: andesite frame (thicker bottom/right), 1px brass bars, 4x4 grid of 2x2 zinc-glow cells
    cell = lambda v: (v - 2) // 3 if 2 <= v <= 12 and (v - 2) % 3 < 2 else None
    rows = []
    for y in range(16):
        r = ''
        for x in range(16):
            cx, cy = cell(x), cell(y)
            if not (1 <= x <= 14 and 1 <= y <= 14): r += '.'
            elif x in (1, 13, 14) or y in (1, 13, 14): r += 'A'
            elif cx is None or cy is None: r += 'B'
            elif not lit(cx, cy): r += 'v'
            else:
                inner = (cx in (1, 2)) + (cy in (1, 2))
                r += 'czC'[2 - inner] if inner < 2 else 'h'
        rows.append(r)
    return rows

def core(complete=True):
    # dark shadow-steel orb, brass equator band, bright chromatic heart
    keep = (lambda x, y: True) if complete else (lambda x, y: x - y < 3)
    rows, px = orb(8, 8, 6.4, 'S', keep)
    for y in range(16):
        for x in range(16):
            if px[y][x] != EMPTY and y in (8, 9):
                px[y][x] = MAT['B'][3 if y == 8 else 1]
            if px[y][x] != EMPTY and y in (7, 10) and px[y][x] in (MAT['S'][0],):
                px[y][x] = MAT['B'][0]
    center = (['w', 'h'] if complete else ['2', '3'])
    flecks = {(5, 6): 'p', (10, 5): 'y', (11, 10): 'o', (5, 11): 'k', (9, 11): 'Y', (5, 9): 'c', (10, 7): 'C'}
    for y in range(16):
        for x in range(16):
            d = math.hypot(x + 0.5 - 8, y + 0.5 - 8)
            if d < 1.6: px[y][x] = FIX[center[1]]
            elif d < 2.7: px[y][x] = FIX[center[0]]
            elif (x, y) in flecks and complete: px[y][x] = FIX[flecks[(x, y)]]
    if not complete:  # shell still open on one side: chromatic compound shows through
        for y in range(16):
            for x in range(16):
                d = math.hypot(x + 0.5 - 8, y + 0.5 - 8)
                if not keep(x, y) and 2.7 <= d < 5.6: px[y][x] = FIX['3' if d < 3.8 else '2' if d < 4.8 else '1']
    return px

GEM = [  # polished rose quartz turning into chromatic compound: pink gem, lower-right already greyed
    '................',
    '................',
    '......QQQQ......',
    '.....QqkkqQ.....',
    '....QqkppkqQ....',
    '...QqkpppkQQ1...',
    '...QkppppQ1221..',
    '..QQkppQ122321..',
    '..QQppQ1233321..',
    '...QQQ12333221..',
    '....Q1233221....',
    '.....122221.....',
    '......1111......',
    '................',
    '................',
    '................',
]

TEXTURES = {
    'incomplete_chromatic_compound': lambda: render(GEM),
    'resonant_lattice': lambda: render(lattice()),
    'incomplete_resonant_lattice': lambda: render(lattice(built=lambda x, y: y < 9)),
    'quantum_circuit': lambda: render(TUBE),
    'incomplete_quantum_circuit': lambda: render(dim_tube()),
    'flux_alloy': lambda: render(INGOT),
    'flux_matrix': lambda: render(matrix()),
    'incomplete_flux_matrix': lambda: render(matrix(lit=lambda cx, cy: cx == 0 or (cx == 1 and cy < 2))),
    'singularity_core': lambda: core(),
    'incomplete_singularity_core': lambda: core(complete=False),
}

# ---- guide book art -------------------------------------------------------------------------------------------
RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src/main/resources')
GUI = os.path.join(RES, 'assets/creativeforge/textures/gui/guide')
GLYPH = {  # 5x7 pixel letters for Create ingredients in the recipe diagrams
    'V': ['X...X', 'X...X', 'X...X', 'X...X', '.X.X.', '.X.X.', '..X..'],
    'T': ['XXXXX', '..X..', '..X..', '..X..', '..X..', '..X..', '..X..'],
    'B': ['XXXX.', 'X...X', 'X...X', 'XXXX.', 'X...X', 'X...X', 'XXXX.'],
    'C': ['.XXX.', 'X...X', 'X....', 'X....', 'X....', 'X...X', '.XXX.'],
    'R': ['XXXX.', 'X...X', 'X...X', 'XXXX.', 'X.X..', 'X..X.', 'X...X'],
    'S': ['.XXXX', 'X....', 'X....', '.XXX.', '....X', '....X', 'XXXX.'],
}
LETTER_BG = {'V': 'b57849', 'T': '6d7d73', 'B': 'c83264', 'C': 'a9afa1', 'R': 'd5dec8', 'S': '38304d'}
ICON = {'creativeforge:singularity_core': 'singularity_core', 'creativeforge:flux_matrix': 'flux_matrix',
        'creativeforge:quantum_circuit': 'quantum_circuit', 'creativeforge:resonant_lattice': 'resonant_lattice'}

def canvas(w, h, c=EMPTY): return [[c] * w for _ in range(h)]
def rect(px, x0, y0, w, h, c):
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w): px[y][x] = c
def blit(px, img, x0, y0, scale):
    for y, row in enumerate(img):
        for x, p in enumerate(row):
            if p[3]: rect(px, x0 + x * scale, y0 + y * scale, scale, scale, p)

def grid_image(recipe):
    """256x256 (content in the top-left 200x200, as Patchouli image pages expect): one cell per crafter."""
    import json
    r = json.load(open(os.path.join(RES, 'data/creativeforge/recipe/mechanical_crafting', recipe + '.json')))
    pat, key = r['pattern'], r['key']
    n = max(len(pat), len(pat[0])); cell = 200 // n; off = (200 - cell * n) // 2
    px = canvas(256, 256)
    rect(px, off - 3, off - 3, cell * n + 6, cell * n + 6, MAT['B'][0])
    rect(px, off - 2, off - 2, cell * n + 4, cell * n + 4, MAT['B'][2])
    icons = {k: TEXTURES[v]() for k, v in ICON.items()}
    for gy, row in enumerate(pat):
        for gx, ch in enumerate(row):
            x0, y0 = off + gx * cell, off + gy * cell
            rect(px, x0, y0, cell, cell, MAT['A'][1])
            rect(px, x0 + 1, y0 + 1, cell - 2, cell - 2, MAT['A'][3] if ch != ' ' else MAT['A'][2])
            if ch == ' ': continue
            iid = key[ch]['item']
            if iid in icons:
                sc = max(1, (cell - 4) // 16); blit(px, icons[iid], x0 + (cell - 16 * sc) // 2, y0 + (cell - 16 * sc) // 2, sc)
            else:
                rect(px, x0 + 2, y0 + 2, cell - 4, cell - 4, hx(LETTER_BG[ch]))
                sc = max(1, (cell - 8) // 8); g = GLYPH[ch]
                ink = MAT['S'][0] if ch in 'RC' else hx('fffff6')
                gx0, gy0 = x0 + (cell - 5 * sc) // 2, y0 + (cell - 7 * sc) // 2
                for yy, gr in enumerate(g):
                    for xx, b in enumerate(gr):
                        if b == 'X': rect(px, gx0 + xx * sc, gy0 + yy * sc, sc, sc, ink)
    return px

def filler():
    """128x128 page filler: a brass cogwheel on an andesite hub, drawn as flat bands (original art)."""
    px = canvas(128, 128)
    cx = cy = 64
    for y in range(128):
        for x in range(128):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy; d = math.hypot(dx, dy); ang = math.atan2(dy, dx)
            tooth = (math.cos(ang * 10) > 0.35)
            outer = 44 if tooth else 36
            lit = (-dx - dy) / (d + 1e-6)  # top-left light
            if d < outer and d >= 18:
                band = 0 if d > outer - 2 else (3 if lit > 0.45 else 2 if lit > -0.3 else 1)
                px[y][x] = MAT['B'][band]
            elif d < 18 and d >= 7:
                px[y][x] = MAT['A'][0 if d > 16 else 3 if lit > 0.3 else 2]
            elif d < 7:
                px[y][x] = MAT['A'][0] if d > 5 else hx('2b3635')
    for i in range(4):  # andesite spokes' rivets on the brass ring
        a2 = i * math.pi / 2 + math.pi / 4
        rx, ry = int(cx + math.cos(a2) * 27), int(cy + math.sin(a2) * 27)
        rect(px, rx - 2, ry - 2, 4, 4, MAT['B'][0]); rect(px, rx - 1, ry - 1, 2, 2, MAT['B'][4])
    return px

BOOK = [  # guide book item: andesite cover, brass corners and spine, small cog emblem
    '................',
    '..BBAAAAAAAAAB..',
    '..BAAAAAAAAAAB..',
    '..BAAAAyyAAAAB..',
    '..BAAAyAAyAAAB..',
    '..BAAyAuuAyAAB..',
    '..BAAyAuuAyAAB..',
    '..BAAAyAAyAAAB..',
    '..BAAAAyyAAAAB..',
    '..BAAAAAAAAAAB..',
    '..BAAAAAAAAAAB..',
    '..BAAAAAAAAAAB..',
    '..BBAAAAAAAABB..',
    '..BlllllllllB...',
    '...BBBBBBBBBB...',
    '................',
]

def write_book_art():
    os.makedirs(GUI, exist_ok=True)
    for rec in ('creative_crate', 'creative_fluid_tank', 'creative_motor', 'creative_blaze_cake', 'handheld_worldshaper'):
        png.write(os.path.join(GUI, f'grid_{rec}.png'), grid_image(rec))
    png.write(os.path.join(GUI, 'filler.png'), filler())
    png.write(os.path.join(OUT, 'guide_book.png'), render(BOOK))

if __name__ == '__main__':
    preview = sys.argv[sys.argv.index('--preview') + 1] if '--preview' in sys.argv else None
    os.makedirs(OUT, exist_ok=True)
    for name, fn in TEXTURES.items():
        px = fn()
        png.write(os.path.join(OUT, name + '.png'), px)
        if preview:
            os.makedirs(preview, exist_ok=True)
            big = [[p for p in row for _ in range(16)] for row in px for _ in range(16)]
            png.write(os.path.join(preview, name + '.png'), big)
    write_book_art()
    print('wrote', len(TEXTURES), 'textures + guide book art to', os.path.normpath(OUT), 'and', os.path.normpath(GUI))
