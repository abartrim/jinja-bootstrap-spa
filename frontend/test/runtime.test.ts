import test from "node:test";
import assert from "node:assert/strict";

import {
  JBS_ACTIONS,
  JBS_HEADERS,
  JBS_PERSISTENCE,
  JBS_PHASES,
  JBS_STREAM_EVENTS,
  JBS_STREAM_MODES,
  JBS_UI_PERSISTENCE,
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

test("JBS_HEADERS exposes all expected header name constants", () => {
  assert.equal(JBS_HEADERS.accept, "text/html");
  assert.equal(JBS_HEADERS.marker, "X-JBS-Request");
  assert.equal(JBS_HEADERS.component, "X-JBS-Component");
  assert.equal(JBS_HEADERS.action, "X-JBS-Action");
  assert.equal(JBS_HEADERS.state, "X-JBS-State");
  assert.equal(JBS_HEADERS.ifNoneMatch, "If-None-Match");
  assert.equal(JBS_HEADERS.etag, "ETag");
});

test("JBS_ACTIONS exposes all action name constants", () => {
  assert.equal(JBS_ACTIONS.filter, "filter");
  assert.equal(JBS_ACTIONS.page, "page");
  assert.equal(JBS_ACTIONS.refresh, "refresh");
  assert.equal(JBS_ACTIONS.row, "row");
  assert.equal(JBS_ACTIONS.sort, "sort");
});

test("JBS_PERSISTENCE exposes all persistence strategy constants", () => {
  assert.equal(JBS_PERSISTENCE.memory, "memory");
  assert.equal(JBS_PERSISTENCE.querystring, "querystring");
  assert.equal(JBS_PERSISTENCE.session, "session");
  assert.equal(JBS_PERSISTENCE.header, "header");
});

test("JBS_UI_PERSISTENCE exposes all UI persistence strategy constants", () => {
  assert.equal(JBS_UI_PERSISTENCE.memory, "memory");
  assert.equal(JBS_UI_PERSISTENCE.session, "session");
  assert.equal(JBS_UI_PERSISTENCE.local, "local");
  assert.equal(JBS_UI_PERSISTENCE.none, "none");
});

test("JBS_STREAM_EVENTS exposes the refresh event constant", () => {
  assert.equal(JBS_STREAM_EVENTS.refresh, "refresh");
});

test("JBS_STREAM_MODES exposes all stream mode constants", () => {
  assert.equal(JBS_STREAM_MODES.replace, "replace");
  assert.equal(JBS_STREAM_MODES.append, "append");
  assert.equal(JBS_STREAM_MODES.prepend, "prepend");
});

test("JBS_PHASES exposes all phase constants", () => {
  assert.equal(JBS_PHASES.idle, "idle");
  assert.equal(JBS_PHASES.loading, "loading");
  assert.equal(JBS_PHASES.success, "success");
  assert.equal(JBS_PHASES.unchanged, "unchanged");
  assert.equal(JBS_PHASES.error, "error");
});

test("parseJBSState tolerates empty or malformed serialized state", () => {
  assert.deepEqual(parseJBSState(null), {});
  assert.deepEqual(parseJBSState(""), {});
  assert.deepEqual(parseJBSState("{not-json"), {});
});

test("parseJBSState returns empty object for JSON null value", () => {
  assert.deepEqual(parseJBSState("null"), {});
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

test("parseJBSStreamPayload handles minimal snapshot payload", () => {
  const payload = parseJBSStreamPayload(
    JSON.stringify({ v: 1, snapshot: "<table></table>", seq: 1 }),
  );
  assert.equal(payload.v, 1);
  assert.equal(payload.snapshot, "<table></table>");
  assert.equal(payload.seq, 1);
});

test("parseJBSStreamPayload falls back to an empty payload on invalid input", () => {
  assert.deepEqual(parseJBSStreamPayload(""), {});
  assert.deepEqual(parseJBSStreamPayload("not-json"), {});
});

