"""Text to video: a prompt is the only required field.

    python examples/python/text_to_video.py ["your prompt"]

8 seconds at 1080p on seedance-2.0 bills 8 x $0.28 = $2.24 at the 2026-10-07 rate.
"""
import json
import sys

from seedance_job import SeedanceJob

prompt = sys.argv[1] if len(sys.argv) > 1 else (
    "Shot 1: a lighthouse keeper climbs a spiral staircase, lantern in hand, slow upward tracking shot. "
    "Shot 2: he opens the door at the top and wind pulls at his coat; wide shot of a stormy sea at dusk. "
    "(low cello drone) <waves crash below> Cinematic, natural colors, keep it subtitle-free."
)

job = SeedanceJob().run(
    {
        "model": "seedance-2.0",
        "prompt": prompt,
        "duration": 8,
        "resolution": "1080p",
        "aspect_ratio": "21:9",
    },
    "lighthouse.mp4",
)
print(json.dumps(job.get("usage", {})))  # output_seconds, reference_video_seconds, billed_seconds
