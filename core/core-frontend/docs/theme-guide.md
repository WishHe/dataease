# 主题色配置说明

> 最后更新: 2026-08-01

---

## 当前配置

| 项目 | 值 |
|------|-----|
| **主色** | `#2a8b92`（青绿色） |
| **应用范围** | 社区版 / 企业版均可 |
| **覆盖方式** | CSS 变量 + 数据库配置 |
| **修改文件** | `src/style/index.less` |

---

## 主题系统架构

### 核心机制

DataEase 使用 **CSS 自定义属性（CSS Variables）** 控制主题色，变量名以 `--ed-` 为前缀（Element Plus Secondary）。

```
┌─────────────────────────────────────────────────┐
│                  CSS 层                          │
│  src/style/index.less  :root:root {             │
│    --ed-color-primary: #2a8b92 !important;      │
│    --ed-color-primary-light-3: #4a9ca2;         │
│    --ed-color-primary_b50: #eaf3f4;             │
│    ... 等 10 个衍生色                             │
│  }                                               │
├─────────────────────────────────────────────────┤
│                  JS 层                           │
│  src/store/modules/appearance.ts                 │
│  从 /sysParameter/ui 读取外观配置                 │
│  企业版: themeColor='custom' → 动态计算衍生色     │
│  社区版: community=true → 使用 CSS 默认值         │
├─────────────────────────────────────────────────┤
│                  数据库层                         │
│  core_sys_setting 表                             │
│  pkey='themeColor'  pval='custom'               │
│  pkey='customColor'  pval='#2a8b92'             │
│  (仅企业版后端读取)                               │
└─────────────────────────────────────────────────┘
```

### 关键文件

| 文件 | 说明 |
|------|------|
| `src/style/index.less` | CSS 变量定义（含主色 + 10 个衍生色） |
| `src/store/modules/appearance.ts` | 外观 Store，控制主题加载逻辑 |
| `src/utils/color.ts` | `getCSSVariable()` 工具函数 |
| `src/style/variable.less` | Less 变量（侧栏、画布等专用色） |

### 当前主色及衍生色

主色 `#2a8b92`（rgb: 42, 139, 146）的衍生色通过 Less 的 `mix()` 函数计算：

| CSS 变量 | 颜色值 | 计算方式 | 用途 |
|----------|--------|----------|------|
| `--ed-color-primary` | `#2a8b92` | 主色 | 按钮、链接、图标、激活态 |
| `--ed-color-primary-light-3` | `#4a9ca2` | 15% 白 | 浅色变体 |
| `--ed-color-primary-light-5` | `#7fb9be` | 40% 白 | 浅色变体 |
| `--ed-color-primary-light-7` | `#d2f1e9` | 70% 白 | 极浅背景 |
| `--ed-color-primary_b50` | `#eaf3f4` | 90% 白 | hover 背景、选中背景 |
| `--ed-color-primary-dark-2` | `#24767c` | 15% 黑 | 深色变体 |
| `--ed-color-primary-dark-20` | `#226f75` | 20% 黑 | 按钮 active 态 |
| `--ed-color-primary-1a` | `#2a8b921a` | 10% 透明度 | 悬浮态背景 |
| `--ed-color-primary-33` | `#2a8b9233` | 20% 透明度 | active 态背景 |
| `--ed-color-primary-99` | `#2a8b9299` | 60% 透明度 | 禁用态 |
| `--van-blue` | `#2a8b92` | 同主色 | 移动端 Vant 组件 |

---

## 如何切换主题色

### 方式 A：CSS 覆盖（社区版 / 开发环境）

修改 `src/style/index.less` 中 `:root:root` 块内的 `--ed-color-primary` 及相关变量。

衍生色计算公式（Less `mix()` 函数）：

```
light-3  → mix(#ffffff, 主色, value=15)  // 15% 白
light-5  → mix(#ffffff, 主色, value=40)  // 40% 白
light-7  → mix(#ffffff, 主色, value=70)  // 70% 白
_b50     → mix(#ffffff, 主色, value=90)  // 90% 白
dark-2   → mix(#000000, 主色, value=15)  // 15% 黑
dark-20  → mix(#000000, 主色, value=20)  // 20% 黑
1a       → 主色 + '1a'                    // 10% 透明度
33       → 主色 + '33'                    // 20% 透明度
99       → 主色 + '99'                    // 60% 透明度
```

### 方式 B：数据库配置（企业版 / 生产环境）

在 `core_sys_setting` 表中插入：

```sql
INSERT INTO core_sys_setting (id, pkey, pval, type, sort)
VALUES
  (..., 'themeColor', 'custom', 'text', 50),
  (..., 'customColor', '#YOUR_COLOR', 'text', 51);
```

后端 `/sysParameter/ui` 接口返回后，`appearance.ts` 会自动计算全部 10 个衍生色。

### 方式 C：后端管理界面

企业版（XPack）提供可视化外观配置页面，可直接在 UI 中设置主题色、Logo 等，无需手动操作数据库。

---

## 社区版 vs 企业版差异

| 功能 | 社区版 | 企业版 |
|------|--------|--------|
| CSS 变量覆盖 | ✅ 支持 | ✅ 支持 |
| 数据库 themeColor | ❌ 不读取 | ✅ 读取 |
| UI 配置页面 | ❌ 无 | ✅ 有 |
| 全局外观设置（Logo等） | ❌ 无 | ✅ 有 |

---

## 其他外观相关设置

`appearance.ts` 中还管理以下外观配置（均需企业版后端支持）：

| 字段 | 说明 |
|------|------|
| `navigate` | 导航栏 Logo 图片 |
| `navigateBg` | 导航栏背景色（light/dark） |
| `login` / `bg` / `web` | 登录页背景 / 全局背景 / 网站图标 |
| `slogan` / `showSlogan` | 登录页标语 |
| `showDoc` / `showAi` / `showAbout` | 显示/隐藏文档、AI、关于按钮 |
| `help` | 自定义帮助文档 URL |
| `name` | 系统标题（`document.title`） |
