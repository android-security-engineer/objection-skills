# Hooking 控制 <code>agent/src/ios/hooking.ts</code>

`hooking.ts` 在 iOS 目标进程里枚举 ObjC 类与方法、按模式搜索选择子、Hook 类或方法并 dump 参数/返回值/回溯、强制改写方法返回值。它支撑 objection 的 `ios hooking` 全部子命令，是 iOS 动态分析的主力模块。

## 📋 模块概览
| 项目 | 值 |
| --- | --- |
| 文件路径 | `agent/src/ios/hooking.ts` |
| 平台 | iOS |
| 导出 RPC | `iosHookingGetClasses`、`iosHookingGetClassMethods`、`iosHookingWatch`、`iosHookingSearch`、`iosHookingSetReturnValue` |
| 依赖 | `ios/lib/libobjc.ts`、`lib/color.ts`、`lib/jobs.ts` |

## 🎯 解决的问题
- 列出当前进程加载的全部 ObjC 类与某类的方法（可选是否含父类方法）。
- 用 `ApiResolver('objc')` 按 glob 模式搜索选择子，定位要 Hook 的方法。
- Hook 整个类或单个方法，按需 dump 参数、回溯、返回值。
- 强制把某 BOOL 方法的返回值改成 true/false，绕过越狱检测、Root 检测等开关。

## 🏗️ 导出的 RPC 方法
| RPC 名 | 说明 |
| --- | --- |
| `iosHookingGetClasses` | 返回 `ObjC.classes` 全部类 |
| `iosHookingGetClassMethods` | 返回类方法列表，`includeParents` 控制是否含父类方法 |
| `iosHookingWatch` | Hook 类或选择子，按 `dargs/dbt/dret/dparents` 控制输出 |
| `iosHookingSearch` | 按 pattern 搜索 ObjC 选择子 |
| `iosHookingSetReturnValue` | 强制覆盖方法返回值为 true/false |

### `rpc.iosHookingWatch` — Hook 类或方法
源码：`agent/src/ios/hooking.ts:35`

`watch` 建一个 `ios-watch` 任务，根据 pattern 是否含 `[` 判断是选择子模式还是类名：含 `[` 则用 `ApiResolver` 展开所有匹配方法逐个 `watchMethod`，否则调 `watchClass`：
```ts
// agent/src/ios/hooking.ts:44-56
const isPattern = patternOrClass.includes('[');
if (isPattern === true) {
  const matches = objcEnumerate(patternOrClass);
  matches.forEach((match: ApiResolverMatch) => {
    watchMethod(match.name, job, dargs, dbt, dret);
  });
  return;
}
watchClass(patternOrClass, job, dargs, dbt, dret, watchParents);
```
`watchClass` 根据 `parents` 决定遍历 `$methods` 还是 `$ownMethods`，拼成 `-[Class method]` 选择子交给 `watchMethod`（`:71-76`）。

### `watchMethod` — 拦截单个选择子
源码：`agent/src/ios/hooking.ts:80`

用 `ApiResolver('objc')` 解析选择子地址，`Interceptor.attach` 挂上。`onEnter` 统计参数个数（按 `:` 数量），打印调用与 receiver `$kind`/`$superClass`；按 `dbt` 打回溯、按 `dargs` dump 参数（args[0]=self, args[1]=selector, args[2+]=实参）：
```ts
// agent/src/ios/hooking.ts:139-151
if (dargs && argumentCount > 0) {
  const methodSplit = ObjC.selectorAsString(args[1]).split(":").filter((val) => val);
  const r = methodSplit.map((argName, position) => {
    const t = new ObjC.Object(args[position + 2]);
    return `${argName}: ${c.greenBright(`${t}`)}`;
  });
  send(...`Argument dump: [${c.green(receiver.$className)} ${r.join(" ")}]`);
}
```
`onLeave` 按 `dret` 打印返回值（`:157-161`），`InvocationListener` 加入任务。

### `rpc.iosHookingSetReturnValue` — 改写返回值
源码：`agent/src/ios/hooking.ts:167`

`TRUE = 0x1`、`FALSE = 0x0`。`ApiResolver` 解析选择子，`onLeave` 比较当前返回值，不同则 `retval.replace`：
```ts
// agent/src/ios/hooking.ts:202-216
const watchInvocation: InvocationListener = Interceptor.attach(matchedMethod.address, {
  onLeave: (retval) => {
    switch (returnValue) {
      case true:
        if (retval.equals(TRUE)) { return; }
        retval.replace(TRUE);
        break;
      case false:
        if (retval.equals(FALSE)) { return; }
        retval.replace(FALSE);
        break;
    }
  },
});
```

### `rpc.iosHookingSearch` — 选择子搜索
源码：`agent/src/ios/hooking.ts:27`

不含 `[` 时自动补成 `*[*<pattern>* *]` 通配模式，再 `objcEnumerate`：
```ts
// agent/src/ios/hooking.ts:29-32
if (!patternOrClass.includes('[')) patternOrClass = `*[*${patternOrClass}* *]`;
return objcEnumerate(patternOrClass);
```

```mermaid
flowchart TD
    RPC[rpc.iosHookingWatch] --> JOB[new ios-watch 任务]
    JOB --> CHK{pattern 含 [ ?}
    CHK -->|是 选择子| ENUM[objcEnumerate 展开匹配]
    CHK -->|否 类名| WC[watchClass]
    ENUM --> LOOP[forEach watchMethod]
    WC --> METHODS[$methods / $ownMethods]
    METHODS --> LOOP2[拼 -[Class method] watchMethod]
    LOOP --> WM[watchMethod]
    LOOP2 --> WM
    WM --> RES[ApiResolver 解析地址]
    RES --> ATT[Interceptor.attach]
    ATT --> ONENTER[onEnter: 参数/回溯/receiver]
    ATT --> ONLEAVE[onLeave: 返回值]
    ATT --> ADD[job.addInvocation]
```

## ⚙️ 实现要点
- **ApiResolver('objc')**：Frida 提供的 ObjC 选择子解析器，支持 glob，`watchMethod` 与 `search` 都经 `objcEnumerate`（`:23-25`）。
- **参数偏移 +2**：ObjC 方法 `args[0]=self`、`args[1]=selector`、`args[2+]=` 实参，dump 参数时按 `position + 2` 取（`:149`）。
- **多匹配告警**：`resolved.length > 1` 时发警告但只 Hook 第一个（`:101-103`，源码注释 TODO 待正确循环 glob）。
- **任务分组**：`watch` 把多个 `watchMethod` 的 `InvocationListener` 收进同一 `ios-watch` 任务，便于 `ios hooking list` 统一管理。

## 🔍 源码索引
| 符号 | 位置 |
| --- | --- |
| `getClasses` | `agent/src/ios/hooking.ts:6` |
| `getClassMethods` | `agent/src/ios/hooking.ts:10` |
| `objcEnumerate` | `agent/src/ios/hooking.ts:23` |
| `search` | `agent/src/ios/hooking.ts:27` |
| `watch` | `agent/src/ios/hooking.ts:35` |
| `watchClass` | `agent/src/ios/hooking.ts:59` |
| `watchMethod` | `agent/src/ios/hooking.ts:80` |
| `setMethodReturn` | `agent/src/ios/hooking.ts:167` |

## 🔗 相关文档
- [Frida 与 Agent](/guide/frida-agent)
- [RPC 通信机制](/guide/rpc)
- 任务管理：[`/reference/agent/lib/jobs`](/reference/agent/lib/jobs)
- 命令文档：[/reference/commands/ios/hooking](/reference/commands/ios/hooking)
