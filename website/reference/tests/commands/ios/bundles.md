# iOS Bundles 测试 <code>tests/commands/ios/test_bundles.py</code>

这个测试文件验证 objection 的 iOS bundle/framework 枚举命令，覆盖多个辅助函数（是否包含 Apple bundle、是否打印全路径、是否为 Apple bundle 标识）以及 `show_frameworks`/`show_bundles` 在不同 flag 组合下的表格输出。

## 📋 模块概览
| 项目 | 值 |
| --- | --- |
| 文件路径 | `tests/commands/ios/test_bundles.py` |
| 被测对象 | `objection.commands.ios.bundles` |
| 用例数 | 11 |
| 框架 | unittest（mock.patch + capture） |

## 🎯 测试意图
- 验证 `--include-apple-frameworks` 与 `--full-path` flag 解析。
- 验证 `_is_apple_bundle` 对 None、`com.apple.*` 前缀、非 Apple 字符串的判定。
- 验证 `show_frameworks` 默认排除 Apple bundle、传 flag 后包含，且 `--full-path` 显示完整路径。
- 验证 `show_bundles` 的表格输出与 `--full-path` 行为。

## 🧪 用例清单
| 用例 | 行号 | 验证点 |
| --- | --- | --- |
| `test_should_include_apple_bundles_helper_is_true` | `tests/commands/ios/test_bundles.py:38` | flag 存在返回 True |
| `test_should_include_apple_bundles_helper_is_false` | `tests/commands/ios/test_bundles.py:42` | 无 flag 返回 False |
| `test_should_print_full_path_helper_is_true` | `tests/commands/ios/test_bundles.py:46` | `--full-path` 返回 True |
| `test_should_print_full_path_helper_is_false` | `tests/commands/ios/test_bundles.py:50` | 无 flag 返回 False |
| `test_is_apple_bunlde_returns_false_on_none` | `tests/commands/ios/test_bundles.py:54` | None 返回 False |
| `test_is_apple_bunlde_returns_true_for_apple_bundle` | `tests/commands/ios/test_bundles.py:57` | `com.apple.*` 返回 True |
| `test_is_apple_bunlde_returns_false_for_string_not_starting_with_com_apple` | `tests/commands/ios/test_bundles.py:60` | 非 `com.apple` 开头返回 False |
| `test_is_apple_bunlde_returns_false_for_non_apple_bundle` | `tests/commands/ios/test_bundles.py:63` | 第三方 bundle 返回 False |
| `test_show_frameworks_prints_without_apple_bundles` | `tests/commands/ios/test_bundles.py:67` | 默认排除 Apple bundle |
| `test_show_frameworks_prints_with_apple_bundles` | `tests/commands/ios/test_bundles.py:82` | 传 flag 包含 Apple bundle |
| `test_show_frameworks_prints_with_apple_bundles_and_full_paths` | `tests/commands/ios/test_bundles.py:95` | flag + full-path 显示完整路径 |
| `test_show_bundles_prints_bundles` | `tests/commands/ios/test_bundles.py:108` | bundle 表格输出 |
| `test_show_bundles_prints_bundles_full_path` | `tests/commands/ios/test_bundles.py:120` | bundle 全路径输出 |

## ⚙️ 测试手法
`setUp`（`tests/commands/ios/test_bundles.py:10`）预置 4 条 bundle 数据（含 Apple、第三方、超长路径）。辅助函数用例直接断言布尔。枚举用例 `@mock.patch(...get_api)` 预设 `ios_bundles_get_frameworks`/`ios_bundles_get_bundles` 返回值，用 `capture` 捕获表格后断言关键字段 token 存在（注释 `:73` 说明不锁定 tabulate 列宽），并用 `assertNotIn` 验证默认排除 Apple bundle。

```mermaid
flowchart LR
    S[setUp 预置数据] --> T[测试函数]
    T -->|辅助| H[断言布尔]
    T -->|枚举| M[mock get_api]
    M --> L[ios_bundles_get_*]
    L --> C[capture 表格]
    C --> A[断言 token 存在/不存在]
```

## 🔍 源码索引
| 用例 | 位置 |
| --- | --- |
| `test_should_include_apple_bundles_helper_is_true` | `tests/commands/ios/test_bundles.py:38` |
| `test_should_include_apple_bundles_helper_is_false` | `tests/commands/ios/test_bundles.py:42` |
| `test_should_print_full_path_helper_is_true` | `tests/commands/ios/test_bundles.py:46` |
| `test_should_print_full_path_helper_is_false` | `tests/commands/ios/test_bundles.py:50` |
| `test_is_apple_bunlde_returns_false_on_none` | `tests/commands/ios/test_bundles.py:54` |
| `test_is_apple_bunlde_returns_true_for_apple_bundle` | `tests/commands/ios/test_bundles.py:57` |
| `test_is_apple_bunlde_returns_false_for_string_not_starting_with_com_apple` | `tests/commands/ios/test_bundles.py:60` |
| `test_is_apple_bunlde_returns_false_for_non_apple_bundle` | `tests/commands/ios/test_bundles.py:63` |
| `test_show_frameworks_prints_without_apple_bundles` | `tests/commands/ios/test_bundles.py:67` |
| `test_show_frameworks_prints_with_apple_bundles` | `tests/commands/ios/test_bundles.py:82` |
| `test_show_frameworks_prints_with_apple_bundles_and_full_paths` | `tests/commands/ios/test_bundles.py:95` |
| `test_show_bundles_prints_bundles` | `tests/commands/ios/test_bundles.py:108` |
| `test_show_bundles_prints_bundles_full_path` | `tests/commands/ios/test_bundles.py:120` |

## 🔗 相关文档
- 对应被测模块文档：`/reference/commands/ios/bundles`（如存在）
