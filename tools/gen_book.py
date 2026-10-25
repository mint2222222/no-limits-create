"""Generates the Patchouli guide book (book.json, categories, entries) from the mod's recipe JSON.

Numbers (loops, fluid amounts, result chances, grid contents) are read from src/main/resources/data/creativeforge/recipe,
so re-run this after tuning a recipe:  python3 tools/gen_book.py
"""
import json, os, shutil
from fractions import Fraction

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src/main/resources')
REC = os.path.join(ROOT, 'data/creativeforge/recipe')
BOOK = os.path.join(ROOT, 'assets/creativeforge/patchouli_books/guide/en_us')
CF = 'creativeforge:'
MAX_TEXT, MAX_SPOT, MAX_IMAGE = 330, 190, 110  # chars per page type, keeps pages from overflowing

NAMES = {
    'creativeforge:singularity_core': 'Singularity Core', 'creativeforge:flux_matrix': 'Flux Matrix',
    'creativeforge:quantum_circuit': 'Quantum Circuit', 'creativeforge:resonant_lattice': 'Resonant Lattice',
    'creativeforge:flux_alloy': 'Flux Alloy', 'create:item_vault': 'Item Vault', 'create:fluid_tank': 'Fluid Tank',
    'create:blaze_cake': 'Blaze Cake', 'create:chromatic_compound': 'Chromatic Compound',
    'create:refined_radiance': 'Refined Radiance', 'create:shadow_steel': 'Shadow Steel',
    'create:sturdy_sheet': 'Sturdy Sheet', 'create:precision_mechanism': 'Precision Mechanism',
    'create:brass_sheet': 'Brass Sheet', 'create:electron_tube': 'Electron Tube', 'create:transmitter': 'Transmitter',
    'create:polished_rose_quartz': 'Polished Rose Quartz', 'create:brass_ingot': 'Brass Ingot',
    'minecraft:glowstone_dust': 'Glowstone Dust', 'minecraft:amethyst_shard': 'Amethyst Shard',
    'minecraft:obsidian': 'Obsidian', 'minecraft:ender_pearl': 'Ender Pearl', 'minecraft:lava': 'lava',
    'create:creative_crate': 'Creative Crate', 'create:creative_fluid_tank': 'Creative Fluid Tank',
    'create:creative_motor': 'Creative Motor', 'create:creative_blaze_cake': 'Creative Blaze Cake',
    'create:handheld_worldshaper': 'Creative Worldshaper', 'c:honey': 'honey',
}
def nm(i): return NAMES[i]
def rec(path): return json.load(open(os.path.join(REC, path + '.json')))
def link(entry, text): return f'$(l:{CF}{entry}){text}$(/l)'

def w(path, obj):
    path = os.path.join(BOOK, path); os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w').write(json.dumps(obj, indent=2) + '\n')

shutil.rmtree(BOOK, ignore_errors=True)  # stale entries from older layouts must not linger

# ---- page helpers (each checks its length) ----
def text(t, title=None):
    assert len(t) <= MAX_TEXT - (60 if title else 0), (len(t), t)
    return {'type': 'patchouli:text', 'text': t, **({'title': title} if title else {})}
def spot(item, t, title=None):
    assert len(t) <= MAX_SPOT, (len(t), t)
    return {'type': 'patchouli:spotlight', 'item': item, 'text': t, **({'title': title} if title else {})}
def image(img, title, t):
    assert len(t) <= MAX_IMAGE, (len(t), t)
    return {'type': 'patchouli:image', 'images': [f'creativeforge:textures/gui/guide/{img}.png'], 'title': title, 'border': True, 'text': t}
def rel(entries, t):
    return {'type': 'patchouli:relations', 'entries': [CF + e for e in entries], **({'text': t} if t else {})}

# ---- recipe readers ----
def steps(r):
    out = []
    for st in r['sequence']:
        kind = st['type'].split(':')[1]
        if kind == 'deploying': out.append('deploy ' + nm(st['ingredients'][1]['item']))
        elif kind == 'pressing': out.append('press')
        elif kind == 'filling':
            f = st['ingredients'][1]; out.append(f"fill {f['amount']} mB {nm(f.get('fluid') or f.get('tag'))}")
        else: out.append(kind)
    return out

