import test from "node:test";
import assert from "node:assert/strict";

import {
  JBS_ACTIONS,
  JBS_HEADERS,
  JBS_PHASES,
  JBS_STREAM_MODES,
  parseJBSState,
  parseJBSStreamPayload,
} from "../src/jinja-bootstrap-spa.js";

test("runtime constants expose the public request contract", () => {
  assert.equal(JBS_HEADERS.marker, "X-JBS-Request");
  assert.equal(JBS_HEADERS.state, "X-JBS-State");
  assert.equal(JBS_ACTIONS.refresh, "refresh");
  assert.equal(JBS_STREAM_MODES.append, "append");
  assert.equal(JBS_PHASES.unchanged, "unchanged");
});

test("parseJBSState tolerates empty or malformed serialized state", () => {
  assert.deepEqual(parseJBSState(null), {});
  assert.deepEqual(parseJBSState(""), {});
  assert.deepEqual(parseJBSState("{not-json"), {});
});

test("parseJBSState preserves scalar and multi-value component state", () => {
  assert.deepEqual(
    parseJBSState('{"page":2,"query":"ada","status":["open","queued"]}'),
    {
      page: 2,
      query: "ada",
      status: ["open", "queued"],
    },
  );
});

test("parseJBSStreamPayload handles delta stream payloads", () => {
  assert.deepEqual(
    parseJBSStreamPayload(
      JSON.stringify({
        v: 1,
        target: "orders-table",
        mode: "prepend",
        seq: 42,
        ops: [{ op: "upsert", id: "order-42", html: "<tr></tr>" }],
      }),
    ),
    {
      v: 1,
      target: "orders-table",
      mode: "prepend",
      seq: 42,
      ops: [{ op: "upsert", id: "order-42", html: "<tr></tr>" }],
    },
  );
});

test("parseJBSStreamPayload falls back to an empty payload on invalid input", () => {
  assert.deepEqual(parseJBSStreamPayload(""), {});
  assert.deepEqual(parseJBSStreamPayload("not-json"), {});
});
