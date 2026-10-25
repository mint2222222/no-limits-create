package com.creativeforge;

import com.simibubi.create.content.processing.sequenced.SequencedAssemblyItem;
import java.util.List;
import net.minecraft.world.item.Item;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;

public final class ModItems {
    public static final DeferredRegister.Items ITEMS = DeferredRegister.createItems(CreativeForge.MODID);

    public static final DeferredItem<Item> SINGULARITY_CORE = ITEMS.registerSimpleItem("singularity_core");
    public static final DeferredItem<Item> RESONANT_LATTICE = ITEMS.registerSimpleItem("resonant_lattice");
    public static final DeferredItem<Item> QUANTUM_CIRCUIT = ITEMS.registerSimpleItem("quantum_circuit");
    public static final DeferredItem<Item> FLUX_ALLOY = ITEMS.registerSimpleItem("flux_alloy");
    public static final DeferredItem<Item> FLUX_MATRIX = ITEMS.registerSimpleItem("flux_matrix");

    public static final DeferredItem<SequencedAssemblyItem> INCOMPLETE_RESONANT_LATTICE = incomplete("resonant_lattice");
    public static final DeferredItem<SequencedAssemblyItem> INCOMPLETE_QUANTUM_CIRCUIT = incomplete("quantum_circuit");
    public static final DeferredItem<SequencedAssemblyItem> INCOMPLETE_FLUX_MATRIX = incomplete("flux_matrix");
    public static final DeferredItem<SequencedAssemblyItem> INCOMPLETE_SINGULARITY_CORE = incomplete("singularity_core");
    public static final DeferredItem<SequencedAssemblyItem> INCOMPLETE_CHROMATIC_COMPOUND = incomplete("chromatic_compound");

    public static final List<DeferredItem<? extends Item>> ALL = List.of(
            SINGULARITY_CORE, RESONANT_LATTICE, QUANTUM_CIRCUIT, FLUX_ALLOY, FLUX_MATRIX,
            INCOMPLETE_RESONANT_LATTICE, INCOMPLETE_QUANTUM_CIRCUIT, INCOMPLETE_FLUX_MATRIX, INCOMPLETE_SINGULARITY_CORE,
            INCOMPLETE_CHROMATIC_COMPOUND);

    private static DeferredItem<SequencedAssemblyItem> incomplete(String name) {
        return ITEMS.register("incomplete_" + name, () -> new SequencedAssemblyItem(new Item.Properties()));
    }

    private ModItems() {}
}
