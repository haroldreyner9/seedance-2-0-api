"""Reference mode: a character image, a motion clip and a voice line in one request.

    python examples/python/reference_to_video.py

Name each asset in the prompt as @Image 1, @Video 1, @Audio 1 (numbered from 1
within its own list). Limits on the 2.0 family: 9 images, 3 videos, 3 audio
clips, 15 assets in total; audio needs at least one image or video beside it.

Billing: the 3.5 s reference video adds 3 s (fractions dropped), so this
6-second 720p job bills 9 s x $0.11 = $0.99 at the 2026-10-07 rate.
"""
import json

from seedance_job import SeedanceJob

job = SeedanceJob().run(
    {
        "model": "seedance-2.0",
        "prompt": (
            "The chef in @Image 1 plates a dessert at a steel counter, copying the hand movements of @Video 1. "
            "She looks up and says {Service!} in the warm, slightly husky voice of @Audio 1. "
            "Medium close-up, fixed camera, soft kitchen light, no text on screen."
        ),
        "duration": 6,
        "resolution": "720p",
        "aspect_ratio": "9:16",
        "reference_images": [{"url": "https://example.com/chef-headshot.png"}],
        "reference_videos": [{"url": "https://example.com/plating-3-5s.mp4"}],
        "reference_audios": [{"url": "https://example.com/voice-line.mp3"}],
    },
    "chef.mp4",
)
print(json.dumps(job.get("usage", {})))  # expect billed_seconds = 6 + 3
