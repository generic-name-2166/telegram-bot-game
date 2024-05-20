import { Telegraf, type Context } from "telegraf";
import { message } from "telegraf/filters";
import type { YC } from "./yc.ts";

const bot = new Telegraf(process.env.BOT_TOKEN!);
bot.start((ctx: Context) => ctx.reply("Welcome"));
bot.help((ctx: Context) => ctx.reply("Game bot"));
bot.use((ctx: Context) => {
  ctx.has(message("text")) ? ctx.reply(ctx.message.text) : ctx.reply("Error");
});

// Enable graceful stop
process.once("SIGINT", () => bot.stop("SIGINT"));
process.once("SIGTERM", () => bot.stop("SIGTERM"));

export.handler = async function(
  event: YC.CloudFunctionsHttpEvent,
  _context: YC.CloudFunctionsHttpContext,
) {
  //@ts-expect-error
  const { api_key, format, fields, brands } = event.queryStringParameters;

  /* if (!api_key) {
    return {
      statusCode: 400,
      headers: { 'Content-Type': 'application/json; charset=utf-8' },
      body: { error: 'Вам необходимо указать параметр api_key' },
      isBase64Encoded: false,
    };
  } */

  const message = JSON.parse(event.body ?? "");
  await bot.handleUpdate(message);
  return {
    statusCode: 200,
    body: "",
  };
}
