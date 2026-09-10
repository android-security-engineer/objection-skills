# Jobs, state & event polling

Action commands (hooks, monitors, bypasses) install **Jobs**. Their ids are not returned by the installing command — use these endpoints to track and control them.

## `jobs list`
- args: `(none)`
- result: `{"jobs":[{id,type,name},...],"count":<>}`

## `jobs kill <id>`
- args: `<job id integer>`
- result: `{"killed": <int>}`

## Session state

### `agent state` (CLI) / `GET /state` (HTTP)
Full session snapshot.
- result:
```json
{
  "connection": {"type":<>,"network":bool,"host":<>,"port":<>,"device_id":<>,"name":<>,"spawn":bool,"foremost":bool},
  "pid": <int|null>,
  "jobs": [{"id":<int>,"type":<>,"name":<>}]
}
```
Returns 503 (HTTP) / error (CLI) if no agent is connected.

## Event polling

### `GET /events/poll`
Drain the async event buffer (hook invocations, canary hits, pasteboard/clipboard changes, raw keychain dumps, JS eval output). **This is how you read hook hits.**
- query: `?peek=1` to view without clearing.
- result: `{"events":[{"message":<frida msg dict>,"data":<str|null>},...],"dropped":<int>,"remaining":0}`

Each event's `message` is the raw Frida message — typically `{"type":"send","payload":{...}}` where `payload` carries the hook's recorded args/return/backtrace.

> Workflow: `watch` a method → re-trigger it in the app → `GET /events/poll` to read the captured invocation.

## `agent capabilities` (CLI) / `GET /capabilities` (HTTP)
Static command-tree enumeration — no device needed. Use this first to discover what's available.
- result: `{"commands":[{"name":<>,"meta":<>,"has_exec":bool,"subcommands":[...]},...]}`

## `agent rpc <method> [--args '<json array>']` (CLI) / `GET|POST /agent/rpc/<method>` (HTTP)
Call an agent RPC export directly (bypass the human command layer). Useful when a command isn't converted to structured output yet, or you need a raw RPC.
- args: method name (snake or camel case); `--args` is a JSON array of positional args (CLI) / POST body is a JSON array (HTTP).
- result: whatever the RPC method returns, wrapped as `result`.

## `agent exec '<command>'` (CLI) / `POST /command/exec` (HTTP)
Run objection command strings. The primary entry point.
- CLI: `agent exec '<command>'`
- HTTP body: `{"command":"..."}` or `{"commands":["...",...]}` (returns an array when multiple).
- result: the unified-schema envelope with the command's `result`.
