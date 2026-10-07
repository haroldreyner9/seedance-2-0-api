// Reference mode with two images: one fixes the product, the other the setting.
//
//   node examples/node/reference_to_video.mjs
//
// Reference images are free; only output seconds bill here: 10 x $0.11 = $1.10.

import { SeedanceJob } from "./seedance_job.mjs";

const job = await new SeedanceJob().run(
  {
    model: "seedance-2.0",
    prompt:
      "The watch in @Image 1 rests on the marble shelf from @Image 2. Shot 1: slow push-in on the dial as the second hand moves. " +
      "Shot 2: cut to a close-up of the strap buckle catching the light. Studio lighting, rich details, do not generate a logo.",
    duration: 10,
    resolution: "720p",
    aspect_ratio: "1:1",
    reference_images: [{ url: "https://example.com/watch.png" }, { url: "https://example.com/marble-shelf.jpg" }],
  },
  "watch.mp4",
);
console.log(JSON.stringify(job.usage ?? {}));
