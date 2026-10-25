package com.creativeforge.mixin;

import com.creativeforge.CraftCounter;
import com.creativeforge.Managed;
import com.simibubi.create.content.kinetics.crafter.RecipeGridHandler;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(RecipeGridHandler.class)
public class RecipeGridHandlerMixin {
    // null (not EMPTY) is Create's "no recipe" signal: MechanicalCrafterBlockEntity then ejects the grid intact.
    // EMPTY would consume the grid. Create only calls this on the server (virtual/ponder crafters use scriptedResult).
    @Inject(method = "tryToApplyRecipe", at = @At("RETURN"), cancellable = true)
    private static void creativeforge$capResult(Level level, RecipeGridHandler.GroupedItems items, CallbackInfoReturnable<ItemStack> cir) {
        ItemStack stack = cir.getReturnValue();
        Managed m = Managed.of(stack);
        if (m == null) return;
        if (!(level instanceof ServerLevel sl) || !CraftCounter.get(sl.getServer()).tryMint(m, stack.getCount()))
            cir.setReturnValue(null);
    }
}
