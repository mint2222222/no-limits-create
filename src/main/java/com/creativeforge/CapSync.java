package com.creativeforge;

import io.netty.buffer.ByteBuf;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.neoforge.network.PacketDistributor;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;
import net.neoforged.neoforge.server.ServerLifecycleHooks;

/** Server -> client snapshot of the counters, indexed by Managed.ordinal(). cap -1 = uncapped. Display only. */
public record CapSync(List<Integer> counts, List<Integer> caps, List<Boolean> enabled) implements CustomPacketPayload {
    public static final Type<CapSync> TYPE = new Type<>(ResourceLocation.fromNamespaceAndPath(CreativeForge.MODID, "cap_sync"));
    public static final StreamCodec<ByteBuf, CapSync> CODEC = StreamCodec.composite(
            ByteBufCodecs.VAR_INT.apply(ByteBufCodecs.list()), CapSync::counts,
            ByteBufCodecs.VAR_INT.apply(ByteBufCodecs.list()), CapSync::caps,
            ByteBufCodecs.BOOL.apply(ByteBufCodecs.list()), CapSync::enabled,
            CapSync::new);

    /** Latest snapshot received by this client; null until the server sends one. Written only by the client handler. */
    public static volatile CapSync latest;

    @Override
    public Type<CapSync> type() {
        return TYPE;
    }

    static void register(RegisterPayloadHandlersEvent e) {
        e.registrar("1").playToClient(TYPE, CODEC, (p, ctx) -> latest = p);
    }

    static CapSync of(MinecraftServer server) {
        CraftCounter c = CraftCounter.get(server);
        List<Integer> counts = new ArrayList<>(), caps = new ArrayList<>();
        List<Boolean> enabled = new ArrayList<>();
        for (Managed m : Managed.values()) {
            counts.add(m.capped() ? c.count(m) : 0);
            caps.add(m.capped() ? m.cap() : -1);
            enabled.add(m.enabled());
        }
        return new CapSync(counts, caps, enabled);
    }

    static void send(ServerPlayer p) {
        PacketDistributor.sendToPlayer(p, of(p.server));
    }

    /** Safe from any thread; does nothing without a running server. */
    static void broadcast() {
        MinecraftServer server = ServerLifecycleHooks.getCurrentServer();
        if (server != null) server.execute(() -> PacketDistributor.sendToAllPlayers(of(server)));
    }
}
