package com.creativeforge;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

public enum Managed {
    CREATIVE_CRATE("creative_crate", "creative_crate", 3, 3),
    CREATIVE_FLUID_TANK("creative_fluid_tank", "creative_fluid_tank", 4, 5),
    CREATIVE_MOTOR("creative_motor", "creative_motor", 20, 20),
    CREATIVE_BLAZE_CAKE("creative_blaze_cake", "creative_blaze_cake", -1, -1),
    WORLDSHAPER("handheld_worldshaper", "worldshaper", -1, -1);

    public final ResourceLocation id;
    public final String key;
    public final int defaultCap;
    /** -1 = uncapped */
    public final int hardMax;

    Managed(String path, String key, int defaultCap, int hardMax) {
        this.id = ResourceLocation.fromNamespaceAndPath("create", path);
        this.key = key;
        this.defaultCap = defaultCap;
        this.hardMax = hardMax;
    }

    public boolean capped() {
        return hardMax >= 0;
    }

    public boolean enabled() {
        return Config.ENABLED.get(this).get();
    }

    public int cap() {
        return Config.CAP.get(this).get();
    }

    public static Managed of(ItemStack stack) {
        return stack == null || stack.isEmpty() ? null : of(stack.getItem());
    }

    public static Managed of(Item item) {
        ResourceLocation rl = BuiltInRegistries.ITEM.getKey(item);
        for (Managed m : values()) if (m.id.equals(rl)) return m;
        return null;
    }

    public static Managed byKey(String key) {
        for (Managed m : values()) if (m.key.equals(key)) return m;
        return null;
    }
}