def seq_pages(path, extra=''):
    r = rec(path)
    lst = ''.join(f'$(li){s}' for s in steps(r))
    return text(f"$(l)Sequenced assembly$() on a $(item){nm(r['ingredient']['item'])}$(), {r['loops']} loops of:{lst}{extra}")

def per_item_totals(path):
    r = rec(path); loops = r['loops']; tot = {}
    for st in r['sequence']:
        if st['type'] == 'create:deploying':
            i = st['ingredients'][1]['item']; tot[i] = tot.get(i, 0) + loops
        elif st['type'] == 'create:filling':
            f = st['ingredients'][1]; k = f.get('fluid') or f.get('tag'); tot[k] = tot.get(k, 0) + loops * f['amount']
    return r, tot

def totals_text(path, intro):
    r, tot = per_item_totals(path)
    parts = [f"1 {nm(r['ingredient']['item'])}"] + [
        (f'{v} mB {nm(k)}' if k in ('minecraft:lava', 'c:honey') else f'{v} {nm(k)}') for k, v in tot.items()]
    return intro + ' $(li)' + '$(li)'.join(parts)

def mixing_list(path):
    r = rec(path); counts = {}
    for i in r['ingredients']: counts[i['item']] = counts.get(i['item'], 0) + 1
    return r, ', '.join(f'{v} {nm(k)}' for k, v in counts.items())

def grid_counts(name):
    r = rec('mechanical_crafting/' + name); c = {}
    for row in r['pattern']:
        for ch in row:
            if ch != ' ': c[ch] = c.get(ch, 0) + 1
    size = f"{len(r['pattern'][0])}x{len(r['pattern'])}"
    return size, {r['key'][k]['item']: v for k, v in c.items()}, r['key']

# ---- book.json ----
json.dump({
    'name': 'Creative Forge',
    'subtitle': 'Field Manual',
    'landing_text': "$(l)Engineer,$()$(br)this manual covers the long road from brass and andesite to Create's $(l)creative$() items.$(br2)"
                    "Every number in here comes from this mod's real recipes. Start with $(l:creativeforge:start/getting_started)Getting Started$(/l).",
    'use_resource_pack': True, 'show_progress': False, 'i18n': False,
    'creative_tab': 'creativeforge:main', 'model': 'creativeforge:guide_book',
    'book_texture': 'patchouli:textures/gui/book_gray.png',
    'filler_texture': 'creativeforge:textures/gui/guide/filler.png',
    'index_icon': 'creativeforge:singularity_core',
    # Create's warm palette: brass headers/links, andesite-dark text, brass-gold nameplate
    'text_color': '2b3635', 'header_color': '7a3f1d', 'nameplate_color': 'fbcc68',
    'link_color': 'b5692d', 'link_hover_color': 'e09a3c',
    'progress_bar_color': 'd3a155', 'progress_bar_background': '4a5451',
}, open(os.path.join(ROOT, 'data/creativeforge/patchouli_books/guide/book.json'), 'w'), indent=2)

# ---- categories ----
for i, (cid, title, desc, icon) in enumerate([
        ('start', 'Getting Started', 'What to build first, and where the raw materials come from.', 'create:mechanical_crafter'),
        ('components', 'Components', 'Every part this mod adds, step by step.', 'creativeforge:flux_matrix'),
        ('creative', 'Creative Items', 'The five creative items and their crafter grids.', 'create:creative_crate'),
        ('rules', 'Caps and Admin', 'How the per-world caps work, commands, config and FAQ.', 'minecraft:command_block')]):
    w(f'categories/{cid}.json', {'name': title, 'description': desc, 'icon': icon, 'sortnum': i})

def entry(cat, eid, title, icon, sort, pages):
    w(f'entries/{cat}/{eid}.json', {'name': title, 'icon': icon, 'category': CF + cat, 'sortnum': sort, 'pages': pages})

