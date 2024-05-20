import * as fs from "node:fs/promises";

const OUTPUT_DIR: string = ".out";

await fs.rm(OUTPUT_DIR, { recursive: true });

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
} else {
  console.log("Success");
}
