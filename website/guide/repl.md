# REPL 与命令

REPL 是用户与 objection 交互的主界面。这一页讲 REPL 如何把一行输入分派到具体实现，以及命令的命名约定。

## REPL 的角色

```mermaid
flowchart LR
    U[用户输入一行命令] --> R[REPL]
    R -->|解析命令名| MAP[命令注册表]
    MAP -->|找到实现函数| IMPL[commands/*.py]
    IMPL -->|调用 agent RPC| AGENT[Agent]
    AGENT -->|结果/消息| R
    R --> U[格式化输出]
```

REPL（`objection/console/repl.py`）核心做三件事：

1. **读取**用户输入的一行命令；
2. **分派**到对应的 Python 实现函数；
3. **输出**结果与 agent 回传的消息。

## 命令的组织

命令按平台/主题分目录：

```text
objection/commands/
├── android/      # android.* 命令
│   ├── hooking.py    # android hooking ...
│   ├── pinning.py    # android sslpinning ...
│   ├── keystore.py   # android keystore ...
│   └── ...
├── ios/          # ios.* 命令
│   ├── keychain.py   # ios keychain ...
│   └── ...
├── memory.py     # memory ... 通用命令
├── filemanager.py
└── ...
```

命令名采用**点分层级**，与目录/模块对应：

| 命令前缀 | 平台 | 例子 |
| --- | --- | --- |
| `android.*` | Android | `android sslpinning disable` |
| `ios.*` | iOS | `ios keychain dump` |
| `memory *` | 通用 | `memory list modules` |
| `env *`、`file *`、`cd`、`ls` | 通用 | `file download /data/.../x.db` |

## 帮助系统

每个命令都有对应的帮助文件（`objection/console/helpfiles/*.txt`）。REPL 里：

```text
# 列出所有命令
help

# 查看某命令用法
help android hooking watch
```

帮助文件名与命令名严格对应，例如 `android.hooking.watch.txt`。

## 常用命令速查

### 连接与环境

```text
env                       # 查看当前环境信息（包名、平台、版本）
```

### 后台任务

很多命令（Hook、监听）会创建**后台 Job**，不阻塞 REPL：

```text
jobs                      # 列出所有 Job
jobs kill <id>            # 结束某个 Job
```

详见 [Jobs 任务](/features/jobs)。

### 执行自定义脚本

```text
# 加载一段 Frida 脚本
objection -g pkg start -S my_script.js
```

## 启动时自动化

`objection start` 支持在进入 REPL 前自动执行命令/脚本（`console/cli.py:142`）：

```bash
# 启动前执行一条命令
objection -g com.example.app start -s 'android sslpinning disable'

# 启动前执行命令文件（每行一条）
objection -g com.example.app start -c cmds.txt

# 启动前加载 Frida 脚本
objection -g com.example.app start -S hook.js
```

这对"一键配置好测试环境"非常有用——比如自动绕过 Pinning + 装好一组 Hook，再进入交互。

## 小结

- REPL = 读取 + 分派 + 输出；
- 命令按 `android.* / ios.* / 通用` 分目录，点分命名；
- 持续性任务以 Job 形式在后台运行，可用 `jobs` 管理；
- 启动期可注入命令/脚本实现自动化。

接下来进入 [功能详解](/features/android-ssl-pinning)，逐个拆解每个能力的实现原理。
