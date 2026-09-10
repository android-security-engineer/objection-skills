# Secrets — keychain, keystore, cookies, defaults, pasteboard, credentials

## iOS Keychain (`ios keychain ...`)

### `ios keychain dump`
May require device passcode/TouchID on-device.
- args: optional `--smart` (smart-decode values), `--json <filename>` (writes file)
- result (stdout/HTTP): `{"entries":[{create_date,accessible_attribute,access_control,item_class,account,service,data},...],"count":<>,"smart_decoded":bool}`
- result (file): `{"dumped_to":<>,"count":<>}`

### `ios keychain dump_raw` *(action)*
Raw unparsed dump; entries emitted as **async messages** — poll `/events/poll`.
- args: `(none)`
- result: `{"action":"dumped_raw"}`

### `ios keychain clear` *(action, auto-proceeds in JSON mode)*
- args: `(none)` — **does not prompt** in JSON mode; clears immediately.
- result: `{"cleared":true}`

### `ios keychain remove` *(action)*
- args: `--account <a> --service <s>` (both required)
- result: `{"removed":true,"account":<>,"service":<>}`

### `ios keychain update` *(action)*
- args: `--account <a> --service <s> --newdata <d>` (all required)
- result: `{"updated":true,"account":<>,"service":<>}`

### `ios keychain add` *(action)*
- args: `--account <a> --service <s> --data <d>` (account/service required when --data given)
- result: `{"added":bool,"account":<>,"service":<>}`; status `error` if add failed.

## Android KeyStore (`android keystore ...`)

### `android keystore list`
- args: `(none)`
- result: `{"entries":[{alias,is_key,is_certificate},...],"count":<>}`

### `android keystore detail`
- args: `(none)`
- result: `{"details":[{keystoreAlias,keyAlgorithm,keySize,blockModes,encryptionPaddings,digests,keyValidityStart,origin,purposes,signaturePaddings,isInsideSecureHardware},...],"count":<>}`

### `android keystore clear` *(action, auto-proceeds in JSON mode)*
- args: `(none)` — no prompt in JSON mode.
- result: `{"cleared":true}`

### `android keystore watch` *(action)*
- args: `(none)`
- result: `{"watching":true}` — usage observed via `/events/poll`.

## Cookies / Defaults / Pasteboard / Credentials

### `ios cookies get`
- args: `(none)`
- result: `{"cookies":[{name,value,expiresDate,domain,path,isSecure,isHTTPOnly},...],"count":<>}`

### `ios nsuserdefaults get`
- args: `(none)`
- result: the raw defaults object (dict). Returned directly as `result`.

### `ios pasteboard monitor` *(action)*
- args: `(none)`
- result: `{"action":"monitoring_pasteboard"}` — new strings via `/events/poll`.

### `android clipboard monitor` *(action)*
- args: `(none)`
- result: `{"action":"monitoring_clipboard"}` — new strings via `/events/poll`.

### `ios nsurlcredentialstorage dump`
- args: `(none)`
- result: `{"credentials":[{protocol,host,port,authMethod,user,password},...],"count":<>}`
