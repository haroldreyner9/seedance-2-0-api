#!/usr/bin/env bash
# Text to video with the three calls spelled out: submit, poll, download.
#   bash examples/curl/text_to_video.sh ["your prompt"]
# 5 s at 720p on seedance-2.0 = 5 x $0.11 = $0.55 (2026-10-07 rate).
set -euo pipefail
: "${SEEDANCE_API_KEY:?export SEEDANCE_API_KEY first}"
BASE="${SEEDANCE_BASE_URL:-https://argolink.io/v1}"
PROMPT="${1:-A paper boat drifts down a rain-filled gutter, low macro tracking shot, evening street lights, <rain patter>}"

BODY=$(jq -n --arg prompt "$PROMPT" '{
  model: "seedance-2.0",
  prompt: $prompt,
  duration: 5,
  resolution: "720p",
  aspect_ratio: "16:9"
}')

# 1. Submit. HTTP 202 with {"request_id": "..."}
REQUEST_ID=$(curl -fsS "$BASE/videos/generations" \
  -H "Authorization: Bearer $SEEDANCE_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$BODY" | jq -er .request_id)
echo "request_id $REQUEST_ID" >&2

# 2 + 3. Poll until done, then download the MP4
bash "$(dirname "$0")/wait_and_download.sh" "$REQUEST_ID" paper-boat.mp4
