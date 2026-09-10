---
name: objection
description: Runtime mobile security testing via Frida. Hook methods, dump keychain/keystore/clipboard, bypass SSL pinning & root/jailbreak detection, search memory, enumerate classes, and inspect the heap on live Android/iOS apps. Use when the user wants to dynamically instrument or extract secrets from a running mobile app.
---

# objection — Runtime Mobile Security Toolkit

objection is a Frida-based runtime exploration toolkit for Android and iOS. It injects an agent into a running (or spawned) app and exposes commands to inspect and manipulate its runtime: hook Java/ObjC methods, dump credentials and storage, bypass security checks, and search process memory.

This skill drives objection **as an AI Agent** — all commands return structured JSON you can parse and act on, not colored terminal text.

## When to use

Use this skill when the user wants to:
- **Hook a method** and watch its arguments / return value / backtrace at runtime (Android Java or iOS ObjC).
- **Extract secrets** from a live app: iOS Keychain, Android KeyStore, NSUserDefaults, cookies, pasteboard, NSURLCredentialStorage.
- **Bypass security controls**: SSL pinning, root/jailbreak detection.
- **Enumerate runtime structure**: loaded classes, class methods, registered activities/services/receivers, loaded modules, heap instances.
- **Inspect/modify memory**: search for bytes/strings, dump regions, patch or write memory.
- **Drive the heap**: find live instances, call methods on them, read fields, evaluate JS.

Do **not** use this skill for:
- Static analysis of an APK/IPA on disk (no device needed) — that's patching/decompilation tooling.
- Network-level MITM or proxying traffic — use a proxy tool; objection's `proxy set` only configures in-app proxy settings.
- Patching an APK/IPA to embed Frida (`patchapk`/`patchipa`) — these are offline build steps, run them directly, not via this skill.

## Prerequisites

objection requires a **running Frida server/gadget** on the target and a connected device/simulator:

- **Android**: `frida-server` running on device (or a gadget-patched APK), app installed. Connect over USB by default.
- **iOS**: jailbroken device with `frida-server`, or a gadget-patched IPA; or the iOS Simulator via `--local`.
- The objection package must be installed (`pip install objection`) and `objection` on PATH.

You cannot meaningfully run objection commands without a live target. If no device is reachable, tell the user what's needed (see *Troubleshooting* below) rather than guessing.

## How this skill talks to objection

Two equivalent transports — pick based on how the user's environment is set up:

### 1. CLI (`objection agent ...`) — one-shot, spawns its own session

```
objection -g <package/bundle-id> agent exec '<command>'
objection -g <package> agent state
objection -g <package> agent rpc <method> [--args '<json array>']
objection agent capabilities      # no device needed
```

`agent exec` runs a single objection command string and prints a **unified JSON result** to stdout. Each call attaches/spawns the target fresh (no cross-call session reuse in one-shot mode).

### 2. HTTP API — long-lived session, poll events

If the user has objection running as an API server (`objection -g <pkg> api`, or `objection start --enable-api`), prefer the HTTP API for multi-step flows — it keeps a single agent session and lets you poll async events (hook hits):

| Endpoint | Method | Purpose |
|---|---|---|
| `/command/exec` | POST | Run one or many objection commands; body `{"command":"..."}` or `{"commands":[...]}` |
| `/state` | GET | Connection / device / running-jobs snapshot |
| `/events/poll` | GET | Drain async events (hook invocations, canary hits, pasteboard changes). `?peek=1` to view without clearing |
| `/capabilities` | GET | Enumerate all commands (static, no device) |
| `/agent/rpc/<method>` | GET/POST | Call an agent RPC method directly; POST body is a JSON array of positional args |
| `/rpc/invoke/<method>` | GET/POST | Legacy raw RPC bridge (pre-existing) |

Default API host/port: `127.0.0.1:8888`.

### Unified JSON schema

Every `agent exec` call and `/command/exec` response is:

```json
{
  "status": "ok" | "error",
  "command": "<the command string>",
  "result": { ... },          // command-specific structured payload
  "jobs_created": [<int>, ...],
  "warnings": ["<str>", ...]
}
```

Parse `status` first. `warnings` carries non-fatal caveats — **read them**: they often say where to look next (e.g. "Job id not surfaced; use `agent state`").

## Critical Agent constraints

1. **Action commands don't return their Job id.** Commands that install hooks (`android hooking watch`, `android sslpinning disable`, `android root disable`, `ios keychain dump_raw`, monitors, etc.) return `{"action": "..."}` with a warning. The hook **is installed** — to see hits or the Job id, call `agent state` / `GET /state` and `GET /events/poll`.

2. **Async results come via events, not the command response.** A `watch` command's response just confirms the hook is armed. Actual invocations (args/return/backtrace) arrive as async messages — poll `GET /events/poll` after triggering the app.

