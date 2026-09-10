# Filesystem — ls, cd, pwd, download, upload, cat, rm

Remote filesystem navigation on the device, plus file transfer. Paths are resolved against the app's working directory (use `pwd`); platform separator differs (`/` on iOS, `/` on Android).

### `pwd`
- args: `(none)`
- result: `{"cwd": "<path>"}`

### `cd <path>`
Updates the in-memory cwd. Validates the path exists on-device.
- args: `<absolute path>` or `<relative>` or `..`
- result: `{"cwd": <new>, "changed": bool}` or `{"cwd":<>,"changed":false,"at_root":true}` (already at root)
- error: `{"error":"invalid path","path":<>}`

### `ls [path]`
- args: optional `<path>` (defaults to cwd)
- result: `{"path":<>,"readable":bool,"writable":bool,"files":{<name>:{attributes,readable,writable},...}}`
- The `files` map's `attributes` differ by platform (iOS: `NSFileType`,`NSFilePosixPermissions`,...; Android: `isDirectory`,`lastModified`,`size`,...).

### `filesystem download <remote> [local]` *(action)*
- args: `<remote location>` + optional `<local destination>` + `--folder` (recursive)
- result: `{"action":"downloaded","source":<>,"destination":<>,"folder":bool}`
- **auto-proceeds** recursive-folder confirm in JSON mode.

### `filesystem upload <local> [remote]` *(action)*
- args: `<local source>` + optional `<remote destination>`
- result: `{"action":"uploaded","source":<>,"destination":<>}`

### `filesystem cat <remote>` *(action)*
Download a file and return its contents as text.
- args: `<remote location>`
- result: `{"path":<>,"content":"<utf-8 string>"}` (uses errors='ignore' for binary)

### `rm <remote>` *(action, auto-proceeds in JSON mode)*
- args: `<target remote file>` — **no confirm prompt** in JSON mode; deletes immediately.
- result: `{"action":"deleted","target":<>,"deleted":bool}`

### `sqlite connect <remote>` — **unavailable in JSON mode**
The interactive sqlite shell can't run under an Agent. Returns:
- error: `{"error":"interactive sqlite shell unavailable in JSON mode"}` + human_text guiding to `filesystem download`.

Pull the DB locally instead: `filesystem download <remote> <local.sqlite>`, then inspect with standard sqlite tooling.
