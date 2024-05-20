import { Telegraf, type Context } from "telegraf";
import type { Update } from "telegraf/typings/core/types/typegram";

const bot = new Telegraf(process.env.BOT_TOKEN!);
bot.start((ctx: Context) => ctx.reply("Welcome"));

console.log("Hello via Bun!");

// Enable graceful stop
process.once("SIGINT", () => bot.stop("SIGINT"));
process.once("SIGTERM", () => bot.stop("SIGTERM"));

/**
 *
 * @param event TODO
 * @param context
 */
export async function handler(event: any, _context: Context) {
  const message: Update = JSON.parse(event.body);
  await bot.handleUpdate(message);
  return {
    statusCode: 200,
    body: "",
  };
}
