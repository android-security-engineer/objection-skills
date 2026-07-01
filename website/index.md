---
layout: home

hero:
  name: objection
  text: Runtime Mobile Exploration
  tagline: 基于 Frida 的运行时移动端安全测试工具，无需越狱即可审视 App 安全姿态
  image:
    src: /logo.png
    alt: objection
  actions:
    - theme: brand
      text: 快速开始
      link: /guide/quickstart
    - theme: alt
      text: objection 是什么？
      link: /guide/what-is-objection

features:
  - icon: 📱
    title: 跨平台
    details: 同时支持 iOS 与 Android，一套工具、一套命令、一套思路覆盖两大移动平台。
  - icon: 🔓
    title: 无需越狱
    details: 借助 Frida Gadget 重新打包应用或附加到已运行进程，普通设备即可进行运行时测试。
  - icon: 🪝
    title: 运行时 Hook
    details: 列举类与方法、监听调用、修改返回值，无需反编译重打包即可动态改变 App 行为。
  - icon: 🔐
    title: 凭证与密钥
    details: 一键绕过 SSL Pinning、Dump iOS Keychain / Android Keystore、提取本地存储数据。
  - icon: 🧠
    title: 堆与内存
    details: 搜索堆上对象实例、调用其方法、Dump 与 Patch 进程内存，深度探索运行时状态。
  - icon: 🧩
    title: 可扩展
    details: Python 插件机制 + Frida 脚本注入，把自定义能力无缝接入 REPL。
---

## objection 在做什么

objection 把 [Frida](https://www.frida.re/) 的动态插桩能力，封装成一套**面向安全测试人员**的交互式命令行。你不必手写每一行 Frida 脚本——objection 已经把"绕过证书校验""Hook 某个方法""Dump 钥匙串"这些高频任务做成了开箱即用的命令。

下图展示了从你敲下一行命令，到目标 App 被改变行为之间的完整链路：

```mermaid
flowchart LR
    U[安全测试人员] -->|objection 命令| CLI[Python CLI<br/>REPL]
    CLI -->|frida-python| FRIDA[Frida Core]
    FRIDA -->|注入 agent.js| AGENT[Agent<br/>TypeScript]
    AGENT -->|Java/ObjC 桥接| APP[目标 App 进程]
    APP -->|RPC 返回结果| AGENT
    AGENT -->|message 回调| CLI
    CLI -->|格式化输出| U
```

## 文档站定位

这是一个**教学站点**。读完它，你将完全理解：

- objection **解决了什么问题**，以及为什么需要运行时测试；
- 它的**整体架构**——Python、Frida、Agent 三者如何协作；
- 每一个功能点的**实现原理与细节**，而不只是"敲哪条命令"。

> 接下来推荐从 [objection 是什么](/guide/what-is-objection) 开始，建立全局认识。
