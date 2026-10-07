"""Run one Seedance 2.0 job end to end: submit, poll, save the MP4.

The other Python examples import this file. It needs `requests`:

    pip install requests
    export SEEDANCE_API_KEY=...            # required
    export SEEDANCE_BASE_URL=...           # optional, defaults to https://argolink.io/v1
"""
from __future__ import annotations

import os
import sys
import time

import requests

DEFAULT_BASE_URL = "https://argolink.io/v1"
POLL_EVERY_SECONDS = 10  # the API docs suggest polling every 10-15 s


class JobError(RuntimeError):
    """The API refused a request, or a job ended as failed or expired."""

    def __init__(self, message: str, payload: object = None):
        super().__init__(message)
        self.payload = payload


class SeedanceJob:
    def __init__(self, api_key: str | None = None, base_url: str | None = None, http: requests.Session | None = None):
        key = api_key or os.environ.get("SEEDANCE_API_KEY")
        if not key:
            raise JobError("SEEDANCE_API_KEY is not set")
        self.base_url = (base_url or os.environ.get("SEEDANCE_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.http = http or requests.Session()
        self.http.headers["Authorization"] = f"Bearer {key}"

    def _check(self, response: requests.Response, what: str) -> requests.Response:
        if response.status_code >= 400:
            try:
                payload = response.json()
            except ValueError:
                payload = response.text
            raise JobError(f"{what} returned HTTP {response.status_code}: {str(payload)[:300]}", payload)
        return response

    def submit(self, body: dict) -> str:
        """POST /videos/generations. Returns the request_id (the API answers 202)."""
        response = self.http.post(f"{self.base_url}/videos/generations", json=body, timeout=60)
        return self._check(response, "submit").json()["request_id"]

    def status(self, request_id: str) -> dict:
        response = self.http.get(f"{self.base_url}/videos/{request_id}", timeout=60)
        return self._check(response, "status").json()

    def wait(self, request_id: str, every: float = POLL_EVERY_SECONDS, give_up_after: float = 3600) -> dict:
        """Poll until status leaves `pending`. Returns the job when it is `done`."""
        started = time.monotonic()
        while True:
            job = self.status(request_id)
            state = job.get("status")
            if state == "done":
                return job
            if state in ("failed", "expired"):
                error = job.get("error") or {}
                raise JobError(f"job {request_id} {state}: {error.get('code', '')} {error.get('message', '')}".strip(), job)
            left = job.get("estimated_seconds_remaining")
            print(f"  {state} {job.get('progress', 0)}%" + (f", about {left}s left" if left else ""), file=sys.stderr)
            if time.monotonic() - started > give_up_after:
                raise JobError(f"job {request_id} still {state} after {give_up_after:.0f}s; poll it again later", job)
            time.sleep(every)

    def save(self, request_id: str, path: str) -> str:
        """GET /videos/{request_id}/content and write the MP4 to `path`."""
        response = self.http.get(f"{self.base_url}/videos/{request_id}/content", timeout=600, stream=True)
        self._check(response, "download")
        with open(path, "wb") as out:
            for chunk in response.iter_content(chunk_size=1 << 20):
                out.write(chunk)
        return path

    def upload(self, file_path: str, kind: str, content_type: str, model: str = "seedance-2.0") -> str:
        """Upload a local image, video or audio file; returns the media_url to put in a request."""
        ticket = self._check(
            self.http.post(
                f"{self.base_url}/media/uploads",
                json={"model": model, "type": kind, "content_type": content_type, "size_bytes": os.path.getsize(file_path)},
                timeout=60,
            ),
            "upload ticket",
        ).json()
        with open(file_path, "rb") as data:
            # The PUT goes straight to storage, so it must not carry the API key.
            put = requests.put(ticket["upload_url"], data=data, headers={"Content-Type": content_type}, timeout=600)
        if put.status_code >= 400:
            raise JobError(f"upload PUT returned HTTP {put.status_code}", put.text)
        return ticket["media_url"]

    def run(self, body: dict, path: str) -> dict:
        """Submit `body`, wait for the result, save it to `path`. Returns the finished job."""
        request_id = self.submit(body)
        print(f"request_id {request_id}", file=sys.stderr)
        job = self.wait(request_id)
        self.save(request_id, path)
        return job
