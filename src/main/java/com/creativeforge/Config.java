package com.creativeforge;

import java.util.EnumMap;
import java.util.Map;
import net.neoforged.neoforge.common.ModConfigSpec;

public final class Config {
    public static final Map<Managed, ModConfigSpec.BooleanValue> ENABLED = new EnumMap<>(Managed.class);
    public static final Map<Managed, ModConfigSpec.IntValue> CAP = new EnumMap<>(Managed.class);
    public static final ModConfigSpec.BooleanValue STRICT_AUDIT;
    public static final ModConfigSpec SPEC;

    static {
        ModConfigSpec.Builder b = new ModConfigSpec.Builder();
        for (Managed m : Managed.values()) {
            b.push(m.key);
            ENABLED.put(m, b.comment("Allow mechanical crafters to make this item").define("enabled", true));
            if (m.capped())
                CAP.put(m, b.comment("Max number ever crafted in this world (counts items made, destroyed items are not refunded)")
                        .defineInRange("cap", m.defaultCap, 0, m.hardMax));
            b.pop();
        }
        STRICT_AUDIT = b.comment("Refuse to start the server if any non-mechanical-crafting recipe outputs a managed item")
                .define("strictAudit", false);
        SPEC = b.build();
    }

    private Config() {}
}
