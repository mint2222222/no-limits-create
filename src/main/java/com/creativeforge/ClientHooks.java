package com.creativeforge;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.neoforged.neoforge.client.event.ClientPlayerNetworkEvent;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.entity.player.ItemTooltipEvent;

/** Client only: shows the last synced counter on managed items. Never touches the counter. */
final class ClientHooks {
    static void register() {
        NeoForge.EVENT_BUS.addListener(ItemTooltipEvent.class, ClientHooks::tooltip);
        NeoForge.EVENT_BUS.addListener(ClientPlayerNetworkEvent.LoggingOut.class, e -> CapSync.latest = null);
    }

    private static void tooltip(ItemTooltipEvent e) {
        CapSync s = CapSync.latest;
        Managed m = Managed.of(e.getItemStack());
        if (s == null || m == null) return;
        int i = m.ordinal(), count = s.counts().get(i), cap = s.caps().get(i);
        Component line;
        if (!s.enabled().get(i)) line = Component.translatable("tooltip.creativeforge.disabled").withStyle(ChatFormatting.RED);
        else if (cap < 0) line = Component.translatable("tooltip.creativeforge.uncapped").withStyle(ChatFormatting.GRAY);
        else {
            int left = Math.max(0, cap - count);
            line = Component.translatable("tooltip.creativeforge.forged", count, cap, left)
                    .withStyle(left > 0 ? ChatFormatting.GREEN : ChatFormatting.RED);
        }
        e.getToolTip().add(line);
    }

    private ClientHooks() {}
}
