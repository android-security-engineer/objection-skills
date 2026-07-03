# 文件系统操作 <code>commands/filemanager.py</code>

本模块是 objection 跨平台文件系统的核心，覆盖目录浏览（`ls/cd/pwd`）、上传/下载、删除、查看（`cat`），以及供 REPL tab 补全的短列表辅助函数，共 27 个函数。命令组前缀为 `filesystem ...`、`ls`、`cd`、`pwd`、`rm`。iOS 与 Android 各有一套对称实现，由平台分发。本文为 reference 版逐函数详解。

## 📋 模块概览

| 项目 | 值 |
| --- | --- |
| 文件路径 | `objection/commands/filemanager.py` |
| Agent 实现 | `agent/src/ios/filesystem.ts`、`agent/src/android/filesystem.ts` |
| 命令组 | `ls`、`cd`、`pwd`、`rm`、`filesystem download/upload/cat` |
| 依赖 | `os`、`tempfile`、`time`、`click`、`tabulate`、`objection.state.connection`、`objection.state.device`、`objection.state.filemanager`、`objection.utils.helpers`、`objection.utils.output` |

## 🎯 解决的问题

- 在设备上像本地一样 `ls/cd/pwd`，路径语义跨 iOS/Android。
- 上传/下载文件与目录（目录需 `--folder` 递归）。
- 远程删除文件，带交互确认（JSON 模式跳过）。
- `cat` 远程文件内容到本地终端。
- tab 补全当前目录下的文件/文件夹名。
- 模块级 `_ls_cache` 缓存短列表，加速补全；写操作后自动失效对应缓存。

## 📜 命令清单

| 命令 | 函数 | 说明 |
| --- | --- | --- |
| `cd <dir>` | `cd()` | 切换工作目录（更新本地状态） |
| `pwd` | `pwd_print()` | 打印当前工作目录 |
| `ls [path]` | `ls()` | 列出目录内容 |
| `filesystem download <remote> [local] [--folder]` | `download()` | 下载文件/目录 |
| `filesystem upload <local> [remote]` | `upload()` | 上传本地文件 |
| `rm <file>` | `rm()` | 删除远程文件 |
| `filesystem cat <remote>` | `cat()` | 打印远程文件内容 |

辅助 / 内部函数：

| 函数 | 作用 |
| --- | --- |
| `_should_download_folder` | 检测 `--folder` |
| `path_exists` | 平台分发判断路径是否存在 |
| `_path_exists_ios` / `_path_exists_android` | 各平台实现 |
| `pwd`（内部） | 返回当前 cwd 字符串 |
| `_pwd_ios` / `_pwd_android` | 各平台取 cwd |
| `_ls_ios` / `_ls_android` | 各平台 ls 渲染 |
| `_download_ios` / `_download_android` | 各平台下载 |
| `_upload_ios` / `_upload_android` | 各平台上传 |
| `_rm_ios` / `_rm_android` | 各平台删除 |
| `_get_short_ios_listing` / `_get_short_android_listing` | 短列表（带缓存） |
| `list_folders_in_current_fm_directory` | 补全：当前目录文件夹 |
| `list_files_in_current_fm_directory` | 补全：当前目录文件 |
| `list_content_in_current_fm_directory` | 补全：当前目录全部 |

## ⚙️ 实现原理

模块维护 `file_manager_state.cwd` 作为当前工作目录状态，`_ls_cache` 字典缓存短列表。所有实际操作走 `state_connection.get_api()` 的 `ios_file_*` / `android_file_*` RPC。路径分隔符取 `device_state.platform.path_separator`，相对路径会与 `pwd()` 拼接成绝对路径。

### `cd()` — 切换目录

源码：[`objection/commands/filemanager.py:32`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L32)

逻辑分四支：`.` 不动（`:66-72`）；`..` 用 `os.path.split` 回退一层，根目录不动（`:77-100`）；绝对路径校验存在后切换（`:104-145`）；相对路径拼 `pwd` 后校验（`:149-199`）。存在性校验走 `_path_exists_ios/android`。JSON 模式返回 `cwd` 与 `changed` 布尔。

### `path_exists()` / `_path_exists_*` — 路径存在性

`path_exists`（[`objection/commands/filemanager.py:202`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L202)）平台分发；`_path_exists_ios`（`:217`）调 `api.ios_file_exists(path)`；`_path_exists_android`（`:229`）调 `api.android_file_exists(path)`。

### `pwd()` / `pwd_print()` / `_pwd_*` — 工作目录

