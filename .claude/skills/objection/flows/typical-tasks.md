# Typical task flows

Sequenced patterns an Agent can follow. Each step shows the CLI form (`objection -g <pkg> agent exec '...'`); for HTTP, `POST /command/exec` with `{"command":"..."}` and poll `GET /events/poll` instead of `agent state`.

## Flow 1 — "Dump the iOS keychain"

```
1. agent exec 'env'                              # confirm iOS + paths
2. agent exec 'ios keychain dump --smart'        # → result.entries[]
3. (if empty) the app hasn't stored creds yet; trigger a login, re-dump
4. (optional) agent exec 'ios keychain dump_raw' # raw entries via /events/poll
```

## Flow 2 — "Bypass SSL pinning and capture a request"

```
1. agent exec 'android sslpinning disable'       # bypass active
2. agent exec 'android hooking watch okhttp3.Request!<init> --dump-args'
   # or watch the app's own HTTP client method
3. (re-trigger the network call in the app)
4. GET /events/poll                              # → captured args
5. agent state                                   # → jobs installed
```

## Flow 3 — "Find and call a method on a live instance"

```
1. agent exec 'android hooking list classes' | grep -i session
2. agent exec 'android heap search instances com.example.Session'
   # → instances[].hashcode
3. agent exec 'android heap print methods <hashcode>'
4. agent exec 'android heap execute method <hashcode> getToken'
   # → result.result = the token
```

## Flow 4 — "Watch a method's args + backtrace"

```
1. agent exec 'android hooking list class_methods com.example.LoginManager'
2. agent exec 'android hooking watch com.example.LoginManager!doLogin --dump-args --dump-backtrace --dump-return'
3. (trigger login in app)
4. GET /events/poll                              # → args, backtrace, return value
```

## Flow 5 — "Extract an Android SQLite DB and inspect locally"

```
1. agent exec 'env'                              # get cwd / paths
2. agent exec 'ls'                               # locate the .db
3. agent exec 'filesystem download /data/.../databases/app.db ./app.db'
   # sqlite connect is unavailable in JSON mode
4. (locally) sqlite3 ./app.db ".tables"          # inspect outside objection
```

## Flow 6 — "Bypass root detection"

```
1. agent exec 'android root disable'
2. (re-run the feature that checked for root — it should now pass)
3. agent state                                   # confirm job running
```

## Flow 7 — "Enumerate iOS storage"

```
1. agent exec 'ios keychain dump --smart'
2. agent exec 'ios nsuserdefaults get'
3. agent exec 'ios cookies get'
4. agent exec 'ios nsurlcredentialstorage dump'
5. agent exec 'ios pasteboard monitor'           # then /events/poll while using the app
```
