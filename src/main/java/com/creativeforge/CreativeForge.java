package com.creativeforge;

import com.mojang.logging.LogUtils;
import com.simibubi.create.content.processing.recipe.ProcessingOutput;
import com.simibubi.create.content.processing.sequenced.SequencedAssemblyRecipe;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.common.Mod;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.fml.config.ModConfig;
import net.neoforged.fml.event.config.ModConfigEvent;
import net.neoforged.fml.loading.FMLEnvironment;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.registries.DeferredRegister;
import org.slf4j.Logger;

@Mod(CreativeForge.MODID)
public class CreativeForge {
    public static final String MODID = "creativeforge";
    public static final Logger LOGGER = LogUtils.getLogger();
    private static final ResourceLocation MECHANICAL_CRAFTING = ResourceLocation.fromNamespaceAndPath("create", "mechanical_crafting");

    private static final DeferredRegister<CreativeModeTab> TABS = DeferredRegister.create(Registries.CREATIVE_MODE_TAB, MODID);

    static {
        TABS.register("main", () -> CreativeModeTab.builder()
                .title(Component.translatable("itemGroup.creativeforge"))
                .icon(() -> new ItemStack(ModItems.SINGULARITY_CORE.get()))
                .displayItems((p, out) -> ModItems.ALL.forEach(i -> out.accept(i.get())))
                .build());
    }

    public CreativeForge(IEventBus modBus, ModContainer container) {
        ModItems.ITEMS.register(modBus);
        TABS.register(modBus);
        container.registerConfig(ModConfig.Type.SERVER, Config.SPEC);
        NeoForge.EVENT_BUS.addListener(RegisterCommandsEvent.class, e -> Commands.register(e.getDispatcher()));
        NeoForge.EVENT_BUS.addListener(ServerStartedEvent.class, e -> audit(e.getServer()));
        modBus.addListener(RegisterPayloadHandlersEvent.class, CapSync::register);
        modBus.addListener(ModConfigEvent.Reloading.class, e -> {
            if (e.getConfig().getSpec() == Config.SPEC) CapSync.broadcast();
        });
        NeoForge.EVENT_BUS.addListener(PlayerEvent.PlayerLoggedInEvent.class, e -> {
            if (e.getEntity() instanceof ServerPlayer p) CapSync.send(p);
        });
        if (FMLEnvironment.dist == Dist.CLIENT) ClientHooks.register();
    }

    /** Managed items may only come out of create:mechanical_crafting, where the mixin enforces caps. */
    static List<ResourceLocation> audit(MinecraftServer server) {
        List<ResourceLocation> bad = new ArrayList<>();
        for (RecipeHolder<?> holder : server.getRecipeManager().getRecipes()) {
            Recipe<?> r = holder.value();
            if (MECHANICAL_CRAFTING.equals(BuiltInRegistries.RECIPE_TYPE.getKey(r.getType()))) continue;
            List<ItemStack> outputs = new ArrayList<>();
            outputs.add(r.getResultItem(server.registryAccess()));
            if (r instanceof SequencedAssemblyRecipe sa) sa.resultPool.stream().map(ProcessingOutput::getStack).forEach(outputs::add);
            for (ItemStack out : outputs) {
                Managed m = Managed.of(out);
                if (m == null) continue;
                LOGGER.error("Recipe {} ({}) outputs managed item {} outside create:mechanical_crafting; the cap does not apply to it",
                        holder.id(), BuiltInRegistries.RECIPE_TYPE.getKey(r.getType()), m.id);
                bad.add(holder.id());
                break;
            }
        }
        if (!bad.isEmpty() && Config.STRICT_AUDIT.get())
            throw new IllegalStateException("creativeforge strictAudit: recipes bypass the creative item caps: " + bad);
        LOGGER.info("creativeforge recipe audit done, {} problem recipe(s)", bad.size());
        return bad;
    }
}
