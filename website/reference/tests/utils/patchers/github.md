# GitHub API 封装测试 <code>tests/utils/patchers/test_github.py</code>

验证 `objection.utils.patchers.github.Github` 的 `_call`（带缓存）、`get_latest_version`、`get_assets`：HTTP 请求、状态码检查、JSON 解析、响应缓存与 404 异常。

## 📋 模块概览

| 项目 | 值 |
| --- | --- |
| 文件路径 | `tests/utils/patchers/test_github.py` |
| 被测对象 | `objection.utils.patchers.github.Github` |
| 用例数 | 5 |
| 框架 | pytest + unittest + mock |

## 🎯 测试意图

- 确认 `_call` 对 200 响应缓存结果（`request_cache` 长度 1），第二次同路径请求命中缓存返回首次结果。
- 确认 `get_latest_version` 返回 `tag_name`。
- 确认 `get_assets` 在 404 时抛异常，200 时返回 `assets` 列表。

## 🧪 用例清单

| 用例 | 行号 | 验证点 |
| --- | --- | --- |
| test_makes_call_and_stores_result_in_cache | 32 | 200 响应缓存且 cache 长度 1 |
| test_makes_call_and_stores_result_in_cache_and_fetches_next_from_cache | 45 | 第二次命中缓存返回首次结果 |
| test_makes_call_and_gets_latest_version | 67 | 返回 tag_name |
| test_makes_call_and_fails_to_get_assets | 79 | 404 抛异常 |
| test_makes_call_and_gets_assets | 90 | 200 返回 assets 列表 |

## ⚙️ 测试手法

每个用例以 `@mock.patch('objection.utils.patchers.github.requests')` 替换 `requests`，构造 `mock.Mock()` 设 `status_code`/`.json.return_value`。`setUp` 预置 `self.mock_response`（含 `tag_name='10.6.9'` 与 assets）。缓存用例先调用一次 `_call('/test')` 再改 `mock_requests.get` 返回值，第二次调用断言仍返回首次结果（证明缓存命中）。

关键代码 `tests/utils/patchers/test_github.py:45`：

```python
@mock.patch('objection.utils.patchers.github.requests')
def test_makes_call_and_stores_result_in_cache_and_fetches_next_from_cache(self, mock_requests):
    ...
    self.github._call('/test')
    # entry is now stored in cache, update the next response object
    mock_response = mock.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'other'}
    mock_requests.get.return_value = mock_response
    result = self.github._call('/test')
    self.assertEqual(result, self.mock_response)
```

```mermaid
flowchart LR
    T[测试函数] --> M[mock requests.get]
    M --> C[_call / get_latest_version / get_assets]
    C --> A[断言返回值 / cache / 异常]
```

## 🔍 源码索引

| 用例 | 位置 |
| --- | --- |
| test_makes_call_and_stores_result_in_cache | tests/utils/patchers/test_github.py:32 |
| test_makes_call_and_stores_result_in_cache_and_fetches_next_from_cache | tests/utils/patchers/test_github.py:45 |
| test_makes_call_and_gets_latest_version | tests/utils/patchers/test_github.py:67 |
| test_makes_call_and_fails_to_get_assets | tests/utils/patchers/test_github.py:79 |
| test_makes_call_and_gets_assets | tests/utils/patchers/test_github.py:90 |

## 🔗 相关文档

- 对应被测模块文档：[/reference/utils/patchers/github](/reference/utils/patchers/github)
- 移动包补丁测试：[/reference/tests/commands/mobile-packages](/reference/tests/commands/mobile-packages)
