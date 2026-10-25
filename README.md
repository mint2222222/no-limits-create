# Creative Forge

NeoForge 1.21.1 addon for Create 6.0.x. Makes Create's creative items craftable through long automated chains, with per-world caps on the crate, fluid tank and motor. The in-game guide book (book + andesite alloy, shapeless) explains everything.

## Balance knobs

Create 6.0.10 has no survival recipe for chromatic compound, refined radiance or shadow steel, so this mod adds one for each (`create_materials/`). If your modpack already supplies them, override these recipe ids with a datapack.

All of these live in recipe JSON under `src/main/resources/data/creativeforge/recipe/` (or a datapack overriding the same ids). There is no config for them. Caps and enable switches are in the server config (`serverconfig/creativeforge-server.toml`). If you change a number, update the guide book entry in `src/main/resources/assets/creativeforge/patchouli_books/guide/en_us/entries/`.

| Recipe file | Knob | Current value |
|---|---|---|
| `sequenced_assembly/resonant_lattice.json` | `loops` | 4 |
| `sequenced_assembly/resonant_lattice.json` | lava fill `amount` | 250 mB |
| `sequenced_assembly/quantum_circuit.json` | `loops` | 3 |
| `sequenced_assembly/quantum_circuit.json` | honey (`c:honey`) fill `amount` | 250 mB |
| `sequenced_assembly/flux_matrix.json` | `loops` | 3 |
| `sequenced_assembly/flux_matrix.json` | lava fill `amount` | 500 mB |
| `sequenced_assembly/singularity_core.json` | `loops` | 3 |
| `sequenced_assembly/singularity_core.json` | lava fill `amount` | 1000 mB |
| `sequenced_assembly/singularity_core.json` | result `chance` weights | core 40, refined radiance 20, shadow steel 20, flux alloy 20 |
| `create_materials/chromatic_compound.json` | sequenced assembly on polished rose quartz: `loops` / lava fill | 5 / 500 mB (deploy precision mechanism, deploy electron tube, fill, press) |
| `create_materials/refined_radiance.json` | superheated mixing inputs | 1 chromatic compound, 4 glowstone dust, 2 amethyst shards |
| `create_materials/shadow_steel.json` | superheated mixing inputs | 1 chromatic compound, 2 obsidian, 1 ender pearl |
| `mixing/flux_alloy.json` | `heat_requirement` / output `count` | superheated / 2 |
| `mechanical_crafting/creative_crate.json` | `pattern` (cores) | 5×5, 5 K |
| `mechanical_crafting/creative_fluid_tank.json` | `pattern` (cores) | 5×5, 4 K |
| `mechanical_crafting/creative_motor.json` | `pattern` (cores) | 7×7, 5 K |
| `mechanical_crafting/creative_blaze_cake.json` | `pattern` | 7×7, no core |
| `mechanical_crafting/handheld_worldshaper.json` | `pattern` | 8×8, no core (its 60 parts don't fit 7×7; crafter grids go up to 9×9) |

## Balance model

Numbers come from `python3 tools/cost_model.py`, which reads the recipe JSON above and fails if a capped item leaves the 2-5 h window. Rerun it after changing a knob.

**Throughput assumption (a decent mid-game factory):** every sequenced-assembly line is a looping belt with one machine per step at 128 RPM, and finishes 20 loop passes per minute (one item leaves each station every 3 s). The factory runs one line per recipe in parallel, plus **2 precision mechanism lines**. A precision mechanism line is 3 deployers (cogwheel, large cogwheel, iron nugget) and needs 5 passes per attempt at 80% success (Create 6.0.10's recipe), so each line makes 3.2 per minute and the pair make 6.4 per minute. The other lines are:

- resonant lattice: 2 deployers, 1 press, 1 spout
- quantum circuit: 2 deployers, 1 spout, 1 press
- chromatic compound: 2 deployers, 1 spout, 1 press
- flux matrix: 2 deployers, 1 press, 1 spout
- singularity core: 4 deployers, 1 spout, 1 press
- sturdy sheet: 1 spout, 2 presses

Single-step parts (superheated mixing, crafting, polishing rose quartz, electron tubes, transmitters, brass sheets) are assumed to keep up. Lava is assumed unlimited (for example a hose pulley in a large lava lake). The time for an item is that of its slowest line, which is always the precision mechanism lines.

**Per Singularity Core** (40% chance, so 2.5 expected attempts; one attempt eats 1 chromatic compound, 3 quantum circuits, 3 flux matrices, 3 refined radiance, 3 shadow steel and 3000 mB lava; the failures are fed back in): 23.5 chromatic compounds, 208 precision mechanisms, 148 electron tubes, 111 B lava, 22.5 B honey.

| Item | Cores | Chromatic | Precision mech. | Electron tubes | Lava | Honey | Time |
|---|---|---|---|---|---|---|---|
| Creative crate | 5 | 121.5 | 1138 | 774 | 602 B | 124.5 B | 2.96 h |
| Creative fluid tank | 4 | 98 | 914 | 627 | 485 B | 102.8 B | 2.38 h |
| Creative motor | 5 | 133.5 | 1366 | 880 | 713 B | 159 B | 3.56 h |

The totals include the grid parts (matrices, circuits and lattices) as well as the cores. With 1 precision mechanism line, every time doubles (to 4.8-7.1 h), so a single line is below the "decent factory" this targets.

Before this tuning (core 20%, chromatic 3 loops, tank 3 K), the same model gave crate 4.38 h, tank 2.76 h and motor 4.91 h. Raising the core chance to 40% alone dropped them to 2.33, 1.53 and 2.86 h. Chromatic compound went to 5 loops and the tank to 4 K to bring them back inside 2-5 h.
