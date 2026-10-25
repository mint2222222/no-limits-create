"""Expected cost and factory time of each capped creative item, read from the recipe JSON.

Run: python3 tools/cost_model.py   (asserts every capped item takes 2-5 h under the throughput assumption below)

Throughput assumption (mid-game factory, every line at 128 RPM, one machine per step on a looping belt):
  every sequenced-assembly line finishes PASSES_PER_MIN loop passes per minute (one item leaves a station every 3 s).
  Lines: LINES gives how many copies of each line the factory runs, all in parallel.
  Single-step parts (mixing, crafting, polishing, electron tubes, transmitters, brass sheets) are assumed to keep up.
"""
import json, os
from fractions import Fraction as F

REC = os.path.join(os.path.dirname(__file__), '..', 'src/main/resources/data/creativeforge/recipe')
PASSES_PER_MIN = 20
# precision mechanism lines get 2 copies: every intermediate except the circuit eats them
LINES = {'precision_mechanism': 2}
# Create 6.0.10 data/create/recipe/sequenced_assembly: precision_mechanism 5 loops x 3 deploys, 120/150 success;
# sturdy_sheet 1 pass (fill 500 mB lava, press, press)
PM_LOOPS, PM_OK = 5, F(120, 150)
STURDY_LAVA = 500
CF = 'creativeforge:'


def rec(p): return json.load(open(os.path.join(REC, p + '.json')))


def per_loop(r):
    """items and fluids one finished sequenced assembly consumes (ingredient + all loops)."""
    tot = {r['ingredient']['item']: 1}
    for st in r['sequence']:
        if len(st['ingredients']) < 2: continue
        i = st['ingredients'][1]
        k = i.get('item') or i.get('fluid') or i.get('tag')
        tot[k] = tot.get(k, 0) + r['loops'] * i.get('amount', 1)
    return tot


def chance(r, i):
    w = sum(F(x.get('chance', 1)) for x in r['results'])
    return sum(F(x.get('chance', 1)) for x in r['results'] if x['id'] == i) / w


def mix(p):
    r = rec(p); out = {}
    for i in r['ingredients']: out[i['item']] = out.get(i['item'], 0) + 1
    return out, r['results'][0].get('count', 1)


def grid(name):
    r = rec('mechanical_crafting/' + name); c = {}
    for row in r['pattern']:
        for ch in row:
            if ch != ' ': c[r['key'][ch]['item']] = c.get(r['key'][ch]['item'], 0) + 1
    return c


def cost(parts):
    need = {k: F(v) for k, v in parts.items()}
    passes = {}
    def add(k, v): need[k] = need.get(k, 0) + v
    def take(k): return need.pop(k, 0)
    def sa(line, n, r):  # run sequenced assembly n times
        passes[line] = passes.get(line, 0) + n * r['loops']
        for k, v in per_loop(r).items(): add(k, n * v)

    core = rec('sequenced_assembly/singularity_core')
    k = take(CF + 'singularity_core'); att = k / chance(core, CF + 'singularity_core')
    sa('singularity_core', att, core)
    for i in ('create:refined_radiance', 'create:shadow_steel', CF + 'flux_alloy'):  # failures are fed back in
        add(i, -att * chance(core, i))
    sa('flux_matrix', take(CF + 'flux_matrix'), rec('sequenced_assembly/flux_matrix'))
    fa_in, fa_out = mix('mixing/flux_alloy')
    n = max(take(CF + 'flux_alloy'), 0) / fa_out
    for i, v in fa_in.items(): add(i, n * v)
    for m in ('refined_radiance', 'shadow_steel'):
        ins, _ = mix('create_materials/' + m)
        n = take('create:' + m)
        for i, v in ins.items(): add(i, n * v)
    chroma = need.get('create:chromatic_compound', 0)
    sa('chromatic_compound', take('create:chromatic_compound'), rec('create_materials/chromatic_compound'))
    sa('resonant_lattice', take(CF + 'resonant_lattice'), rec('sequenced_assembly/resonant_lattice'))
    sa('quantum_circuit', take(CF + 'quantum_circuit'), rec('sequenced_assembly/quantum_circuit'))
    n = need.get('create:sturdy_sheet', 0); passes['sturdy_sheet'] = n; add('minecraft:lava', n * STURDY_LAVA)
    pm = need.get('create:precision_mechanism', 0); passes['precision_mechanism'] = pm / PM_OK * PM_LOOPS
    minutes = {l: p / PASSES_PER_MIN / LINES.get(l, 1) for l, p in passes.items()}
    return dict(cores=k, attempts=att, chroma=chroma, pm=pm, et=need.get('create:electron_tube', 0),
                lava=need.get('minecraft:lava', 0), honey=need.get('c:honey', 0), minutes=minutes,
                hours=max(minutes.values()) / 60, bottleneck=max(minutes, key=minutes.get))


if __name__ == '__main__':
    core = rec('sequenced_assembly/singularity_core')
    print(f"attempts per core: {float(1 / chance(core, CF + 'singularity_core')):g}")
    bad = []
    for name in ('one singularity_core', 'creative_crate', 'creative_fluid_tank', 'creative_motor'):
        c = cost({CF + 'singularity_core': 1} if name.startswith('one') else grid(name))
        print(f"{name}: {c['cores']} cores, {float(c['attempts']):g} attempts, {float(c['chroma']):.1f} chromatic, "
              f"{float(c['pm']):.0f} precision mech, {float(c['et']):.0f} electron tubes, "
              f"{float(c['lava']) / 1000:.0f} B lava, {float(c['honey']) / 1000:.1f} B honey, "
              f"{c['hours']:.2f} h (bottleneck {c['bottleneck']})")
        print('   line minutes:', {k: round(float(v)) for k, v in c['minutes'].items()})
        if not name.startswith('one') and not 2 <= c['hours'] <= 5: bad.append((name, float(c['hours'])))
    assert not bad, bad
    # recycling stays a net loss: one attempt eats more radiance + shadow steel than its single result can return
    eaten = sum(v for i, v in per_loop(core).items() if i in ('create:refined_radiance', 'create:shadow_steel'))
    assert eaten > 1 and all(x.get('count', 1) == 1 for x in core['results']), eaten
    ks = {n: grid(n).get(CF + 'singularity_core', 0) for n in ('creative_crate', 'creative_motor')}
    assert ks['creative_crate'] >= ks['creative_motor'], ks
