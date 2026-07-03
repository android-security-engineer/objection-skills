# Android SSL Pinning 测试 <code>tests/commands/android/test_pinning.py</code>

这个测试文件验证 objection 的 Android SSL pinning 绕过命令 `android_disable`，确认它通过 RPC 调用设备端 `android_ssl_pinning_disable`。

## 📋 模块概览
| 项目 | 值 |
| --- | --- |
| 文件路径 | `tests/commands/android/test_pinning.py` |
| 被测对象 | `objection.commands.android.pinning.android_disable` |
| 用例数 | 1 |
| 框架 | unittest（mock.patch） |

## 🎯 测试意图
- 验证 `android_disable([])` 触发 `android_ssl_pinning_disable` RPC 调用。

## 🧪 用例清单
| 用例 | 行号 | 验证点 |
| --- | --- | --- |
| `test_pinning_disable` | `tests/commands/android/test_pinning.py:9` | 触发 SSL pinning 禁用 RPC |

## ⚙️ 测试手法
`@mock.patch(...get_api)` 注入 mock（`tests/commands/android/test_pinning.py:8`），调用 `android_disable([])` 后断言 `mock_api.return_value.android_ssl_pinning_disable.called`。无参数、无输出校验，是纯 RPC 透传用例。

```mermaid
flowchart LR
    T[test_pinning_disable] --> M[mock get_api]
    M --> D[android_disable]
    D --> R[android_ssl_pinning_disable]
    R --> A[断言 called]
```

## 🔍 源码索引
| 用例 | 位置 |
| --- | --- |
| `test_pinning_disable` | `tests/commands/android/test_pinning.py:9` |

## 🔗 相关文档
- 对应被测模块文档：`/reference/commands/android/pinning`（如存在）
