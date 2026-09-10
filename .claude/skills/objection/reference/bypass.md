# Bypass — SSL pinning, root/jailbreak detection

All commands here are **action** commands: they install a Frida hook Job and return immediately. The bypass is active until the Job is killed (`jobs kill <id>`) or the session ends. Job id is **not** returned — query `agent state` / `GET /state`.

## Android

### `android sslpinning disable`
Hook common pinning classes to bypass certificate pinning.
- args: optional `--quiet` (suppress per-attempt logging)
- result: `{"action":"ssl_pinning_disabled","quiet":bool}`

### `android root disable`
Bypass root detection checks.
- args: `(none)`
- result: `{"action":"root_detection_disabled"}`

### `android root simulate`
Make the app believe it IS rooted (test the rooted path).
- args: `(none)`
- result: `{"action":"root_detection_simulated"}`

## iOS

### `ios sslpinning disable`
- args: optional `--quiet`
- result: `{"action":"ssl_pinning_disabled","quiet":bool}`

### `ios jailbreak disable`
- args: `(none)`
- result: `{"action":"jailbreak_detection_disabled"}`

### `ios jailbreak simulate`
- args: `(none)`
- result: `{"action":"jailbreak_simulated"}`

> After installing a bypass, re-trigger the app's network call / detection check and observe behavior. Pinning/root bypasses don't emit events — their effect is that the previously-failing operation now succeeds.
