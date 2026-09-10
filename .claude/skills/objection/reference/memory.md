# Memory — modules, exports, search, replace, write, dump

All process-memory operations on the injected target. Addresses are hex strings (`0x...`); sizes are integers (bytes).

## Listing

### `memory list modules`
- args: optional `--json <filename>` (writes file)
- result (stdout/HTTP): `{"modules":[{name,base,size,path},...],"count":<>}`
- result (file): `{"dumped_to":<>,"count":<>}`

### `memory list exports <module>`
- args: `<module name>` + optional `--json <filename>`
- result (stdout/HTTP): `{"module":<>,"exports":[{type,name,address},...],"count":<>}`
- result (file): `{"dumped_to":<>,"module":<>,"count":<>}`

## Search / patch

### `memory search "<pattern>"`
Search accessible memory. Pattern is space-separated hex bytes; `??` = wildcard.
- args: `"<hex pattern>"` + `--string` (interpret arg as ASCII→hex) + `--offsets-only` (return only addresses)
- result: `{"pattern":<>,"matches":[<addr>,...],"count":<>}`

### `memory replace "<pattern>" "<replace>"`
Find and overwrite bytes in-place.
- args: `"<search hex>" "<replace hex>"` + `--string-pattern` / `--string-replace` (ASCII)
- result: `{"pattern":<>,"replaced_at":[<addr>,...],"count":<>}`
- warnings: in-memory replacement can be unstable; re-mapping may revert.

### `memory write "<address>" "<bytes>"` *(action, dangerous)*
- args: `"<hex addr>" "<hex bytes>"` + `--string`
- result: `{"action":"wrote","address":<>,"bytes":<int>}`

## Dump

### `memory dump all <destination>` *(action, slow)*
Dump all `rw-` memory regions to a local file. Appends if file exists.
- args: `<local destination path>` — **auto-proceeds** if file exists in JSON mode (appends).
- result: `{"dumped_to":<>,"ranges_total":<>,"ranges_dumped":<>,"total_size":<>}`

### `memory dump from_base <addr> <size> <destination>` *(action)*
- args: `<hex base address> <size bytes> <local destination>`
- result: `{"dumped_to":<>,"base":<>,"size":<>,"bytes_written":<>}`
