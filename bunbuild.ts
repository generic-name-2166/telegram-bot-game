import * as fs from "node:fs/promises";
import { zip } from "zip-a-folder";

const OUTPUT_DIR: string = ".out";

async function clearOutdir(): Promise<void> {
  return fs.rm(OUTPUT_DIR, { recursive: true });
}

async function copyAssets(): Promise<void> {
  // Bun file I/O has undocumented ENOENT
  return fs.copyFile("assets/out.package.json", OUTPUT_DIR + "/package.json");
}

async function zipOutput(): Promise<void> {
  const result = await zip(OUTPUT_DIR, "out.zip");
  if (result) {
    console.error(result.name);
    console.error(result.message);
  }
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
  await zipOutput();

  console.log("Build success");
}

await main();
