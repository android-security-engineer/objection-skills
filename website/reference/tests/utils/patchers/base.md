# 补丁器基类测试 <code>tests/utils/patchers/test_base.py</code>

验证 `objection.utils.patchers.base` 的 `BasePlatformGadget`/`BasePlatformPatcher`：本地版本回退、初始化、requirements 检查、`_check_commands` 用 `shutil.which` 定位依赖命令与失败提示。

## 📋 模块概览

| 项目 | 值 |
| --- | --- |
| 文件路径 | `tests/utils/patchers/test_base.py` |
| 被测对象 | `objection.utils.patchers.base.BasePlatformGadget`/`BasePlatformPatcher` |
| 用例数 | 6 |
| 框架 | pytest + unittest + mock |

## 🎯 测试意图

- 确认 `get_local_version` 在无本地记录（`os.path.exists=False`）时返回 `'0'`。
- 确认 `BasePlatformPatcher` 初始化后 `have_all_commands=True`、`command_run_timeout=300`。
- 确认 `are_requirements_met` 依 `_check_commands` 返回布尔。
- 确认 `_check_commands` 用 `shutil.which` 找到命令时设 `location` 并返回 True，找不到时打印安装提示并返回 False。

## 🧪 用例清单

| 用例 | 行号 | 验证点 |
| --- | --- | --- |
| test_sets_version_to_zero_if_no_local_record_is_found | 14 | 无记录返回 '0' |
| test_inits_base_patcher | 26 | have_all_commands 与 timeout |
| test_are_requirements_met_returns_true_if_met | 33 | requirements 满足返回 True |
| test_are_requirements_met_returns_false_if_not_met | 39 | 不满足返回 False |
| test_check_commands_finds_commands_and_sets_location | 46 | which 找到时设 location |
| test_check_commands_fails_to_find_command_and_displays_error | 63 | which 失败时打印安装提示 |

## ⚙️ 测试手法

`BasePlatformGadget.setUp` 以 `@mock.patch('objection.utils.patchers.base.Github')` 构造实例。`get_local_version` 用例 mock `os.path.exists=False` 断言返回 `'0'`。`BasePlatformPatcher` 用例以 `@mock.patch` 替换 `_check_commands` 返回值构造实例，断言属性。`_check_commands` 真实用例 mock `BasePlatformPatcher.__init__` 绕过基类初始化，再 mock `shutil.which` 返回 `/bin/test` 或 None，用 `capture` 捕获失败提示。

关键代码 `tests/utils/patchers/test_base.py:46`：

```python
@mock.patch('objection.utils.patchers.base.BasePlatformPatcher.__init__', mock.Mock(return_value=None))
@mock.patch('objection.utils.patchers.base.shutil')
def test_check_commands_finds_commands_and_sets_location(self, mock_shutil):
    mock_shutil.which.return_value = '/bin/test'
    base_patcher = BasePlatformPatcher()
    base_patcher.required_commands = {'aapt': {'installation': 'apt install aapt (Kali Linux)'}}
    check_result = base_patcher._check_commands()
    self.assertTrue(check_result)
    self.assertEqual(base_patcher.required_commands['aapt']['location'], '/bin/test')
```

```mermaid
flowchart LR
    T[测试函数] --> M[mock Github/os/shutil/__init__]
    M --> B[BasePlatformGadget/Patcher]
    B --> C[get_local_version / are_requirements_met / _check_commands]
    C --> A[断言 布尔/属性/location/stdout]
```

## 🔍 源码索引

| 用例 | 位置 |
| --- | --- |
| test_sets_version_to_zero_if_no_local_record_is_found | tests/utils/patchers/test_base.py:14 |
| test_inits_base_patcher | tests/utils/patchers/test_base.py:26 |
| test_are_requirements_met_returns_true_if_met | tests/utils/patchers/test_base.py:33 |
| test_are_requirements_met_returns_false_if_not_met | tests/utils/patchers/test_base.py:39 |
| test_check_commands_finds_commands_and_sets_location | tests/utils/patchers/test_base.py:46 |
| test_check_commands_fails_to_find_command_and_displays_error | tests/utils/patchers/test_base.py:63 |

## 🔗 相关文档

- 对应被测模块文档：[/reference/utils/patchers/base](/reference/utils/patchers/base)
- Android/iOS 子类测试：[/reference/tests/utils/patchers/android](/reference/tests/utils/patchers/android)、[/reference/tests/utils/patchers/ios](/reference/tests/utils/patchers/ios)
