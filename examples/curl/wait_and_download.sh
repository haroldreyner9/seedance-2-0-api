#!/usr/bin/env bash
# Poll a Seedance 2.0 job until it leaves "pending", then save the MP4.
#   bash examples/curl/wait_and_download.sh REQUEST_ID [output.mp4]
set -euo pipefail
: "${SEEDANCE_API_KEY:?export SEEDANCE_API_KEY first}"
BASE="${SEEDANCE_BASE_URL:-https://argolink.io/v1}"
REQUEST_ID="${1:?usage: wait_and_download.sh REQUEST_ID [output.mp4]}"
OUT="${2:-$REQUEST_ID.mp4}"

while :; do
  JOB=$(curl -fsS "$BASE/videos/$REQUEST_ID" -H "Authorization: Bearer $SEEDANCE_API_KEY")
  STATUS=$(jq -r .status <<<"$JOB")
  case "$STATUS" in
    done) break ;;
    failed | expired)
      echo "job $STATUS:" >&2
      jq .error <<<"$JOB" >&2 # code, message, retryable, field
      exit 1 ;;
    *)
      echo "$STATUS $(jq -r '.progress // 0' <<<"$JOB")%" >&2
      sleep 10 ;;
  esac
done

curl -fsSL "$BASE/videos/$REQUEST_ID/content" -H "Authorization: Bearer $SEEDANCE_API_KEY" -o "$OUT"
echo "saved $OUT" >&2
jq .usage <<<"$JOB"
