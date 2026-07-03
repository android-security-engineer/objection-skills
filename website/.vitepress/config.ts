import { defineConfig } from 'vitepress'
import { withMermaid } from 'vitepress-plugin-mermaid'

// https://vitepress.dev/reference/site-config
export default withMermaid(
  defineConfig({
    // 仓库为 android-security-engineer/objection-skills，GitHub Pages 会部署到
    // https://android-security-engineer.github.io/objection-skills/，因此 base 为该子路径。
    base: '/objection-skills/',
    title: 'objection',
    description: '基于 Frida 的运行时移动端安全测试工具 · 教学文档',
    lang: 'zh-CN',
    lastUpdated: true,
    cleanUrls: true,

    head: [
      ['link', { rel: 'icon', type: 'image/png', href: '/objection-skills/logo.png' }],
      // 等宽字体用于品牌名、小标题点缀与代码（signature 的一部分）
      ['link', { rel: 'preconnect', href: 'https://fonts.googleapis.com' }],
      ['link', { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' }],
      ['link', {
        rel: 'stylesheet',
        href: 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600;700&display=swap'
      }]
    ],

    themeConfig: {
      // 站点标题旁的 logo
      logo: '/logo.png',

      nav: [
        { text: '首页', link: '/' },
        { text: '指南', link: '/guide/what-is-objection' },
        {
          text: '功能详解',
          items: [
            { text: 'SSL Pinning 绕过', link: '/features/android-ssl-pinning' },
            { text: 'Root / 越狱检测绕过', link: '/features/root-jailbreak-detection' },
            { text: '方法 Hook', link: '/features/hooking' },
            { text: 'Keystore 监控', link: '/features/android-keystore' },
            { text: 'Keychain Dump', link: '/features/ios-keychain' },
            { text: 'iOS 本地存储取证', link: '/features/ios-local-storage' },
            { text: '堆搜索与操作', link: '/features/heap' },
            { text: '内存 Dump/Patch', link: '/features/memory' },
            { text: '文件系统', link: '/features/filesystem' },
            { text: '运行时操作命令', link: '/features/runtime-commands' },
            { text: 'Android 运行时监控', link: '/features/android-runtime-monitoring' },
            { text: 'APK Patch', link: '/features/patcher' },
            { text: '插件系统', link: '/features/plugins' },
            { text: 'Jobs 任务', link: '/features/jobs' }
          ]
        },
        { text: 'GitHub', link: 'https://github.com/android-security-engineer/objection-skills' }
      ],

      sidebar: {
        '/guide/': [
          {
            text: '入门',
            items: [
              { text: 'objection 是什么', link: '/guide/what-is-objection' },
              { text: '它能解决什么问题', link: '/guide/problems' },
              { text: '整体架构', link: '/guide/architecture' },
              { text: '安装与依赖', link: '/guide/installation' },
              { text: '快速上手', link: '/guide/quickstart' },
              { text: '故障排查', link: '/guide/troubleshooting' }
            ]
          },
          {
            text: '核心概念',
            items: [
              { text: 'Frida 与 Agent', link: '/guide/frida-agent' },
              { text: 'RPC 通信机制', link: '/guide/rpc' },
              { text: 'REPL 与命令', link: '/guide/repl' }
            ]
          },
          {
            text: 'AI Agent 集成',
            items: [
              { text: '面向 AI Agent 使用', link: '/guide/agent-usage' },
              { text: '统一 JSON Schema', link: '/guide/agent-schema' },
              { text: 'HTTP API 端点', link: '/guide/agent-http' }
            ]
          }
        ],
        '/features/': [
          {
            text: 'Android',
            items: [
              { text: 'SSL Pinning 绕过', link: '/features/android-ssl-pinning' },
              { text: 'Root / 越狱检测绕过', link: '/features/root-jailbreak-detection' },
              { text: '方法 Hook', link: '/features/hooking' },
              { text: 'Keystore 监控', link: '/features/android-keystore' },
              { text: '堆搜索与操作', link: '/features/heap' },
              { text: '运行时监控', link: '/features/android-runtime-monitoring' },
              { text: 'APK Patch', link: '/features/patcher' }
            ]
          },
          {
            text: 'iOS',
            items: [
              { text: 'Keychain Dump', link: '/features/ios-keychain' },
              { text: '本地存储取证', link: '/features/ios-local-storage' }
            ]
          },
          {
            text: '通用',
            items: [
              { text: '内存 Dump/Patch', link: '/features/memory' },
              { text: '文件系统', link: '/features/filesystem' },
              { text: '运行时操作命令', link: '/features/runtime-commands' },
              { text: '插件系统', link: '/features/plugins' },
              { text: 'Jobs 任务', link: '/features/jobs' }
            ]
          }
        ],

        '/reference/': [
          { text: '📚 源码模块文档', link: '/reference/' },
          {
            text: '📖 命令速查',
            items: [
              { text: '命令速查总览', link: '/cli/' }
            ]
          },
          {
            text: '🤖 Android 命令',
            collapsed: true,
            items: [
              { text: '总览', link: '/reference/commands/android/' },
              { text: 'clipboard', link: '/reference/commands/android/clipboard' },
              { text: 'command', link: '/reference/commands/android/command' },
              { text: 'general', link: '/reference/commands/android/general' },
              { text: 'generate', link: '/reference/commands/android/generate' },
              { text: 'heap', link: '/reference/commands/android/heap' },
              { text: 'hooking', link: '/reference/commands/android/hooking' },
              { text: 'intents', link: '/reference/commands/android/intents' },
              { text: 'keystore', link: '/reference/commands/android/keystore' },
              { text: 'monitor', link: '/reference/commands/android/monitor' },
              { text: 'pinning', link: '/reference/commands/android/pinning' },
              { text: 'proxy', link: '/reference/commands/android/proxy' },
              { text: 'root', link: '/reference/commands/android/root' }
            ]
          },
          {
            text: '🍎 iOS 命令',
            collapsed: true,
            items: [
              { text: '总览', link: '/reference/commands/ios/' },
              { text: 'binary', link: '/reference/commands/ios/binary' },
              { text: 'bundles', link: '/reference/commands/ios/bundles' },
              { text: 'cookies', link: '/reference/commands/ios/cookies' },
              { text: 'generate', link: '/reference/commands/ios/generate' },
              { text: 'heap', link: '/reference/commands/ios/heap' },
              { text: 'hooking', link: '/reference/commands/ios/hooking' },
              { text: 'jailbreak', link: '/reference/commands/ios/jailbreak' },
              { text: 'keychain', link: '/reference/commands/ios/keychain' },
              { text: 'monitor', link: '/reference/commands/ios/monitor' },
              { text: 'nsurlcredentialstorage', link: '/reference/commands/ios/nsurlcredentialstorage' },
              { text: 'nsuserdefaults', link: '/reference/commands/ios/nsuserdefaults' },
              { text: 'pasteboard', link: '/reference/commands/ios/pasteboard' },
              { text: 'pinning', link: '/reference/commands/ios/pinning' },
              { text: 'plist', link: '/reference/commands/ios/plist' }
            ]
          },
          {
            text: '🛠️ 通用命令',
            collapsed: true,
            items: [
              { text: '总览', link: '/reference/commands/' },
              { text: 'command_history', link: '/reference/commands/command-history' },
              { text: 'custom', link: '/reference/commands/custom' },
              { text: 'device', link: '/reference/commands/device' },
              { text: 'filemanager', link: '/reference/commands/filemanager' },
              { text: 'frida_commands', link: '/reference/commands/frida-commands' },
              { text: 'http', link: '/reference/commands/http' },
              { text: 'jobs', link: '/reference/commands/jobs' },
              { text: 'memory', link: '/reference/commands/memory' },
              { text: 'mobile_packages', link: '/reference/commands/mobile-packages' },
              { text: 'plugin_manager', link: '/reference/commands/plugin-manager' },
              { text: 'sqlite', link: '/reference/commands/sqlite' },
              { text: 'ui', link: '/reference/commands/ui' }
            ]
          },
          {
            text: '🔌 状态层',
            collapsed: true,
            items: [
              { text: '总览', link: '/reference/state/' },
              { text: 'connection', link: '/reference/state/connection' },
              { text: 'app', link: '/reference/state/app' },
              { text: 'device', link: '/reference/state/device' },
              { text: 'filemanager', link: '/reference/state/filemanager' },
              { text: 'jobs', link: '/reference/state/jobs' },
              { text: 'api', link: '/reference/state/api' }
            ]
          },
          {
            text: '⚙️ 工具层',
            collapsed: true,
            items: [
              { text: '总览', link: '/reference/utils/' },
              { text: 'agent', link: '/reference/utils/agent' },
              { text: 'events', link: '/reference/utils/events' },
              { text: 'helpers', link: '/reference/utils/helpers' },
              { text: 'output', link: '/reference/utils/output' },
              { text: 'plugin', link: '/reference/utils/plugin' },
              { text: 'update_checker', link: '/reference/utils/update-checker' },
              { text: 'patchers/base', link: '/reference/utils/patchers/base' },
              { text: 'patchers/android', link: '/reference/utils/patchers/android' },
              { text: 'patchers/ios', link: '/reference/utils/patchers/ios' },
              { text: 'patchers/github', link: '/reference/utils/patchers/github' }
            ]
          },
          {
            text: '🖥️ CLI 与 REPL',
            collapsed: true,
            items: [
              { text: '总览', link: '/reference/console/' },
              { text: 'cli', link: '/reference/console/cli' },
              { text: 'commands', link: '/reference/console/commands' },
              { text: 'repl', link: '/reference/console/repl' },
              { text: 'completer', link: '/reference/console/completer' },
              { text: 'agent_cli', link: '/reference/console/agent_cli' }
            ]
          },
          {
            text: '🌐 HTTP API',
            collapsed: true,
            items: [
              { text: '总览', link: '/reference/api/' },
              { text: 'app', link: '/reference/api/app' },
              { text: 'rpc', link: '/reference/api/rpc' },
              { text: 'script', link: '/reference/api/script' },
              { text: 'agent_endpoints', link: '/reference/api/agent_endpoints' }
            ]
          },
          {
            text: '🪝 Frida Agent',
            collapsed: true,
            items: [
              { text: '总览', link: '/reference/agent/' },
              { text: '入口 index.ts', link: '/reference/agent/index' },
              { text: 'Android 实现总览', link: '/reference/agent/android/' },
              { text: '· clipboard', link: '/reference/agent/android/clipboard' },
              { text: '· filesystem', link: '/reference/agent/android/filesystem' },
              { text: '· general', link: '/reference/agent/android/general' },
              { text: '· heap', link: '/reference/agent/android/heap' },
              { text: '· hooking', link: '/reference/agent/android/hooking' },
              { text: '· intent', link: '/reference/agent/android/intent' },
              { text: '· keystore', link: '/reference/agent/android/keystore' },
              { text: '· monitor', link: '/reference/agent/android/monitor' },
              { text: '· pinning', link: '/reference/agent/android/pinning' },
              { text: '· proxy', link: '/reference/agent/android/proxy' },
              { text: '· root', link: '/reference/agent/android/root' },
              { text: '· shell', link: '/reference/agent/android/shell' },
              { text: '· userinterface', link: '/reference/agent/android/userinterface' },
              { text: '· lib/intent-utils', link: '/reference/agent/android/lib/intent-utils' },
              { text: '· lib/interfaces', link: '/reference/agent/android/lib/interfaces' },
              { text: '· lib/libjava', link: '/reference/agent/android/lib/libjava' },
              { text: '· lib/types', link: '/reference/agent/android/lib/types' },
              { text: 'iOS 实现总览', link: '/reference/agent/ios/' },
              { text: '· binarycookies', link: '/reference/agent/ios/binarycookies' },
              { text: '· binary', link: '/reference/agent/ios/binary' },
              { text: '· bundles', link: '/reference/agent/ios/bundles' },
              { text: '· credentialstorage', link: '/reference/agent/ios/credentialstorage' },
              { text: '· crypto', link: '/reference/agent/ios/crypto' },
              { text: '· filesystem', link: '/reference/agent/ios/filesystem' },
              { text: '· heap', link: '/reference/agent/ios/heap' },
              { text: '· hooking', link: '/reference/agent/ios/hooking' },
              { text: '· jailbreak', link: '/reference/agent/ios/jailbreak' },
              { text: '· keychain', link: '/reference/agent/ios/keychain' },
              { text: '· nsuserdefaults', link: '/reference/agent/ios/nsuserdefaults' },
              { text: '· pasteboard', link: '/reference/agent/ios/pasteboard' },
              { text: '· pinning', link: '/reference/agent/ios/pinning' },
              { text: '· plist', link: '/reference/agent/ios/plist' },
              { text: '· userinterface', link: '/reference/agent/ios/userinterface' },
              { text: '· lib/constants', link: '/reference/agent/ios/lib/constants' },
              { text: '· lib/helpers', link: '/reference/agent/ios/lib/helpers' },
              { text: '· lib/interfaces', link: '/reference/agent/ios/lib/interfaces' },
              { text: '· lib/libobjc', link: '/reference/agent/ios/lib/libobjc' },
              { text: '· lib/types', link: '/reference/agent/ios/lib/types' },
              { text: '通用实现总览', link: '/reference/agent/generic/' },
              { text: '· custom', link: '/reference/agent/generic/custom' },
              { text: '· environment', link: '/reference/agent/generic/environment' },
              { text: '· http', link: '/reference/agent/generic/http' },
              { text: '· memory', link: '/reference/agent/generic/memory' },
              { text: '· ping', link: '/reference/agent/generic/ping' },
              { text: 'RPC 聚合总览', link: '/reference/agent/rpc/' },
              { text: '· rpc/android', link: '/reference/agent/rpc/android' },
              { text: '· rpc/ios', link: '/reference/agent/rpc/ios' },
              { text: '· rpc/environment', link: '/reference/agent/rpc/environment' },
              { text: '· rpc/memory', link: '/reference/agent/rpc/memory' },
              { text: '· rpc/jobs', link: '/reference/agent/rpc/jobs' },
              { text: '· rpc/other', link: '/reference/agent/rpc/other' },
              { text: '公共库总览', link: '/reference/agent/lib/' },
              { text: '· lib/color', link: '/reference/agent/lib/color' },
              { text: '· lib/constants', link: '/reference/agent/lib/constants' },
              { text: '· lib/helpers', link: '/reference/agent/lib/helpers' },
              { text: '· lib/interfaces', link: '/reference/agent/lib/interfaces' },
              { text: '· lib/jobs', link: '/reference/agent/lib/jobs' }
            ]
          },
          {
            text: '🧪 测试',
            collapsed: true,
            items: [
              { text: '总览', link: '/reference/tests/' },
              { text: 'helpers 公共工具', link: '/reference/tests/helpers' },
              { text: 'api/agent-endpoints', link: '/reference/tests/api/agent-endpoints' },
              { text: 'commands/agent-converted-json', link: '/reference/tests/commands/agent-converted-json' },
              { text: 'commands/command-history', link: '/reference/tests/commands/command-history' },
              { text: 'commands/device', link: '/reference/tests/commands/device' },
              { text: 'commands/filemanager', link: '/reference/tests/commands/filemanager' },
              { text: 'commands/frida-commands', link: '/reference/tests/commands/frida-commands' },
              { text: 'commands/jobs', link: '/reference/tests/commands/jobs' },
              { text: 'commands/memory', link: '/reference/tests/commands/memory' },
              { text: 'commands/mobile-packages', link: '/reference/tests/commands/mobile-packages' },
              { text: 'commands/plugin-manager', link: '/reference/tests/commands/plugin-manager' },
              { text: 'commands/ui', link: '/reference/tests/commands/ui' },
              { text: 'commands/android/clipboard', link: '/reference/tests/commands/android/clipboard' },
              { text: 'commands/android/command', link: '/reference/tests/commands/android/command' },
              { text: 'commands/android/heap', link: '/reference/tests/commands/android/heap' },
              { text: 'commands/android/hooking', link: '/reference/tests/commands/android/hooking' },
              { text: 'commands/android/intents', link: '/reference/tests/commands/android/intents' },
              { text: 'commands/android/keystore', link: '/reference/tests/commands/android/keystore' },
              { text: 'commands/android/pinning', link: '/reference/tests/commands/android/pinning' },
              { text: 'commands/android/root', link: '/reference/tests/commands/android/root' },
              { text: 'commands/ios/bundles', link: '/reference/tests/commands/ios/bundles' },
              { text: 'commands/ios/cookies', link: '/reference/tests/commands/ios/cookies' },
              { text: 'commands/ios/hooking', link: '/reference/tests/commands/ios/hooking' },
              { text: 'commands/ios/jailbreak', link: '/reference/tests/commands/ios/jailbreak' },
              { text: 'commands/ios/keychain', link: '/reference/tests/commands/ios/keychain' },
              { text: 'commands/ios/nsurlcredentialstorage', link: '/reference/tests/commands/ios/nsurlcredentialstorage' },
              { text: 'commands/ios/nsuserdefaults', link: '/reference/tests/commands/ios/nsuserdefaults' },
              { text: 'commands/ios/pasteboard', link: '/reference/tests/commands/ios/pasteboard' },
              { text: 'commands/ios/pinning', link: '/reference/tests/commands/ios/pinning' },
              { text: 'commands/ios/plist', link: '/reference/tests/commands/ios/plist' },
              { text: 'console/agent-cli', link: '/reference/tests/console/agent-cli' },
              { text: 'console/cli', link: '/reference/tests/console/cli' },
              { text: 'console/completer', link: '/reference/tests/console/completer' },
              { text: 'console/repl', link: '/reference/tests/console/repl' },
              { text: 'state/app', link: '/reference/tests/state/app' },
              { text: 'state/jobs', link: '/reference/tests/state/jobs' },
              { text: 'utils/helpers', link: '/reference/tests/utils/helpers' },
              { text: 'utils/output', link: '/reference/tests/utils/output' },
              { text: 'utils/patchers/android', link: '/reference/tests/utils/patchers/android' },
              { text: 'utils/patchers/base', link: '/reference/tests/utils/patchers/base' },
              { text: 'utils/patchers/github', link: '/reference/tests/utils/patchers/github' },
              { text: 'utils/patchers/ios', link: '/reference/tests/utils/patchers/ios' }
            ]
          }
        ]
      },

      socialLinks: [
        { icon: 'github', link: 'https://github.com/android-security-engineer/objection-skills' }
      ],

      outline: {
        label: '本页目录',
        level: [2, 3]
      },

      docFooter: {
        prev: '上一页',
        next: '下一页'
      },

      lastUpdated: {
        text: '最后更新于'
      },

      returnToTopLabel: '回到顶部',
      sidebarMenuLabel: '菜单',
      darkModeSwitchLabel: '主题',
      lightModeSwitchTitle: '切换到浅色模式',
      darkModeSwitchTitle: '切换到深色模式',

      search: {
        provider: 'local',
        options: {
          translations: {
            button: {
              buttonText: '搜索文档',
              buttonAriaLabel: '搜索文档'
            },
            modal: {
              noResultsText: '无法找到相关结果',
              resetButtonTitle: '清除查询条件',
              footer: {
                selectText: '选择',
                navigateText: '切换'
              }
            }
          }
        }
      },

      footer: {
        message: '基于 GPL-3.0-or-later 许可发布',
        copyright: 'Copyright © 2017-present objection contributors'
      }
    }
  })
)
