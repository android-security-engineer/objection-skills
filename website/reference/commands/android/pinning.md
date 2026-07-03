# Android SSL Pinning 绕过 <code>commands/android/pinning.py</code>

该模块启动一个作业，hook 常见 SSL Pinning 实现类（OkHttp、TrustManager、Conscrypt 等），替换校验逻辑以绕过证书锁定。它属于 `android sslpinning` 命令组，CLI 前缀为 `android sslpinning disable`，是流量抓包的前置步骤。

## 模块概览

| 项目 | 值 |
| --- | --- |
| 文件路径 | `objection/commands/android/pinning.py` |
| Agent 实现 | `agent/src/android/pinning.ts` |
| 命令组 | `android sslpinning` |
| 依赖 | `objection.state.connection`、`objection.utils.output` |

## 解决的问题

- App 用证书锁定阻止中间人抓包，需一键绕过常见实现。
- `--quiet` 抑制 agent 侧的逐条 hook 日志，减少噪声。
- 以异步作业常驻，hook 完即生效，无需重启 App。

## 📋 命令清单

| 命令 | 函数 | 说明 |
| --- | --- | --- |
| `android sslpinning disable [--quiet]` | `android_disable()` | hook 常见类绕过 SSL pinning |

辅助函数：`_should_be_quiet()`（行 5）。

## ⚙️ 实现原理

Python 层仅解析 `--quiet` 标志并透传给 `api.android_ssl_pinning_disable(quiet)`。agent 侧批量替换 `X509TrustManager.checkServerTrusted`、`OkHttp3`/`Conscrypt` 等校验方法。

### `android_disable()` — 绕过 SSL pinning

源码：[`objection/commands/android/pinning.py:17`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/android/pinning.py#L17)

无位置参数。调 `api.android_ssl_pinning_disable(_should_be_quiet(args))`。JSON 模式返回 `result={'action': 'ssl_pinning_disabled', 'quiet': ...}`，`warnings` 提示作业 id 需经 `agent state` 查。

```python
# objection/commands/android/pinning.py:26-27
api = state_connection.get_api()
api.android_ssl_pinning_disable(_should_be_quiet(args))
```

```python
# objection/commands/android/pinning.py:29-36
if should_output_json(args):
    return output_result(
        CommandResult(
            result={'action': 'ssl_pinning_disabled', 'quiet': _should_be_quiet(args)},
            warnings=['Job id not surfaced; use `agent state` to list running jobs.'],
        ),
        command='android sslpinning disable',
    )
```

```mermaid
flowchart LR
    A["CLI: sslpinning disable [--quiet]"] --> B["_should_be_quiet 解析"]
    B --> C["get_api"]
    C --> D["api.android_ssl_pinning_disable RPC"]
    D --> E["agent hook TrustManager/OkHttp/Conscrypt"]
    E --> F["校验逻辑被替换 / JSON CommandResult"]
```

## JSON 模式行为

`--quiet` 既影响 agent 侧日志，也被回填到 `CommandResult.result.quiet` 供 agent 查阅。因是异步作业，`warnings` 提示作业 id 不在同步返回里，需 `agent state` 查询。非 JSON 模式返回 `None`，agent 侧成功后无额外输出。

## 🔍 源码索引

| 符号 | 位置 |
| --- | --- |
| `_should_be_quiet` | [`objection/commands/android/pinning.py:5`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/android/pinning.py#L5) |
| `android_disable` | [`objection/commands/android/pinning.py:17`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/android/pinning.py#L17) |

## 相关文档

- [RPC 通信机制](/guide/rpc)
- [REPL 与命令](/guide/repl)
