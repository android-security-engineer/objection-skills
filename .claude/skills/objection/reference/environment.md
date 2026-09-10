# Environment — env, frida info, ping, import

Quick status / introspection commands. Good first calls when orienting.

### `env`
Platform + paths of interest (Documents, Library, bundle).
- args: `(none)`
- result: `{"platform":"ios"|"android","paths":{<name>:<path>,...}}`

### `frida` (alias for frida_environment)
Frida runtime info.
- args: `(none)`
- result: `{"version":<>,"arch":<>,"platform":<>,"debugger":<>,"runtime":<>,"heap":<int>}`

### `ping`
Check the agent is responsive.
- args: `(none)`
- result: `{"ok":bool}` — status `error`/exit 1 if not responding.

### `import <path>` *(action)*
Load and run a Frida script in the background (persists for the session).
- args: `<local path to frida-script>` (`~` expanded)
- result: `{"action":"imported","source":<>}` — script output via async messages.

### `evaluate <file>` *(action, JSON mode requires a file path)*
Evaluate a JS file in the agent's context.
- args: `<local path to js file>` — interactive editor unavailable in JSON mode; a file path is mandatory.
- result: `{"action":"evaluated","source":<>}` — output via async messages.
- error: `{"error":"JSON mode requires a file path argument (interactive prompt unavailable)"}` if no path given.
