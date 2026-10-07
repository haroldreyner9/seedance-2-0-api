"""First frame (and optionally a last frame) to video.

    python examples/python/image_to_video.py first.png [last.png]

Local files are uploaded first; an HTTPS URL you already host works too.
With "adaptive" the video takes the ratio closest to the first frame; a fixed
ratio such as "9:16" crops the frame instead. Frames cannot be mixed with
reference_images / reference_videos / reference_audios in one request.
"""
import json
import sys

from seedance_job import SeedanceJob

if len(sys.argv) < 2:
    sys.exit("usage: python image_to_video.py first.png [last.png]")

client = SeedanceJob()


def as_url(path_or_url: str) -> str:
    if path_or_url.startswith("https://"):
        return path_or_url
    content_type = "image/png" if path_or_url.lower().endswith(".png") else "image/jpeg"
    return client.upload(path_or_url, "image", content_type, model="seedance-2.0-fast")


body = {
    "model": "seedance-2.0-fast",  # 480p/720p only; $0.091/s at 720p
    "prompt": "The camera pushes in slowly as steam rises from the cup and the morning light shifts across the table",
    "duration": 5,
    "resolution": "720p",
    "aspect_ratio": "adaptive",
    "start_image": {"url": as_url(sys.argv[1])},
}
if len(sys.argv) > 2:
    body["end_image"] = {"url": as_url(sys.argv[2])}

job = client.run(body, "from-frames.mp4")
print(json.dumps(job.get("usage", {})))
