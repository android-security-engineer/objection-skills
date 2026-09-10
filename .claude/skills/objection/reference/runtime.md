# Runtime commands — UI, intents, shell, generation

These commands perform runtime actions on the connected device. All return the [unified JSON schema](README.md); only `result` is shown.

## UI

### `ios ui alert` / `android ui alert` — `alert <message>`
```json
{"action":"alert","message":"objection!","platform":"<ios|android>"}
```
On iOS, displays a popup; on Android, currently a no-op (platform recorded in result).

### `ios ui screenshot <local png>` — `ios_screenshot`
```json
{"saved_to":"out.png","bytes":12345}
```
Writes the PNG locally. Error on missing destination: `{"status":"error","result":{"error":"missing local png destination"}}`.

### `android ui screenshot <local png>` — `android_screenshot`
```json
{"saved_to":"out.png","bytes":12345}
```

### `ios ui dump` — `dump_ios_ui`
```json
{"ui":"<serialized iOS UI hierarchy>"}
```

### `ios ui bypass_touchid` — `bypass_touchid`
```json
{"action":"bypass_touchid"}
```
Action command — Job id not surfaced; check `agent state`. `warnings` present.

### `android ui flag_secure <true|false>` — `android_flag_secure`
```json
{"action":"set_flag_secure","value":"true"}
```
Error on bad input: `{"status":"error","result":{"error":"flag must be true or false"}}`.

## On-device HTTP server

### `http start [port]` — `start`
```json
{"action":"http_start","port":9000,"root":"/"}
```
Starts an on-device HTTP server exposing the filesystem (rooted at the current cwd).

### `http stop` — `stop`
```json
{"action":"http_stop"}
```

### `http status` — `status`
```json
{"action":"http_status"}
```

## Android intents

### `android intent analyze_implicit_intents [--dump-backtrace]` — `analyze_implicit_intents`
```json
{"action":"analyze_implicit_intents","dump_backtrace":false}
```
Action command — async intent broadcasts arrive as events; poll `agent state` / HTTP `/events`.

### `android intent launch_activity <class>` — `launch_activity`
```json
{"action":"launch_activity","activity":"com.example.MainActivity"}
```

### `android intent launch_service <class>` — `launch_service`
```json
{"action":"launch_service","service":"com.example.Service"}
```

## Android shell & VM

### `android shell_exec <command...>` — `execute`
```json
{"command":"id","stdout":"uid=0(root)...","stderr":""}
```
Runs an arbitrary shell command on the device. High value for Agent-driven exploration.

### `android deoptimize` — `deoptimise`
```json
{"action":"deoptimize"}
```
Forces the VM interpreter; useful when hooks are bypassed by JIT optimizations.

## Hook script generation

### `android hooking generate class` — `clazz`
```json
{"source":"<Java Hook Manager JS source>","asset":"javahookmanager.js"}
```

### `android hooking generate simple <class>` — `simple` (Android)
```json
{"class":"com.example.Cls","methods":["foo","bar"],"hooks":["<JS hook source>", ...]}
```

### `ios hooking generate class` — `clazz` (iOS)
```json
{"source":"<ObjC Hook Manager JS source>","asset":"objchookmanager.js"}
```

### `ios hooking generate simple <class>` — `simple` (iOS)
```json
{"class":"Foo","methods":["methodA:","methodB"],"hooks":["<JS hook source>", ...]}
```

Error on missing class / empty methods: `{"status":"error","result":{"error":"missing class name"}}` or `{"error":"no class / methods found"}`.

## iOS binary info

### `ios binary info` — `info`
```json
{"binaries":{"App":{"type":"Mach-O","encrypted":false,"pie":true,"arc":true,"canary":true,"stackExec":false,"rootSafe":false}},"count":1}
```

## Command history

### `commands history` — `history`
```json
{"commands":["env","android hooking list classes"],"count":2}
```

### `commands save <local destination>` — `save`
```json
{"saved_to":"history.txt","count":2}
```

### `commands clear` — `clear`
```json
{"cleared":true}
```

## Plugin loading

### `plugin load <path> [namespace]` — `load_plugin`
```json
{"loaded":true,"namespace":"myplugin","path":"/abs/path/__init__.py"}
```
Error paths: missing path, file not found, invalid plugin type, or load exception (`result.error` + `result.traceback`).