内部 `pwd`（[`objection/commands/filemanager.py:241`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L241)）：优先返回 `file_manager_state.cwd`，否则按平台调 `_pwd_ios`（`:283`）/`_pwd_android`（`:300`），两者调 `ios_file_cwd` / `android_file_cwd` 并回写状态。`pwd_print`（`:264`）打印或 JSON 返回 `{cwd}`。

### `ls()` — 列目录

源码：[`objection/commands/filemanager.py:317`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L317)

无路径用 `pwd()`；相对路径拼 `pwd`。**JSON 模式直接返回原始 listing**（跳过表格渲染，`:335-352`）：

```python
# objection/commands/filemanager.py:335-352
if should_output_json(args):
    api = state_connection.get_api()
    if device_state.platform == Ios:
        data = api.ios_file_ls(path)
    elif device_state.platform == Android:
        data = api.android_file_ls(path)
    ...
    return output_result(
        CommandResult(
            result={'path': path, 'readable': data.get('readable'),
                    'writable': data.get('writable'), 'files': data.get('files')},
        ),
        command='ls',
    )
```

非 JSON 模式分发到 `_ls_ios`（`:364`）/`_ls_android`（`:438`）。

### `_ls_ios()` / `_ls_android()` — 渲染

`_ls_ios`（[`objection/commands/filemanager.py:364`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L364)）调 `ios_file_ls`，内含两个嵌套 helper（`_get_key_if_exists`、`_humanize_size_if_possible`），用 `tabulate` 渲染十列：`NSFileType/Perms/NSFileProtection/Read/Write/Owner/Group/Size/Creation/Name`（`:406-432`）。`_ls_android`（`:438`）调 `android_file_ls`，嵌套 `_timestamp_to_str` 把毫秒时间戳转 `GMT` 字符串，渲染七列：`Type/Last Modified/Read/Write/Hidden/Size/Name`（`:466-484`）。两者在目录不可读时跳过表格，仅打印可读/可写汇总。

### `download()` — 下载

源码：[`objection/commands/filemanager.py:489`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L489)

源/目标解析：缺目标时用 `os.path.basename(source)`（`:518-519`）。`_should_download_folder` 决定是否递归目录。平台分发到 `_download_ios`（`:540`）/`_download_android`（`:604`）。JSON 模式返回 `action/source/destination/folder`（`:529-536`）。

### `_download_ios()` / `_download_android()` — 下载实现

两者结构对称（[`objection/commands/filemanager.py:540`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L540)、`:604`）：相对路径拼 `pwd`；先校验可读（`ios_file_readable`/`android_file_readable`）；若不是文件且未指定 `--folder` 则提示并返回；目录递归时 `os.makedirs` 建本地目录，根节点 `click.confirm` 确认（JSON 模式跳过，`:575`/`:639`），列目录后递归调用自身（`path_root=False`）：

```python
# objection/commands/filemanager.py:580-585
data = api.ios_file_ls(path)
for name, _ in data['files'].items():
    sub_path = device_state.platform.path_separator.join([path, name])
    sub_destination = os.path.join(destination, name)
    _download_ios(sub_path, sub_destination, True, False)
```

文件下载走 `ios_file_download`/`android_file_download`，把 `file_data['data']` 转 bytearray 写本地（`:598-599`/`:661-662`）。

### `upload()` — 上传

源码：[`objection/commands/filemanager.py:667`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L667)

缺源报错。目标缺省时拼 `pwd + basename(source)`（`:693-694`）。平台分发到 `_upload_ios`（`:712`）/`_upload_android`（`:747`）。JSON 模式返回 `action/source/destination`（`:702-708`）。

### `_upload_ios()` / `_upload_android()` — 上传实现

两者对称（[`objection/commands/filemanager.py:712`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L712)、`:747`）：目标相对路径拼 `pwd`；校验目标父目录可写（`ios_file_writable`/`android_file_writable`）；本地文件读为 bytes 再 `.hex()` 成字符串发设备：

```python
# objection/commands/filemanager.py:733-737
with open(path, 'rb') as f:
    data = f.read().hex()
...
api.ios_file_upload(destination, data)
```

上传后**失效 `_ls_cache` 对应目录的缓存**（`:743-744`/`:778-779`），保证下次补全看到新文件。

### `rm()` — 删除

源码：[`objection/commands/filemanager.py:782`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L782)

相对路径拼 `pwd`。**JSON 模式跳过交互确认**（`:810-813`）：

