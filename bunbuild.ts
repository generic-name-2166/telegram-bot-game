import { $ } from "bun";
import * as fs from "node:fs/promises";

const OUTPUT_DIR: string = ".out";

async function clearOutdir(): Promise<void> {
  await fs.rm(OUTPUT_DIR, { recursive: true });
}

async function copyAssets(): Promise<void> {
  // Bun file I/O has undocumented ENOENT
  return fs.copyFile("assets/out.package.json", OUTPUT_DIR + "/package.json");
}

async function main(): Promise<void> {
  await clearOutdir();

  const result = await Bun.build({
    entrypoints: ["src/index.ts"],
    outdir: OUTPUT_DIR,
    target: "node",
    format: "esm", // cjs
    minify: true,
    naming: "[dir]/[name].[ext]",
  });
  
  if (!result.success) {
    console.error("Build failed");
    for (const message of result.logs) {
      // Bun will pretty print the message object
      console.error(message);
    }
    return;
  }

  await copyAssets();

  console.log("Build success");
}

await main();
