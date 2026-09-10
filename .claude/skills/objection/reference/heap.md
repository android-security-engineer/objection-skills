# Heap — live instance search, inspection, method execution, JS eval

The heap commands let you find **live in-memory instances** of a class and operate on them — call methods, read fields, run arbitrary JS against a handle. This is the most powerful runtime introspection path.

## Android (`android heap ...`)

### `android heap search instances <class>`
Find live instances of a Java class.
- args: `<fully qualified class>` e.g. `com.example.Session`
- result: `{"class":<>,"instances":[{hashcode,classname,tostring},...],"count":<>}`
- Use the returned `hashcode` as the handle in the commands below.

### `android heap print methods <hashcode>`
- args: `<hashcode>` + optional `--without-arguments` (filter to no-arg methods)
- result: `{"handle":<>,"methods":[...],"class":<>,"count":<>}`

### `android heap print fields <hashcode>`
- args: `<hashcode>`
- result: `{"handle":<>,"fields":[{name,value},...],"count":<>}`

### `android heap execute method <hashcode> <method>` *(action, may return value)*
Call a no-arg method on a live instance.
- args: `<hashcode> <method>` + optional `--return-string`
- result: `{"handle":<>,"method":<>,"result":<agent return>,"as_string":bool}`

### `android heap execute js <hashcode>` *(action)*
Evaluate JS against a handle. **JSON mode requires `--inline <js>`** (interactive editor unavailable).
- args: `<hashcode> --inline <javascript source>` — the instance is available as `clazz` in the script.
- result: `{"action":"evaluated_js","handle":<>}` — script output via async messages.

## iOS (`ios heap ...`)

### `ios heap search instances <class>`
- args: `<class>`
- result: `{"class":<>,"instances":[{handle,kind,className,superClass,ivars,methods},...],"count":<>}`
- Use `handle` (a pointer) below.

### `ios heap print ivars <pointer>`
- args: `<pointer>` + optional `--to-utf8`
- result: `{"pointer":<>,"class":<>,"ivars":{<name>:<value>},"to_utf8":bool}`

### `ios heap print methods <pointer>`
- args: `<pointer>` + optional `--without-arguments`
- result: `{"pointer":<>,"class":<>,"methods":[...],"count":<>}`

### `ios heap execute method <pointer> <method>` *(action, may return value)*
Only no-arg methods supported (selector with no `:`).
- args: `<pointer> <method>` + optional `--return-string`
- result: `{"pointer":<>,"method":<>,"result":<agent return>,"as_string":bool}`
- error if method name contains `:` (`{"error":"only methods that do not require arguments are supported"}`)

### `ios heap execute js <pointer>` *(action)*
**JSON mode requires `--inline <js>`**. The pointer is available as `ptr`.
- args: `<pointer> --inline <javascript source>`
- result: `{"action":"evaluated_js","pointer":<>}`