```python
# objection/commands/filemanager.py:810-813
if not should_output_json(args):
    if not click.confirm('Really delete {0} ?'.format(target)):
        click.secho('Not deleting {0}'.format(target), dim=True)
        return None
```

平台分发到 `_rm_ios`（`:855`）/`_rm_android`（`:830`）。JSON 模式返回 `action/target/deleted`。

### `_rm_ios()` / `_rm_android()` — 删除实现

两者对称（[`objection/commands/filemanager.py:830`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L830)、`:855`）：先 `_path_exists_*` 校验存在；调 `ios_file_delete`/`android_file_delete`；失效 `_ls_cache` 对应目录缓存（`:849-850`/`:874-875`）；返回布尔。

### `cat()` — 查看文件

源码：[`objection/commands/filemanager.py:880`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L880)

用 `tempfile.mkstemp('.file')` 建临时文件，复用 `_download_ios/android`（`should_download_folder=False`）拉下来。JSON 模式读临时文件内容入 `result.content` 后删除（`:918-925`）；非 JSON 打印内容（`:927-930`）后删除。

### `_get_short_ios_listing()` / `_get_short_android_listing()` — 短列表（带缓存）

`_get_short_ios_listing`（[`objection/commands/filemanager.py:936`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L936)）：取 `pwd()`，命中 `_ls_cache` 直接返回；否则 `ios_file_ls` 后按 `NSFileType` 标记 `directory`/`file`，存缓存返回（`:952-978`）。`_get_short_android_listing`（`:981`）按 `isDirectory` 标记（`:1010`）。

### `list_folders_in_current_fm_directory()` 等 — 补全辅助

三个函数（[`objection/commands/filemanager.py:1019`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L1019)、`:1053`、`:1087`）结构相同：取短列表，按 type 过滤（folders/files/全部），对含空格的文件名加单引号包裹，返回 `{name: name}` 字典供 REPL tab 补全（`:1044-1048` 等）。

```mermaid
flowchart TD
    A["cd(args)"] --> B{"path 形态"}
    B -- "." --> C["不动 cwd"]
    B -- ".." --> D["os.path.split 回退"]
    B -- 绝对 --> E["校验存在后切换"]
    B -- 相对 --> F["拼 pwd 后校验"]
    E --> G["file_manager_state.cwd = path"]
    F --> G

    H["ls(args)"] --> I{"JSON 模式?"}
    I -- 是 --> J["返回原始 listing{path,readable,writable,files}"]
    I -- 否 --> K["_ls_ios / _ls_android 渲染"]

    L["download(args)"] --> M{"--folder?"}
    M -- 否 --> N["校验可读 → 下载文件 → 写本地"]
    M -- 是 --> O["makedirs + 递归下载"]

    P["upload(args)"] --> Q["读本地 .hex()"]
    Q --> R["校验父目录可写 → file_upload"]
    R --> S["失效 _ls_cache"]

    T["rm(args)"] --> U{"JSON?"}
    U -- 否 --> V["click.confirm"]
    U -- 是 --> W["跳过确认"]
    V --> X["file_delete + 失效缓存"]
    W --> X
```

## 🔌 JSON 模式行为

- `cd`：返回 `cwd` 与 `changed` 布尔；根目录时带 `at_root: True`；非法路径返回 `status='error'`。
- `ls`：**直接返回原始 listing**，不做表格渲染——Agent 友好化的关键差异（`:335-352`）。
- `download`：返回 `action/source/destination/folder`；目录递归时**跳过** `click.confirm`（`:575`/`:639`）。
- `upload`：返回 `action/source/destination`。
- `rm`：**跳过** `click.confirm` 直接删除（`:810`）。
- `cat`：把文件内容读入 `result.content` 返回。
- 缺参数的命令在 JSON 模式返回 `status='error'`、`exit_code=1` 与 `human_text` 用法。

## 🔍 源码索引

