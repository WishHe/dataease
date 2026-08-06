# 外部 API 调用记录

本文档记录 DataEase core-frontend 中所有不经过后端代理（`192.168.0.222:8100`）的外部 API 请求和资源加载。

---

## 1. MaxKB AI 助手（iframe 嵌入）

- **域名**: `https://maxkb.fit2cloud.com`
- **触发方式**: 点击 Header 顶部导航栏右侧的 AI 助手图标，从页面右下角弹出 iframe 面板
- **方式**: iframe 嵌入 MaxKB 聊天页面，iframe 内部 JS 自行调用 MaxKB 后端接口

**图标位置**: `src/layout/components/Header.vue:159-167`，位于 `<div class="operate-setting">` 中

**面板位置**: `src/layout/components/AiComponent.vue:50`，CSS `position: fixed; bottom: 48px; right: 36px`

**涉及文件**:

| 文件 | 说明 |
|------|------|
| `src/layout/components/Header.vue:35` | 默认 baseUrl 定义 (`aiBaseUrl`) |
| `src/layout/components/Header.vue:88-103` | `initAiBase()` 调用 `/aiBase/findTargetUrl` 动态获取 URL |
| `src/layout/components/Header.vue:159-167` | AI 助手触发图标（Header 右侧） |
| `src/layout/components/Header.vue:215-218` | `<ai-component>` 面板渲染 |
| `src/layout/components/AiComponent.vue` | AI 面板组件（fixed 定位在右下角） |
| `src/layout/components/DesktopSetting.vue:19` | 桌面版中同样的默认 URL |
| `src/api/aiComponent.ts` | `/aiBase/findTargetUrl` 接口，后端可动态覆盖 URL |

> URL 优先级：后端接口返回 > 代码默认值。如果 `/aiBase/findTargetUrl` 返回空或未配置，使用硬编码的 `https://maxkb.fit2cloud.com/ui/chat/2ddd8b594ce09dbb?mode=embed`。

**iframe 内实际调用的 MaxKB API**（由 MaxKB SDK 自动发起）:

| 接口 | 用途 |
|------|------|
| `https://maxkb.fit2cloud.com/api/profile` | 获取 MaxKB 用户信息 |
| `https://maxkb.fit2cloud.com/api/application/authentication` | 应用认证校验 |
| `https://maxkb.fit2cloud.com/api/display/info` | 显示信息配置 |
| `https://maxkb.fit2cloud.com/api/application/profile` | 应用配置信息 |
| `https://maxkb.fit2cloud.com/api/application/{id}/chat/client/1/20` | AI 对话接口 |

> **注意**: 这些请求由 iframe 内的 MaxKB SDK 自动发起，不是 DataEase 前端直接调用，无法通过 Vite 代理拦截。

---

## 2. 模板市场

- **域名**: `https://dataease.io/templates`（由后端动态返回，`src/views/template-market/index.vue:433`）
- **触发时机**: 进入模板市场页面
- **方式**: 缩略图加载（`<img>` 标签）、模板预览（`window.open()`）

**涉及文件**:

| 文件 | 行号 | 用途 |
|------|------|------|
| `src/views/template-market/index.vue` | 316 | 初始默认值 `baseUrl` |
| `src/views/template-market/index.vue` | 433 | 后端返回的真实 `baseUrl` 覆盖默认值 |
| `src/views/template-market/index.vue` | 367 | 缩略图路径拼接 `baseUrl + thumbnail` |
| `src/views/template-market/index.vue` | 531-533 | `window.open(baseUrl)` 跳转预览 |
| `src/views/template-market/component/MarketPreview.vue` | 124 | 预览弹窗同样逻辑 |
| `src/views/template-market/component/MarketPreviewV2.vue` | 194 | 新版预览弹窗同样逻辑 |

> 模板列表数据本身通过后端 `/templateMarket/*` 接口返回（走 `192.168.0.222` 代理），仅缩略图和外部跳转使用 dataease.io 域名。

---

## 3. XpackComponent 插件动态加载

- **触发时机**: 系统初始化、特定页面加载（路由中包含 `plugin: true` 标记的页面）
- **方式**: 从后端拉取加密/混淆的 JS 代码，动态解密并执行

