// Text to video on Seedance 2.0 Mini, the cheapest tier: 480p or 720p only.
//
//   node examples/node/text_to_video.mjs ["your prompt"]
//
// 6 s at 480p bills 6 x $0.026 = $0.156 at the 2026-10-07 rate.

import { SeedanceJob } from "./seedance_job.mjs";

const prompt =
  process.argv[2] ??
  "A red vintage tram climbs a steep street at golden hour, side tracking shot, passengers wave, <tram bell rings>";

const job = await new SeedanceJob().run(
  { model: "seedance-2.0-mini", prompt, duration: 6, resolution: "480p", aspect_ratio: "16:9" },
  "tram.mp4",
);
console.log(JSON.stringify(job.usage ?? {}));
