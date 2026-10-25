package com.creativeforge;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import com.mojang.brigadier.exceptions.DynamicCommandExceptionType;
import java.util.Arrays;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.network.chat.Component;

import static net.minecraft.commands.Commands.argument;
import static net.minecraft.commands.Commands.literal;

public final class Commands {
    private static final DynamicCommandExceptionType UNKNOWN =
            new DynamicCommandExceptionType(k -> Component.literal("Unknown capped item: " + k));

    public static void register(CommandDispatcher<CommandSourceStack> d) {
        d.register(literal("creativeforge").requires(s -> s.hasPermission(2))
                .then(literal("counts").executes(Commands::counts))
                .then(literal("set").then(item().then(argument("n", IntegerArgumentType.integer(0))
                        .executes(c -> set(c, IntegerArgumentType.getInteger(c, "n"))))))
                .then(literal("reset").then(item().executes(c -> set(c, 0)))));
    }

    private static com.mojang.brigadier.builder.RequiredArgumentBuilder<CommandSourceStack, String> item() {
        return argument("item", StringArgumentType.word()).suggests((c, b) -> SharedSuggestionProvider.suggest(
                Arrays.stream(Managed.values()).filter(Managed::capped).map(m -> m.key), b));
    }

    private static int counts(CommandContext<CommandSourceStack> c) {
        CraftCounter counter = CraftCounter.get(c.getSource().getServer());
        for (Managed m : Managed.values()) {
            String line = m.key + ": " + (m.capped() ? counter.count(m) + "/" + m.cap() : "uncapped")
                    + (m.enabled() ? "" : " (disabled)");
            c.getSource().sendSuccess(() -> Component.literal(line), false);
        }
        return 1;
    }

    private static int set(CommandContext<CommandSourceStack> c, int n) throws CommandSyntaxException {
        String key = StringArgumentType.getString(c, "item");
        Managed m = Managed.byKey(key);
        if (m == null || !m.capped()) throw UNKNOWN.create(key);
        CraftCounter.get(c.getSource().getServer()).set(m, n);
        c.getSource().sendSuccess(() -> Component.literal(m.key + " count set to " + n), true);
        return n;
    }

    private Commands() {}
}
