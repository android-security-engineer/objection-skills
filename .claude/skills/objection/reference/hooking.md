# Hooking — class/method enumeration, watching, return forcing, search

## Android

### `android hooking list classes`
Enumerate **currently loaded** Java classes. Lazy — only classes used so far appear.
- args: `(none)`
- result: `{"classes": ["com.example.Foo", ...], "count": <int>}`

### `android hooking list class_loaders`
- args: `(none)`
- result: `{"class_loaders": [...], "count": <int>}`

### `android hooking list class_methods <class>`
- args: `<class name>`
- result: `{"class": "<class>", "methods": ["method1", ...], "count": <int>}`

### `android hooking list activities` / `receivers` / `services`
- args: `(none)`
- result: `{"activities"|"broadcast_receivers"|"services": [...], "count": <int>}`

### `android hooking get current_activity`
- args: `(none)`
- result: `{"activity": "<name>", "fragment": "<name>"}` (raw agent dict)

### `android hooking watch <pattern>` *(action)*
Install a hook. **Async hits via `/events/poll`**. Job id not returned — see `jobs list`.
- args: `<class>!<method>` or `<class>` (all methods) + flags `--dump-args --dump-backtrace --dump-return`
- result: `{"action":"watching","pattern":<>,"dump_args":bool,"dump_backtrace":bool,"dump_return":bool}`
- warnings: job id not surfaced; invocations arrive as async messages.

### `android hooking set return_value <class>!<method> <true|false>` *(action)*
- args: `"<class>!<method>" ["<overload>"] true|false`
- result: `{"action":"set_return_value","method":<>,"overload":<>,"value":bool}`

### `android hooking search <class>!<method>`
Enumerate classes/methods matching a pattern.
- args: `<pattern>` + optional `--json <filename>` (writes file → `{"dumped_to":<>,"count":<>}`) or `--only-classes`
- result (stdout/HTTP): `{"runtime":"java","results":[{loader,classes:[{name,methods,overloads}]}],"count":<>}`

### `android hooking notify <pattern>` *(action)*
Lazy-watch: arm a hook that activates when a class loads later.
- args: `<pattern>` + `--watch --dump-args --dump-backtrace --dump-return`
- result: `{"action":"watching_lazy","pattern":<>,"watch":bool,"dump_args":bool,...}`

## iOS

### `ios hooking list classes`
- args: optional `--ignore-native` (drop `NS*`,`UI*`,`CF*`, etc.)
- result: `{"classes":[...],"count":<>,"ignored_native":bool}`

### `ios hooking list class_methods <class>`
- args: `<class>` + optional `--include-parents`
- result: `{"class":<>,"methods":[...],"count":<>,"include_parents":bool}`

### `ios hooking watch <pattern>` *(action)*
- args: `<pattern>` + `--dump-args --dump-backtrace --dump-return --include-parents`
- result: `{"action":"watching","pattern":<>,"dump_args":bool,"dump_backtrace":bool,"dump_return":bool,"include_parents":bool}`

### `ios hooking set_method_return <selector> <true|false>` *(action)*
- args: `"<selector>"` e.g. `"-[ClassName methodName:]"` + `true|false`
- result: `{"action":"set_return_value","selector":<>,"value":bool}`

### `ios hooking search <pattern>`
- args: `<pattern>` + optional `--json <filename>` / `--only-classes`
- result (stdout/HTTP): `{"runtime":"objc","classes":{<class>:[<fullname>,...]},"class_count":<>}`
