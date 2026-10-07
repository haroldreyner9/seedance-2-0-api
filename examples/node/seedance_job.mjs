// Seedance 2.0 job runner for Node.js 18+ (built-in fetch, no packages).
// Used by the other Node examples:
//
//   export SEEDANCE_API_KEY=...            # required
//   export SEEDANCE_BASE_URL=...           # optional, defaults to https://argolink.io/v1

import { createWriteStream } from "node:fs";
import { Readable } from "node:stream";
import { pipeline } from "node:stream/promises";

const DEFAULT_BASE_URL = "https://argolink.io/v1";

export class JobError extends Error {
  constructor(message, payload) {
    super(message);
    this.payload = payload;
  }
}

export class SeedanceJob {
  constructor({ apiKey = process.env.SEEDANCE_API_KEY, baseUrl = process.env.SEEDANCE_BASE_URL || DEFAULT_BASE_URL } = {}) {
    if (!apiKey) throw new JobError("SEEDANCE_API_KEY is not set");
    this.apiKey = apiKey;
    this.baseUrl = baseUrl.replace(/\/+$/, "");
  }

  async #call(method, path, body) {
    const response = await fetch(this.baseUrl + path, {
      method,
      headers: { Authorization: `Bearer ${this.apiKey}`, ...(body ? { "Content-Type": "application/json" } : {}) },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!response.ok) {
      const text = await response.text();
      throw new JobError(`${method} ${path} returned HTTP ${response.status}: ${text.slice(0, 300)}`, text);
    }
    return response;
  }

  /** POST /videos/generations; resolves to the request_id. */
  async submit(body) {
    return (await (await this.#call("POST", "/videos/generations", body)).json()).request_id;
  }

  async status(requestId) {
    return (await this.#call("GET", `/videos/${requestId}`)).json();
  }

  /** Poll every `everyMs` until the job is done; throws on failed or expired. */
  async wait(requestId, { everyMs = 10_000, giveUpAfterMs = 60 * 60 * 1000 } = {}) {
    const started = Date.now();
    for (;;) {
      const job = await this.status(requestId);
      if (job.status === "done") return job;
      if (job.status === "failed" || job.status === "expired") {
        throw new JobError(`job ${requestId} ${job.status}: ${job.error?.code ?? ""} ${job.error?.message ?? ""}`.trim(), job);
      }
      console.error(`  ${job.status} ${job.progress ?? 0}%`);
      if (Date.now() - started > giveUpAfterMs) throw new JobError(`job ${requestId} still ${job.status}`, job);
      await new Promise((resolve) => setTimeout(resolve, everyMs));
    }
  }

  /** Stream GET /videos/{id}/content into a file. */
  async save(requestId, path) {
    const response = await this.#call("GET", `/videos/${requestId}/content`);
    await pipeline(Readable.fromWeb(response.body), createWriteStream(path));
    return path;
  }

  async run(body, path) {
    const requestId = await this.submit(body);
    console.error(`request_id ${requestId}`);
    const job = await this.wait(requestId);
    await this.save(requestId, path);
    return job;
  }
}