# ---- Getting started ----
entry('start', 'overview', 'Overview', 'creativeforge:singularity_core', 0, [
    spot('creativeforge:singularity_core', title='Creative Forge', t="Creative Forge makes Create's creative items craftable, through long automated chains that end in a $(l)mechanical crafter$() grid."),
    text("The strongest items are $(l)capped per world$(): a server only ever gets a few creative crates, fluid tanks and motors. See "
         + link('rules/cap', 'How the Cap Works') + ".$(br2)The chain: raw materials, then four components, then the "
         + link('components/singularity_core', 'Singularity Core') + ", then a creative item."),
])
entry('start', 'getting_started', 'Getting Started', 'create:mechanical_crafter', 1, [
    text("Build these first, in order:$(li)Create basics: andesite alloy, shafts, cogs, a steady power source"
         "$(li)Brass and a $(l)superheated$() mixer (blaze burner fed with a blaze cake)"
         "$(li)A sequenced assembly line: depot or belt, deployers, mechanical press, spout", 'First Steps'),
    text("$(li)Precision mechanisms and electron tubes (Create's own assembly recipes)"
         "$(li)A mechanical crafter grid up to 8x8, powered by a cogwheel touching one crafter"
         "$(br2)Then make the " + link('start/raw_materials', 'raw materials') + '.'),
])
gr = rec('guide_book')
entry('start', 'guide_book', 'This Guide Book', 'minecraft:book', 2, [
    {'type': 'patchouli:crafting', 'recipe': CF + 'guide_book',
     'text': 'Shapeless: ' + ' + '.join('1 ' + i['item'].split(':')[1].replace('_', ' ') for i in gr['ingredients']) + '. Nothing in the book is locked.'},
])
_, cc_tot = per_item_totals('create_materials/chromatic_compound')
_, rr = mixing_list('create_materials/refined_radiance')
_, ss = mixing_list('create_materials/shadow_steel')
entry('start', 'raw_materials', 'Raw Materials', 'create:chromatic_compound', 3, [
    text("Create 6.0.10 has $(l)no survival recipe$() for Chromatic Compound, Refined Radiance or Shadow Steel. This mod adds one for each, so the chain is playable.$(br2)"
         "A modpack that already makes them can override these recipe ids with a datapack.", 'Added by this mod'),
    spot('create:chromatic_compound', ''),
    seq_pages('create_materials/chromatic_compound'),
    spot('create:refined_radiance', f'$(l)Superheated mixing$(): {rr}. One per batch.'),
    spot('create:shadow_steel', f'$(l)Superheated mixing$(): {ss}. One per batch.'),
    rel(['components/flux_alloy', 'components/singularity_core', 'components/core_economy'], None),
])
# fill the chromatic spotlight text now that totals are known
p = os.path.join(BOOK, 'entries/start/raw_materials.json'); e = json.load(open(p))
e['pages'][1]['text'] = totals_text('create_materials/chromatic_compound', 'One compound costs:')
assert len(e['pages'][1]['text']) <= MAX_SPOT, e['pages'][1]['text']
json.dump(e, open(p, 'w'), indent=2)

# ---- Components ----
def component(eid, sort, intro, related, pages_mid):
    item = CF + eid
    entry('components', eid, nm(item), item, sort, [spot(item, intro)] + pages_mid + [rel(related, None)])

component('resonant_lattice', 0, 'A brass lattice riveted onto a sturdy sheet. The base part of every final recipe.',
          ['components/flux_matrix', 'creative/crafter_grids'],
          [seq_pages('sequenced_assembly/resonant_lattice'), text(totals_text('sequenced_assembly/resonant_lattice', 'Total per lattice:'))])
component('quantum_circuit', 1, 'An electron tube filled with honey and rose quartz light.',
          ['components/flux_matrix', 'components/singularity_core'],
          [seq_pages('sequenced_assembly/quantum_circuit'), text(totals_text('sequenced_assembly/quantum_circuit', 'Total per circuit:'))])
fa, fa_list = mixing_list('mixing/flux_alloy')
component('flux_alloy', 2, f"$(l)Superheated mixing$(): {fa_list}, giving {fa['results'][0].get('count', 1)} Flux Alloy.",
          ['start/raw_materials', 'components/flux_matrix'],
          [text('Flux Alloy is the starting item of every ' + link('components/flux_matrix', 'Flux Matrix') +
                ". It also comes back as a failed result of the Singularity Core, so it can be fed straight back in.")])
