# 常量 <code>agent/src/lib/constants.ts</code>

`constants.ts` 定义 Agent 跨平台使用的枚举常量，目前主要是 `DeviceType`，用于运行时识别目标平台。

## 📋 模块概览
| 项目 | 值 |
| --- | --- |
| 文件路径 | `agent/src/lib/constants.ts` |
| 平台 | 通用 |
| 导出 RPC | 无 |
| 依赖 | 无 |

## 🎯 解决的问题
- 给 `generic/environment.ts` 的 `runtime()` 提供平台标识字符串。

## 🏗️ 导出的方法
| 符号 | 说明 |
| --- | --- |
| `DeviceType.IOS` | `"ios"` |
| `DeviceType.ANDROID` | `"android"` |
| `DeviceType.UNKNOWN` | `"unknown"` |

## ⚙️ 实现要点

```ts
// agent/src/lib/constants.ts:1-5
export enum DeviceType {
  IOS = "ios",
  ANDROID = "android",
  UNKNOWN = "unknown",
}
```

`generic/environment.ts:36-41` 的 `runtime()` 据此返回当前进程是 iOS 还是 Android：先看 `ObjC.available`，再看 `Java.available`，否则 `UNKNOWN`。该返回值被 `rpc/environment.ts` 的 `envRuntime` 暴露，Python 侧据此选择走哪套命令实现。

## 📐 调用关系

```mermaid
flowchart LR
    C[constants.ts DeviceType] --> E[environment.ts runtime]
    E --> R[rpc/environment.ts envRuntime]
    R --> Py[Python device.py]
```

## 🔍 源码索引
| 符号 | 位置 |
| --- | --- |
| `DeviceType` enum | [`agent/src/lib/constants.ts:1`](https://github.com/android-security-engineer/objection-skills/blob/master/agent/src/lib/constants.ts#L1) |

## 🔗 相关文档
- [Frida 与 Agent](/guide/frida-agent)
- [`environment.md`](/reference/agent/generic/environment) · [`environment.md`](/reference/agent/rpc/environment)