| 符号 | 位置 |
| --- | --- |
| `_ls_cache` | [`objection/commands/filemanager.py:18`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L18) |
| `_should_download_folder` | [`objection/commands/filemanager.py:21`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L21) |
| `cd` | [`objection/commands/filemanager.py:32`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L32) |
| `path_exists` | [`objection/commands/filemanager.py:202`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L202) |
| `_path_exists_ios` | [`objection/commands/filemanager.py:217`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L217) |
| `_path_exists_android` | [`objection/commands/filemanager.py:229`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L229) |
| `pwd` | [`objection/commands/filemanager.py:241`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L241) |
| `pwd_print` | [`objection/commands/filemanager.py:264`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L264) |
| `_pwd_ios` | [`objection/commands/filemanager.py:283`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L283) |
| `_pwd_android` | [`objection/commands/filemanager.py:300`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L300) |
| `ls` | [`objection/commands/filemanager.py:317`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L317) |
| `_ls_ios` | [`objection/commands/filemanager.py:364`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L364) |
| `_ls_android` | [`objection/commands/filemanager.py:438`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L438) |
| `download` | [`objection/commands/filemanager.py:489`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L489) |
| `_download_ios` | [`objection/commands/filemanager.py:540`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L540) |
| `_download_android` | [`objection/commands/filemanager.py:604`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L604) |
| `upload` | [`objection/commands/filemanager.py:667`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L667) |
| `_upload_ios` | [`objection/commands/filemanager.py:712`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L712) |
| `_upload_android` | [`objection/commands/filemanager.py:747`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L747) |
| `rm` | [`objection/commands/filemanager.py:782`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L782) |
| `_rm_android` | [`objection/commands/filemanager.py:830`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L830) |
| `_rm_ios` | [`objection/commands/filemanager.py:855`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L855) |
| `cat` | [`objection/commands/filemanager.py:880`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L880) |
| `_get_short_ios_listing` | [`objection/commands/filemanager.py:936`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L936) |
| `_get_short_android_listing` | [`objection/commands/filemanager.py:981`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L981) |
| `list_folders_in_current_fm_directory` | [`objection/commands/filemanager.py:1019`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L1019) |
| `list_files_in_current_fm_directory` | [`objection/commands/filemanager.py:1053`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L1053) |
| `list_content_in_current_fm_directory` | [`objection/commands/filemanager.py:1087`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L1087) |

## 🧭 工作目录（cwd）状态机

`file_manager_state.cwd` 是 objection 侧维护的"虚拟 cwd"，设备端并不真正切换目录——每次操作都把 cwd 拼到路径前发给 Frida。首次访问时 `cwd` 为 `None`，触发一次 `ios_file_cwd`/`android_file_cwd` RPC 回填（[`objection/commands/filemanager.py:254`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L254)），此后所有 `pwd()` 命中本地状态，不再产生 RPC。

```mermaid
stateDiagram-v2
    [*] --> Uninitialized: 进程启动
    Uninitialized --> Initialized: pwd() 首次调用\n(_pwd_ios/android 回填)
    Initialized --> Initialized: cd 切换 / 命中本地
    Initialized --> Initialized: upload/rm 后失效 _ls_cache\n(不影响 cwd)
    note right of Uninitialized: cwd = None\n任何 pwd() 触发 RPC
    note right of Initialized: cwd = 绝对路径\npwd() 零 RPC
```

边界情况：`cd ..` 在根目录时 `os.path.split` 返回长度 1 的元组，状态不变并返回 `at_root: True`（`:82-88`）；相对路径规范化后若变成 `//`（Linux 根的拼接产物）也视作根，状态不变（`:156-162`）。`cd` 失败（路径不存在）时 **不修改** `cwd`，仅返回 `status='error'`，保证虚拟 cwd 不会被脏路径污染。

## 📡 文件操作时序：以 `filesystem cat` 为例

`cat` 不直接读设备文件，而是用 `tempfile.mkstemp('.file')` 建本地临时文件，复用 `_download_*` 把字节流拉到本地，再读回终端，最后 `os.remove` 清理（[`objection/commands/filemanager.py:910`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L910)）。JSON 模式额外把内容读入 `result.content`（`:918-925`）。

```mermaid
sequenceDiagram
    participant U as 用户/Agent
    participant C as cat(args)
    participant T as tempfile
    participant D as _download_ios/android
    participant A as Frida Agent (RPC)
    participant FS as 设备文件系统

    U->>C: filesystem cat <remote>
    C->>T: mkstemp('.file') → destination
    C->>D: download(source, destination, False)
    D->>A: ios_file_readable(path)
    A->>FS: stat 可读性
    A-->>D: true/false
    alt 不可读
        D-->>C: 红色提示并 return
    else 可读
        D->>A: ios_file_path_is_file(path)
        A-->>D: true
        D->>A: ios_file_download(path)
        A->>FS: read bytes
        A-->>D: {data: [...]}
        D->>FS(本地): open(dest,'wb').write(bytearray(data))
    end
    C->>T: open(dest,'r',errors='ignore').read()
    alt JSON 模式
        C-->>U: {path, content}
    else 交互模式
        C-->>U: ==== 内容 ====
    end
    C->>T: os.remove(destination)
```