component('flux_matrix', 3, 'A denser lattice with a cool zinc glow. The heaviest part by count in the final grids.',
          ['components/resonant_lattice', 'components/quantum_circuit', 'components/flux_alloy'],
          [seq_pages('sequenced_assembly/flux_matrix'), text(totals_text('sequenced_assembly/flux_matrix', 'Total per matrix:'))])
core = rec('sequenced_assembly/singularity_core')
total_w = sum(r.get('chance', 1) for r in core['results'])
pool = ''.join(f"$(li){Fraction(int(r.get('chance', 1)), int(total_w)) * 100:.0f}% {nm(r['id'])}" for r in core['results'])
component('singularity_core', 4, 'The gate. Needed by the creative crate, fluid tank and motor. Each attempt can fail.',
          ['components/core_economy', 'creative/creative_crate', 'creative/creative_fluid_tank', 'creative/creative_motor'],
          [seq_pages('sequenced_assembly/singularity_core'), text('Each finished attempt gives $(l)one$() result from this pool:' + pool, 'Result Pool')])

# economy numbers from the JSON
_, ctot = per_item_totals('sequenced_assembly/singularity_core')
p_core = Fraction(int(next(r.get('chance', 1) for r in core['results'] if r['id'] == CF + 'singularity_core')), int(total_w))
att = 1 / p_core
ret = {r['id']: Fraction(int(r.get('chance', 1)), int(total_w)) * att for r in core['results'] if r['id'] != CF + 'singularity_core'}
def f(x): return f'{float(x):g}'
entry('components', 'core_economy', 'Core Economy', 'create:refined_radiance', 5, [
    text(f"One attempt costs:$(li)1 Chromatic Compound" + ''.join(
        f"$(li){v} {nm(k)}" if k != 'minecraft:lava' else f"$(li){v} mB lava" for k, v in ctot.items())
        + f"$(br2)A core drops {f(p_core * 100)}% of the time, so expect about {f(att)} attempts per core.", 'Cost per Attempt'),
    text("Per core, on average, the failures give back:" + ''.join(f"$(li){f(v)} {nm(k)}" for k, v in ret.items())
         + "$(br2)Feed failures back in. It is still a net loss: an attempt uses "
         + f"{ctot.get('create:refined_radiance', 0) + ctot.get('create:shadow_steel', 0)} radiance and shadow steel, and returns at most 1.", 'Recycling'),
])

# ---- Creative items ----
CAPS = {'creative_crate': (3, 3), 'creative_fluid_tank': (4, 5), 'creative_motor': (20, 20)}
def creative(eid, rname, sort, blurb, extra=''):
    size, counts, _ = grid_counts(rname)
    cores = counts.get(CF + 'singularity_core', 0)
    cap = CAPS.get(rname)
    cap_t = f'Cap: {cap[0]} per world (config 0-{cap[1]}).' if cap else 'Uncapped.'
    lst = ''.join(f'$(li){v} {nm(k)}' for k, v in counts.items())
    entry('creative', eid, nm('create:' + rname), 'create:' + rname, sort, [
        spot('create:' + rname, f'{blurb} $(l)Core cost: {cores}$(). {cap_t}'),
        text(f'{size} mechanical crafting{extra}:{lst}', 'Recipe'),
        image('grid_' + rname, 'Crafter Grid', 'Lay the crafters out like this. Letters: see ' + link('creative/crafter_grids', 'Crafter Grids') + '.'),
        rel(['creative/crafter_grids', 'rules/cap'] + (['components/singularity_core'] if cores else []), None),
    ])
creative('creative_crate', 'creative_crate', 0, 'Endless items: the most broken, so the most cores.')
creative('creative_fluid_tank', 'creative_fluid_tank', 1, 'Endless fluid.')
creative('creative_motor', 'creative_motor', 2, 'Free rotation at any speed. Really difficult.')
creative('creative_blaze_cake', 'creative_blaze_cake', 3, 'Permanent superheat. Very expensive, but no cores.')
creative('worldshaper', 'handheld_worldshaper', 4, 'Creative terrain tool. No cores.',
         ', corners empty (60 parts do not fit 7x7; crafter grids go up to 9x9)')
