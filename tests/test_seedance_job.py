"""Offline tests for examples/python/seedance_job.py: a fake HTTP session replaces the API."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "examples", "python"))
import seedance_job  # noqa: E402


class FakeResponse:
    def __init__(self, status_code=200, payload=None, body=b""):
        self.status_code = status_code
        self._payload = payload
        self._body = body
        self.text = json.dumps(payload) if payload is not None else body.decode()

    def json(self):
        if self._payload is None:
            raise ValueError("no JSON")
        return self._payload

    def iter_content(self, chunk_size=1):
        yield self._body


class FakeSession:
    """Answers like the Seedance video API; records every call."""

    def __init__(self, states):
        self.headers = {}
        self.states = list(states)
        self.calls = []

    def post(self, url, json=None, timeout=None):
        self.calls.append(("POST", url, json))
        if url.endswith("/videos/generations"):
            return FakeResponse(202, {"request_id": "req-42"})
        if url.endswith("/media/uploads"):
            return FakeResponse(200, {"upload_url": "https://storage.test/put", "media_url": "https://media.test/a.png"})
        raise AssertionError(url)

    def get(self, url, timeout=None, stream=False):
        self.calls.append(("GET", url, None))
        if url.endswith("/content"):
            return FakeResponse(200, body=b"\x00\x00\x00\x18ftypmp42")
        return FakeResponse(200, self.states.pop(0))


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(seedance_job.time, "sleep", lambda seconds: None)


def test_run_submits_polls_and_saves(tmp_path):
    http = FakeSession([
        {"request_id": "req-42", "status": "pending", "progress": 0},
        {"request_id": "req-42", "status": "pending", "progress": 61, "estimated_seconds_remaining": 40},
        {"request_id": "req-42", "status": "done", "progress": 100,
         "usage": {"output_seconds": 6, "reference_video_seconds": 3, "billed_seconds": 9}},
    ])
    client = seedance_job.SeedanceJob(api_key="k", http=http)
    body = {"model": "seedance-2.0", "prompt": "a chef plates dessert", "duration": 6}
    job = client.run(body, str(tmp_path / "out.mp4"))

    assert http.headers["Authorization"] == "Bearer k"
    assert http.calls[0] == ("POST", "https://argolink.io/v1/videos/generations", body)
    assert [c[1] for c in http.calls[1:4]] == ["https://argolink.io/v1/videos/req-42"] * 3
    assert http.calls[-1][1] == "https://argolink.io/v1/videos/req-42/content"
    assert (tmp_path / "out.mp4").read_bytes().endswith(b"ftypmp42")
    assert job["usage"]["billed_seconds"] == 9


@pytest.mark.parametrize("state", ["failed", "expired"])
def test_failed_and_expired_jobs_raise_with_the_error(state):
    error = {"code": "invalid_input", "message": "reference audio needs an image or video", "retryable": False}
    http = FakeSession([{"request_id": "req-42", "status": state, "error": error}])
    with pytest.raises(seedance_job.JobError) as raised:
        seedance_job.SeedanceJob(api_key="k", http=http).wait("req-42")
    assert raised.value.payload["error"]["code"] == "invalid_input"
    assert state in str(raised.value)


def test_http_errors_keep_the_body():
    class Rejecting(FakeSession):
        def post(self, url, json=None, timeout=None):
            return FakeResponse(400, {"error": {"type": "invalid_request_error", "code": "request_unsupported",
                                                "message": "seedance-2.0-mini does not support video resolution 1080p"}})

    with pytest.raises(seedance_job.JobError) as raised:
        seedance_job.SeedanceJob(api_key="k", http=Rejecting([])).submit({"model": "seedance-2.0-mini", "resolution": "1080p"})
    assert raised.value.payload["error"]["code"] == "request_unsupported"


def test_upload_sends_size_and_puts_bytes_without_the_key(tmp_path, monkeypatch):
    image = tmp_path / "frame.png"
    image.write_bytes(b"\x89PNG" + b"0" * 96)
    puts = []
    monkeypatch.setattr(seedance_job.requests, "put", lambda url, data, headers, timeout: puts.append((url, headers)) or FakeResponse(200, {}))
    http = FakeSession([])
    url = seedance_job.SeedanceJob(api_key="k", http=http).upload(str(image), "image", "image/png", model="seedance-2.0-fast")

    assert url == "https://media.test/a.png"
    assert http.calls[0][2] == {"model": "seedance-2.0-fast", "type": "image", "content_type": "image/png", "size_bytes": 100}
    assert puts == [("https://storage.test/put", {"Content-Type": "image/png"})]


def test_base_url_comes_from_the_environment(monkeypatch):
    monkeypatch.setenv("SEEDANCE_BASE_URL", "https://example.test/v1/")
    assert seedance_job.SeedanceJob(api_key="k", http=FakeSession([])).base_url == "https://example.test/v1"


def test_missing_key_is_reported(monkeypatch):
    monkeypatch.delenv("SEEDANCE_API_KEY", raising=False)
    with pytest.raises(seedance_job.JobError):
        seedance_job.SeedanceJob(http=FakeSession([]))
