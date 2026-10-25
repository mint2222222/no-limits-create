package com.creativeforge;

import com.simibubi.create.content.kinetics.crafter.RecipeGridHandler;
import io.netty.buffer.Unpooled;
import java.util.List;
import java.util.Map;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.tags.TagKey;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

@GameTestHolder(CreativeForge.MODID)
@PrefixGameTestTemplate(false)
public class GameTests {

    @GameTest(template = "empty")
    public static void counterCapsAndPersists(GameTestHelper h) {
        CraftCounter c = new CraftCounter();
        Managed crate = Managed.CREATIVE_CRATE;
        int oldCap = crate.cap();
        try {
            Config.CAP.get(crate).set(3);
            for (int i = 0; i < 3; i++) h.assertTrue(c.tryMint(crate, 1), "mint " + (i + 1) + " should succeed");
            h.assertFalse(c.tryMint(crate, 1), "4th mint must fail");
            h.assertTrue(c.count(crate) == 3, "count must stay 3");

            Config.ENABLED.get(Managed.CREATIVE_MOTOR).set(false);
            h.assertFalse(c.tryMint(Managed.CREATIVE_MOTOR, 1), "disabled item must fail");
            Config.ENABLED.get(Managed.CREATIVE_BLAZE_CAKE).set(false);
            h.assertFalse(c.tryMint(Managed.CREATIVE_BLAZE_CAKE, 1), "disabled uncapped item must fail");

            var reg = h.getLevel().registryAccess();
            CraftCounter loaded = CraftCounter.load(c.save(new CompoundTag(), reg), reg);
            h.assertTrue(loaded.count(crate) == 3, "count must survive save/load");
            h.assertFalse(loaded.tryMint(crate, 1), "loaded counter must still be capped");
        } finally {
            Config.CAP.get(crate).set(oldCap);
            Config.ENABLED.get(Managed.CREATIVE_MOTOR).set(true);
            Config.ENABLED.get(Managed.CREATIVE_BLAZE_CAKE).set(true);
        }
        h.succeed();
    }

    /**
     * Drives the real crafter entry point (RecipeGridHandler.tryToApplyRecipe) with the crate grid 4 times.
     * shortcut: no physical crafter structure; null -> ejectWholeGrid was verified in bytecode, upgrade to a .nbt build if Create changes tick().
     */
    @GameTest(template = "empty")
    public static void crateCapThroughCrafter(GameTestHelper h) {
        CraftCounter counter = CraftCounter.get(h.getLevel().getServer());
        Managed crate = Managed.CREATIVE_CRATE;
        int oldCount = counter.count(crate), oldCap = crate.cap();
        String[] pattern = {"VLKLV", "LQMQL", "KMKMK", "LQMQL", "VLKLV"};
        Map<Character, String> key = Map.of('K', "creativeforge:singularity_core", 'M', "creativeforge:flux_matrix",
                'Q', "creativeforge:quantum_circuit", 'L', "creativeforge:resonant_lattice", 'V', "create:item_vault");
        try {
            counter.set(crate, 0);
            Config.CAP.get(crate).set(3);
            int made = 0;
            for (int run = 0; run < 4; run++) {
                ListTag list = new ListTag();
                for (int y = 0; y < 5; y++)
                    for (int x = 0; x < 5; x++) {
                        CompoundTag e = new CompoundTag();
                        e.putInt("x", x);
                        e.putInt("y", y);
                        ItemStack s = new ItemStack(BuiltInRegistries.ITEM.get(ResourceLocation.parse(key.get(pattern[y].charAt(x)))));
                        e.put("item", s.saveOptional(h.getLevel().registryAccess()));
                        list.add(e);
                    }
                CompoundTag tag = new CompoundTag();
                tag.put("Grid", list);
                ItemStack out = RecipeGridHandler.tryToApplyRecipe(h.getLevel(),
                        RecipeGridHandler.GroupedItems.read(tag, h.getLevel().registryAccess()));
                if (run < 3) {
                    h.assertTrue(out != null && Managed.of(out) == crate, "craft " + (run + 1) + " should yield a crate, got " + out);
                    made++;
                } else {
                    h.assertTrue(out == null, "4th craft must be refused with null (grid ejected intact), got " + out);
                }
            }
            h.assertTrue(made == 3 && counter.count(crate) == 3, "exactly 3 crates, counter 3");
        } finally {
            counter.set(crate, oldCount);
            Config.CAP.get(crate).set(oldCap);
        }
        h.succeed();
    }

    @GameTest(template = "empty")
    public static void capSyncCodecRoundTrip(GameTestHelper h) {
        CapSync sent = new CapSync(List.of(2, 0, 20, 0, 0), List.of(3, 4, 20, -1, -1), List.of(true, false, true, true, false));
        var buf = Unpooled.buffer();
        CapSync.CODEC.encode(buf, sent);
        CapSync got = CapSync.CODEC.decode(buf);
        h.assertTrue(sent.equals(got) && buf.readableBytes() == 0, "round trip changed the payload: " + got);
        CapSync live = CapSync.of(h.getLevel().getServer());
        h.assertTrue(live.counts().size() == Managed.values().length, "snapshot must have one entry per managed item");
        h.succeed();
    }

    /** Fails loudly if a Create update drops the c:honey fluid tag the quantum circuit recipe fills with. */
    @GameTest(template = "empty")
    public static void honeyTagAndQuantumCircuitLoad(GameTestHelper h) {
        var honey = TagKey.create(Registries.FLUID, ResourceLocation.parse("c:honey"));
        h.assertTrue(BuiltInRegistries.FLUID.getTag(honey).map(t -> t.size() > 0).orElse(false), "fluid tag c:honey is empty or missing");
        h.assertTrue(h.getLevel().getRecipeManager().byKey(ResourceLocation.parse("creativeforge:sequenced_assembly/quantum_circuit")).isPresent(),
                "recipe creativeforge:sequenced_assembly/quantum_circuit did not load");
        for (String r : new String[] {"chromatic_compound", "refined_radiance", "shadow_steel"})
            h.assertTrue(h.getLevel().getRecipeManager().byKey(ResourceLocation.parse("creativeforge:create_materials/" + r)).isPresent(),
                    "recipe creativeforge:create_materials/" + r + " did not load");
        h.succeed();
    }
}
