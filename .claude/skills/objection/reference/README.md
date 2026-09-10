# Reference — command argument & return schemas

This directory documents the **structured inputs and outputs** of objection's Agent-facing commands. Each command run via `agent exec` or `POST /command/exec` returns the [unified JSON schema](../SKILL.md#unified-json-schema); here we document the shape of `result` for each.

Only the `result` field is shown below — wrap it in the full envelope:

```json
{"status":"ok","command":"<cmd>","result":<below>,"jobs_created":[],"warnings":[]}
```

Files:
- [hooking.md](hooking.md) — class/method enumeration, watching, return-value forcing, search (Android + iOS)
- [secrets.md](secrets.md) — keychain, keystore, cookies, nsuserdefaults, pasteboard, credential storage
- [bypass.md](bypass.md) — SSL pinning, root/jailbreak detection
- [heap.md](heap.md) — live instance search, method/field inspection, method execution, JS evaluation
- [memory.md](memory.md) — module/export listing, search, replace, write, dump
- [filesystem.md](filesystem.md) — ls/cd/pwd, download/upload/cat/rm
- [jobs-state.md](jobs-state.md) — jobs list/kill, session state, event polling
- [environment.md](environment.md) — env, frida info, ping, import
- [runtime.md](runtime.md) — UI (alert/screenshot/dump/touchid/flag_secure), on-device HTTP, Android intents & shell_exec, deoptimize, hook script generation, iOS binary info, command history, plugin loading