关键技术点：`errors='ignore'` 让二进制文件也能"猫"出来而不抛 `UnicodeDecodeError`（`:919`、`:928`），代价是非法字节被静默丢弃——对取证场景需注意 `cat` 不保证字节级保真，应改用 `filesystem download`。临时文件后缀固定为 `.file`，多进程并发 `cat` 时由 `mkstemp` 保证不冲突（`O_EXCL` 语义）。

## 🔁 上传/下载数据流与编码

上传与下载走两条不对称的编码路径：下载是 `bytearray(file_data['data'])` 直接落盘（`:599`/`:662`），上传则把本地 bytes `.hex()` 成十六进制字符串再发设备（`:734`/`:769`）。hex 编码使传输体积翻倍但规避了 Frida RPC 二进制传递的边界问题（消息走 JSON 序列化）。

```
+------------------+      下载      +------------------+
|  设备文件        | --read----> |  Frida Agent     |
|  /path/to/file   |             |  file_download() |
+------------------+             +------------------+
                                         |
                                   {data: [int,...]}
                                         |  bytearray()
                                         v
                                 +------------------+
                                 |  本地文件        |
                                 |  ./to/file       |
                                 +------------------+

+------------------+      上传      +------------------+
|  本地文件        | --read---> |  commands 层     |
|  ./from/file     |   bytes    |  .hex() 编码     |
+------------------+             +------------------+
                                         |
                                   "a1b2c3..." (str)
                                         |  file_upload(dest, hex)
                                         v
                                 +------------------+
                                 |  Frida Agent     |
                                 |  解码写设备      |
                                 +------------------+
```

目录递归下载的栈深度：`_download_ios/android` 通过 `path_root` 参数区分"用户发起的根调用"与"递归子调用"（`:540`/`:604`）。只有 `path_root=True` 时才弹 `click.confirm` 与"Streaming/Recursive finished"提示，避免递归每层都问用户。递归无显式深度上限，依赖设备目录树深度；遇到符号链接循环理论上可能爆栈，实测 objection 不解析 symlink 目标，因此相对安全。

缓存失效策略：`_ls_cache` 是模块级全局 dict，key 为目录绝对路径。`upload` 失效**目标父目录**（`os.path.dirname(destination)`，`:743`/`:778`），`rm` 同样失效**被删文件的父目录**（`:849`/`:874`）。注意 `download` 与 `cat` **不失效缓存**——因为它们不改设备目录列表。`cd` 也不失效缓存，但切换到的目标目录若从未缓存，下次补全会触发一次 `ls` RPC。

```mermaid
flowchart LR
    subgraph 写操作
      U[upload] -->|失效 dirname| C1[_ls_cache]
      R[rm] -->|失效 dirname| C1
    end
    subgraph 只读操作
      L[ls] -->|填充| C1
      S[补全 _get_short_*] -->|读缓存/填充| C1
      D[download/cat] -.->|不触碰| C1
      CD[cd] -.->|不触碰| C1
    end
    C1 -->|key = 绝对路径| N[(下一个 tab 补全)]
```

## 🐛 边界情况与错误处理汇总

- **缺参**：所有命令在 `len(args) < 1` 时，JSON 模式返回 `status='error'` + `human_text` 用法 + `exit_code=1`，交互模式仅 `click.secho` 用法（如 `cd` 在 [`:48-60`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/filemanager.py#L48)）。
- **未知平台**：`ls` 的 JSON 分支显式处理 `else` 返回 `unknown platform` 错误（`:341-345`），但 `cd`/`download` 等的 `if Ios / if Android` 链没有 `else`，未知平台会**静默跳过**所有分支，`cwd` 不变、文件不下载——这是潜在陷阱。
- **下载目标已存在**：目录下载时若本地 `destination` 已存在，直接 `return` 不覆盖（`:568-570`/`:632-634`），避免误删已有本地目录。
- **上传目标父目录不可写**：先 `ios_file_writable(os.path.dirname(destination))` 校验（`:728`/`:763`），不可写直接 return，不传字节。
- **iOS `NSFileType` 缺失**：`_get_short_ios_listing` 跳过没有 `NSFileType` 属性的条目（`:968-969`），Android 版无此保护——平台行为差异。
- **文件名含空格**：补全函数对含空格名加单引号包裹（`:1045-1048`），让 REPL 词法分析器把整段当一个 token。

## 🔗 相关文档

- [文件系统](/features/filesystem)
- [RPC 通信机制](/guide/rpc)
- [REPL 与命令](/guide/repl)