**涉及文件**:

| 文件 | 说明 |
|------|------|
| `src/components/plugin/src/index.vue` | 核心插件加载器 |
| `src/api/plugin.ts` | 插件 API：`/xpackComponent/content/{key}`、`/DEXPack.umd.js`、`/xpackModel` |
| `src/config/axios/service.ts:188-192` | 响应拦截器中 xpack 特殊处理（跳过错误提示） |

**加载流程**:

```
1. /xpackModel → 判断部署模式
2. 分布式: /DEXPack.umd.js → new Function(code)() 执行远程代码
3. 非分布式: /xpackComponent/content/{key} → 解密 → 动态 import Vue 组件
```

> **注意**: 这些请求走标准 axios 请求（经过 Vite 代理到 `192.168.0.222`），但插件代码执行后可能产生额外的外部请求。

---

## 4. 第三方 AI 助手对接

- **触发时机**: 系统设置 > 第三方对接 > 保存验证
- **方式**: `fetch()` 直接请求用户配置的第三方域名（绕过代理）

**涉及文件**:

| 文件 | 行号 | 说明 |
|------|------|------|
| `src/views/system/parameter/third-party/ThirdEdit.vue` | 101-104 | 保存前验证：`fetch({domain}/api/v1/system/assistant/validate/{id})` |
| `src/views/system/parameter/third-party/ThirdEdit.vue` | 136 | 同上 |

> 该 URL 由用户在系统设置中配置，非固定地址。因为域名完全由用户指定，无法走 Vite 代理。

---

## 5. 地图样式资源

- **触发时机**: 图表渲染时加载自定义地图样式
- **方式**: `fetch()` 直接请求外部 JSON

**涉及文件**:

| 文件 | 行号 | 说明 |
|------|------|------|
| `src/views/system/parameter/map/OnlineMapCustom.vue` | 144 | 在线自定义地图样式 `fetch(config.styleUrl)` |
| `src/views/chart/components/js/panel/common/common_antv.ts` | 1666 | AntV 图表地图样式 `fetch(mapKey.styleUrl)` |

> URL 由用户或配置决定，非固定地址。

---

## 6. 文档与社区链接（纯外链，无 API 调用）

以下 URL 仅作为 `<a>` 链接或 `window.open()` 跳转，不会自动发起 HTTP 请求：

| 文件 | 行号 | URL | 用途 |
|------|------|-----|------|
| `src/layout/components/TopDoc.vue` | 20 | `dataease.io/docs/v2/`（可由后端覆盖） | 帮助文档 |
| `src/layout/components/TopDoc.vue` | 25 | `bbs.fit2cloud.com/c/de/6` | 社区论坛 |
| `src/layout/components/TopDoc.vue` | 30 | `blog.fit2cloud.com/categories/dataease` | 官方博客 |
| `src/layout/components/TopDoc.vue` | 35 | `jinshuju.net/f/TK5TTd` | 企业版试用申请 |
| `src/views/about/index.vue` | 58 | `support.fit2cloud.com` | 技术支持 |
| `src/locales/zh-CN.ts` | 2265 | `dataease.io/docs/...` | Excel 错误帮助链接 |
| `src/custom-component/rich-text/plugins/vertical-content.ts` | 93 | `dataease.io` | Tinymce 插件元信息（非链接） |

---

## 7. 遗漏外部请求的排查方法

如果发现 Network 面板中有未知的外部请求，按以下步骤排查：

```bash
# 1. 搜索硬编码的外部域名
grep -rn "https\?://" src --include="*.ts" --include="*.vue" --include="*.js" \
  | grep -v "localhost\|192.168\|\.svg"

# 2. 搜索 iframe 嵌入
grep -rn "<iframe\|:src.*http" src --include="*.vue"

# 3. 搜索直接 fetch/axios 调用（不经过标准 request 封装）
grep -rn "fetch(\|axios(" src --include="*.ts" --include="*.vue" \
  | grep -v "from '@/config/axios'"

# 4. 搜索动态脚本加载
grep -rn "new Function\|eval(\|createElement.*script" src --include="*.ts" --include="*.vue"
```

---

> 最后更新: 2026-08-01