entry('creative', 'crafter_grids', 'Crafter Grids', 'create:mechanical_crafter', 5, [
    text("Each grid picture is one mechanical crafter per square. Our parts are drawn as icons; Create parts as letters:"
         "$(li)V Item Vault$(li)T Fluid Tank$(li)B Blaze Cake$(li)C Chromatic Compound$(li)R Refined Radiance$(li)S Shadow Steel"
         "$(br2)Grey squares are empty.", 'Legend'),
    text("Point every crafter's arrow along a chain that ends in one crafter; that one outputs. Crafters only turn from a $(l)cogwheel$() touching one of them, not a shaft behind.$(br2)"
         "Mirrored layouts are not accepted.", 'Building a Grid'),
    image('grid_creative_crate', 'Crate', '5x5, all 25 crafters filled.'),
    image('grid_creative_fluid_tank', 'Fluid Tank', '5x5, all 25 filled.'),
    image('grid_creative_motor', 'Motor', '7x7, all 49 filled.'),
    image('grid_creative_blaze_cake', 'Blaze Cake', '7x7, all 49 filled.'),
    image('grid_handheld_worldshaper', 'Worldshaper', '8x8, four empty corners.'),
])

# ---- Rules and admin ----
entry('rules', 'tiers', 'Tiers and Caps', 'create:creative_motor', 0, [
    text("Default caps per world:$(li)Creative Crate: 3$(li)Creative Fluid Tank: 4$(li)Creative Motor: 20$(li)Blaze Cake: uncapped$(li)Worldshaper: uncapped"
         "$(br2)These are defaults. The server config can lower them or disable any item.", 'Defaults'),
    text("Config limits: crate 0-3, fluid tank 0-5, motor 0-20. The config cannot raise a cap above these."),
])
entry('rules', 'cap', 'How the Cap Works', 'minecraft:barrier', 1, [
    text("Each world keeps one counter per capped item, saved with the world (not per player).$(br2)"
         "It counts items $(l)made$(), not items that exist. A destroyed, burnt or voided creative item is $(l)never refunded$()."),
    text("The cap is checked at the mechanical crafter when the craft completes. If the item is disabled or the cap is reached, the craft is refused and the crafter "
         "ejects its whole grid, so $(l)the inputs are kept$() (they drop as items in front of the crafters).$(br2)Uncapped items are only checked for being enabled."),
])
entry('rules', 'admin', 'Commands', 'minecraft:command_block', 2, [
    text("Op level 2:$(li)/creativeforge counts: made / cap per item$(li)/creativeforge set <item> <n>: overwrite a counter$(li)/creativeforge reset <item>: set it to 0"
         "$(br2)Items: creative_crate, creative_fluid_tank, creative_motor."),
])
entry('rules', 'config', 'Config and Audit', 'create:wrench', 3, [
    text("File: serverconfig/creativeforge-server.toml in the world folder.$(li)[creative_crate], [creative_fluid_tank], [creative_motor]: enabled, cap"
         "$(li)[creative_blaze_cake], [worldshaper]: enabled$(li)strictAudit (default false)"),
    text("At server start every recipe is checked. One that makes a creative item outside mechanical crafting is logged as an error, because the cap cannot see it."
         " With $(l)strictAudit$() on, the server refuses to start instead."),
])
entry('rules', 'limits', 'Known Limits', 'minecraft:structure_void', 4, [
    text("The cap only covers mechanical crafters. These bypass it:$(li)/give and the creative inventory$(li)loot, structures and mods that create items directly"
         "$(li)other mods' recipes for these items (the audit reports them, but does not block them)$(br2)JEI still shows the recipes after a cap is reached."),
])
entry('rules', 'faq', 'FAQ', 'minecraft:book', 5, [
    text("$(l)Why was my craft refused?$()$(br)The item is disabled in the config, or this world already made its cap. Check /creativeforge counts.$(br2)"
         "$(l)Did I lose the inputs?$()$(br)No. The grid is ejected in front of the crafters. Pick it up before it despawns (5 minutes)."),
    text("$(l)Can I get a slot back if a crate is destroyed?$()$(br)Not by itself: the counter counts items made. An admin can lower it with /creativeforge set.$(br2)"
         "$(l)What does /creativeforge set do?$()$(br)It overwrites the counter for one item, for example after a rollback."),
])
print('book written to', os.path.normpath(BOOK))
