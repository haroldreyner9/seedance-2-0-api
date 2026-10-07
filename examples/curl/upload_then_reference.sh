#!/usr/bin/env bash
# Upload a local image and audio clip, then use both as references.
#   bash examples/curl/upload_then_reference.sh portrait.png line.mp3
# Audio cannot be the only reference on the 2.0 family, so an image goes with it.
set -euo pipefail
: "${SEEDANCE_API_KEY:?export SEEDANCE_API_KEY first}"
BASE="${SEEDANCE_BASE_URL:-https://argolink.io/v1}"
IMAGE="${1:?usage: upload_then_reference.sh IMAGE.png AUDIO.mp3}"
AUDIO="${2:?usage: upload_then_reference.sh IMAGE.png AUDIO.mp3}"

content_type() {
  case "$(tr '[:upper:]' '[:lower:]' <<<"${1##*.}")" in
    png) echo image/png ;;
    jpg | jpeg) echo image/jpeg ;;
    mp3) echo audio/mpeg ;;
    wav) echo audio/wav ;;
    *) echo "unsupported file type: $1 (use PNG/JPEG images, MP3/WAV audio)" >&2; exit 1 ;;
  esac
}

# A ticket is free and creates no job. upload_url lasts 15 minutes; media_url 7 days.
upload() { # upload FILE TYPE -> prints media_url
  local ticket mime
  mime=$(content_type "$1")
  ticket=$(curl -fsS "$BASE/media/uploads" \
    -H "Authorization: Bearer $SEEDANCE_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"seedance-2.0\",\"type\":\"$2\",\"content_type\":\"$mime\",\"size_bytes\":$(wc -c <"$1" | tr -d ' ')}")
  # The PUT must carry exactly the Content-Type declared in the ticket.
  curl -fsS -X PUT "$(jq -r .upload_url <<<"$ticket")" -H "Content-Type: $mime" --data-binary @"$1" >/dev/null
  jq -r .media_url <<<"$ticket"
}

IMAGE_URL=$(upload "$IMAGE" image)
AUDIO_URL=$(upload "$AUDIO" audio)

BODY=$(jq -n --arg img "$IMAGE_URL" --arg aud "$AUDIO_URL" '{
  model: "seedance-2.0",
  prompt: "The woman in @Image 1 looks into the camera and speaks the line from @Audio 1 in the same calm voice, natural lip movement, soft window light",
  duration: 5,
  resolution: "720p",
  aspect_ratio: "9:16",
  reference_images: [{url: $img}],
  reference_audios: [{url: $aud}]
}')

REQUEST_ID=$(curl -fsS "$BASE/videos/generations" \
  -H "Authorization: Bearer $SEEDANCE_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$BODY" | jq -er .request_id)

bash "$(dirname "$0")/wait_and_download.sh" "$REQUEST_ID" talking.mp4
