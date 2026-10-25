package com.creativeforge;

import java.util.HashMap;
import java.util.Map;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.level.saveddata.SavedData;

/** Per-world (overworld) count of capped items minted by mechanical crafters. */
public class CraftCounter extends SavedData {
    private static final SavedData.Factory<CraftCounter> FACTORY = new SavedData.Factory<>(CraftCounter::new, CraftCounter::load, null);

    final Map<String, Integer> counts = new HashMap<>();

    public static CraftCounter get(MinecraftServer server) {
        return server.overworld().getDataStorage().computeIfAbsent(FACTORY, "creativeforge_counts");
    }

    public static CraftCounter load(CompoundTag tag, HolderLookup.Provider registries) {
        CraftCounter c = new CraftCounter();
        for (String k : tag.getAllKeys()) c.counts.put(k, tag.getInt(k));
        return c;
    }

    @Override
    public CompoundTag save(CompoundTag tag, HolderLookup.Provider registries) {
        counts.forEach(tag::putInt);
        return tag;
    }

    public int count(Managed m) {
        return counts.getOrDefault(m.key, 0);
    }

    public void set(Managed m, int n) {
        counts.put(m.key, n);
        setDirty();
        CapSync.broadcast();
    }

    /** Uncapped items are only gated by enabled and are not counted. */
    public boolean tryMint(Managed m, int n) {
        if (!m.enabled()) return false;
        if (!m.capped()) return true;
        if (count(m) + n > m.cap()) return false;
        set(m, count(m) + n);
        return true;
    }
}
