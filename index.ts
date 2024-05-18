import { Telegraf, type Context } from "telegraf";

const bot = new Telegraf("secret token");
bot.start((ctx: Context) => ctx.reply("Welcome"));

console.log("Hello via Bun!");