3. **No interactive prompts in JSON mode.** Commands that would `click.confirm` (keystore clear, keychain clear, file delete, recursive download) **auto-proceed** in JSON mode — they do NOT block. Treat them as immediately executed. Commands that open an interactive shell (`sqlite connect`, JS `prompt` editors) are **unavailable** in JSON mode and return an error guiding you to the non-interactive alternative.

4. **`--json <filename>` vs global JSON mode.** Some commands (`memory list modules`, `ios keychain dump`, `android hooking search`) historically took `--json <file>` to write a file. Under `agent exec` / HTTP (global JSON mode) they instead return the data to stdout/response. If you need a file, pass `--json <filename>` explicitly and you'll get `{"dumped_to": "<file>"}`.

5. **Classes load lazily (Android).** `android hooking list classes` only shows classes *already loaded* — trigger the feature in the app first, or use `android hooking notify <pattern>` for lazy watching.

## Recommended flow

Most tasks follow this shape — adapt to the platform (Android vs iOS):

```
1. Discover what's available
   → agent capabilities                          (no device)
   → agent exec 'env'                            (platform + paths)
   → agent exec 'android hooking list classes'   (or 'ios hooking list classes')

2. Locate the target
   → agent exec 'android hooking search <class>!<method>'
   → agent exec 'android hooking list class_methods <class>'
   → agent exec 'android heap search instances <class>'

3. Act (install hook / dump / bypass)
   → agent exec 'android hooking watch <class>!<method> --dump-args --dump-return'
   → agent exec 'android sslpinning disable'
   → agent exec 'ios keychain dump'

4. Observe results
   → GET /events/poll        (hook hits, args, return values)
   → GET /state              (jobs installed)
   → (re-trigger the feature in the app, then poll again)
```

## Common capabilities (quick reference)

| Goal | Android | iOS |
|---|---|---|
| List classes | `android hooking list classes` | `ios hooking list classes` |
| List methods | `android hooking list class_methods <c>` | `ios hooking list class_methods <c>` |
| Watch a method | `android hooking watch <c>!<m> --dump-args --dump-return --dump-backtrace` | `ios hooking watch <pattern>` |
| Force return value | `android hooking set return_value <c>!<m> true` | `ios hooking set_method_return <selector> true` |
| Secrets | `android keystore list/detail`, `android clipboard monitor` | `ios keychain dump`, `ios cookies get`, `ios nsuserdefaults get`, `ios pasteboard monitor`, `ios nsurlcredentialstorage dump` |
| Bypass | `android sslpinning disable`, `android root disable/simulate` | `ios sslpinning disable`, `ios jailbreak disable/simulate` |
| Heap | `android heap search instances <c>`, `print methods/fields`, `execute method` | `ios heap search instances <c>`, `print ivars/methods`, `execute method` |
| Memory | `memory list modules`, `memory list exports <m>`, `memory search <pat>`, `memory dump from_base <addr> <size> <dest>` | same |
| Filesystem | `ls`, `cd`, `pwd`, `filesystem download/cat`, `rm` | same |
| Runtime | `android shell_exec <cmd>`, `android ui flag_secure <true/false>`, `android ui screenshot <png>`, `android intent launch_activity <c>`, `android deoptimize` | `ios ui alert <msg>`, `ios ui screenshot <png>`, `ios ui dump`, `ios ui bypass_touchid`, `ios binary info` |
| Generation | `android hooking generate simple <c>` (emit hook JS) | `ios hooking generate simple <c>` (emit hook JS) |

Full per-command argument and return schemas live in `reference/` (see `reference/runtime.md` for UI, on-device HTTP, intents, shell_exec, deoptimize, generation, binary info, command history, plugins).

## Troubleshooting

- **"Failed to talk to the Frida RPC" / "Frida server is not running"** → `frida-server` isn't running on the device, or the package id is wrong. Have the user start it (`adb shell su -c frida-server &` on Android) and confirm with `frida-ps -U`.
- **Empty class list** → classes aren't loaded yet; navigate the app to the feature first.
- **Hook installed but no events** → you haven't triggered the hooked method in the app yet; poll `/events/poll` after exercising the feature.
- **`sqlite connect` errors in JSON mode** → expected; pull the DB with `filesystem download <remote> <local.sqlite>` and inspect locally.
- **Command returns `result: null` with a "no structured output" warning** → that command hasn't been converted to structured output yet; fall back to `agent rpc <method>` to call the underlying RPC directly, or tell the user.

## What this skill cannot do

- Call methods that require complex arguments via the heap `execute` (only no-arg methods are supported by the agent).
- Reliably patch memory that gets re-mapped/relinked (in-memory `memory replace` can revert).
- Run on a target without Frida — there is no fallback.
