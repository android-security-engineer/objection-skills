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
              { text: '快速上手', link: '/guide/quickstart' }
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
