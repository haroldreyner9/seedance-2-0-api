#!/usr/bin/env bash
# First + last frame at 4K: only seedance-2.0 renders 4K.
#   bash examples/curl/first_last_frame_4k.sh https://.../dawn.jpg https://.../noon.jpg
# 5 s at 4K = 5 x $0.58 = $2.90 (2026-10-07 rate).
set -euo pipefail
: "${SEEDANCE_API_KEY:?export SEEDANCE_API_KEY first}"
BASE="${SEEDANCE_BASE_URL:-https://argolink.io/v1}"
FIRST="${1:?usage: first_last_frame_4k.sh FIRST_URL LAST_URL}"
LAST="${2:?usage: first_last_frame_4k.sh FIRST_URL LAST_URL}"

# "adaptive" keeps the first frame's shape (closest of the six ratios).
# A fixed ratio such as "16:9" would crop the first frame instead.
BODY=$(jq -n --arg first "$FIRST" --arg last "$LAST" '{
  model: "seedance-2.0",
  prompt: "Shadows shorten as the sun climbs over the same valley; slow time-lapse feel, fixed camera, no text on screen",
  duration: 5,
  resolution: "4k",
  aspect_ratio: "adaptive",
  start_image: {url: $first},
  end_image: {url: $last}
}')

REQUEST_ID=$(curl -fsS "$BASE/videos/generations" \
  -H "Authorization: Bearer $SEEDANCE_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$BODY" | jq -er .request_id)

bash "$(dirname "$0")/wait_and_download.sh" "$REQUEST_ID" valley-4k.mp4
