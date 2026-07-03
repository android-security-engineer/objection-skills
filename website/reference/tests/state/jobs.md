# 任务状态测试 <code>tests/state/test_jobs.py</code>

验证 `objection.state.jobs.job_manager_state` 与 `Job` 模型：初始空 jobs、`add_job` 添加、`remove_job` 按 UUID 移除并调用远端 `state_connection.get_api`。

## 📋 模块概览

| 项目 | 值 |
| --- | --- |
| 文件路径 | `tests/state/test_jobs.py` |
| 被测对象 | `objection.state.jobs.job_manager_state`/`Job` |
| 用例数 | 3 |
| 框架 | pytest + unittest + mock |

## 🎯 测试意图

- 确认 `job_manager_state.jobs` 初始为空。
- 确认 `add_job` 把 `Job` 实例加入 jobs 字典。
- 确认 `remove_job(uuid)` 移除本地条目并调用 `state_connection.get_api`。`tearDown` 清空 jobs。

## 🧪 用例清单

| 用例 | 行号 | 验证点 |
| --- | --- | --- |
| test_job_manager_starts_with_empty_jobs | 11 | 初始 jobs 长度为 0 |
| test_adds_jobs | 14 | add_job 后长度为 1 |
| test_removes_jobs | 22 | remove_job 后长度为 0 且调 get_api |

## ⚙️ 测试手法

构造真实 `Job('foo','hook',None,uuid)` 实例加入 `job_manager_state.jobs`。`remove_job` 用例以 `@mock.patch('objection.state.jobs.state_connection.get_api')` 注入连接，调用后断言 jobs 字典长度归零。`tearDown` 重置 `job_manager_state.jobs = {}`。

关键代码 `tests/state/test_jobs.py:22`：

```python
@mock.patch('objection.state.jobs.state_connection.get_api')
def test_removes_jobs(self, mock_api):
    job_manager_state.jobs = {}
    j1 = Job('foo', 'hook', None, 100002)
    j2 = Job('bar', 'hook', None, 100003)
    job_manager_state.add_job(j1)
    job_manager_state.add_job(j2)
    job_manager_state.remove_job(j1.uuid)
    job_manager_state.remove_job(j2.uuid)
    self.assertEqual(len(job_manager_state.jobs), 0)
```

```mermaid
flowchart LR
    T[测试函数] --> J[构造 Job 实例]
    J --> S[job_manager_state.add_job]
    S --> A[mock get_api]
    A --> R[remove_job uuid]
    R --> O[断言 jobs 长度]
```

## 🔍 源码索引

| 用例 | 位置 |
| --- | --- |
| test_job_manager_starts_with_empty_jobs | tests/state/test_jobs.py:11 |
| test_adds_jobs | tests/state/test_jobs.py:14 |
| test_removes_jobs | tests/state/test_jobs.py:22 |

## 🔗 相关文档

- 对应被测模块文档：[/reference/state/jobs](/reference/state/jobs)
- 任务命令测试：[/reference/tests/commands/jobs](/reference/tests/commands/jobs)
