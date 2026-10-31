# 第三方大屏嵌入说明

> 最后更新: 2026-08-18

---

## 结论

前端**已支持**把第三方大屏（或任意网页）嵌入到本系统大屏 / 仪表板中进行管理。

做法：在编辑器中插入 **「网页」** 组件（`DeFrame`），在右侧属性里填写第三方 URL。组件内部用 `<iframe>` 渲染，可调整位置、大小、图层，随大屏一起保存和预览。

---

## 使用方式

1. 打开大屏或仪表板编辑
2. 左侧组件 **「更多」→「网页」**，拖到画布
3. 选中组件，右侧 **链接信息** 中填写地址
4. 保存后预览 / 发布即可看到嵌入内容

编辑态会盖一层遮罩，提示「编辑状态不可操作网页内部」，避免误点进 iframe；预览、发布后才是完整交互。

---

## 两种嵌入模式

右侧「链接信息」由 `FrameLinks` 配置，数据结构：

```ts
{
  src: '',      // 网页 URL，或嵌入模式下的代码
  isApp: false  // false = 网页地址；true = 嵌入模式
}
```

| 模式 | 开关 | 填什么 | 渲染方式 |
|------|------|--------|----------|
| **网页地址**（默认） | `isApp = false` | 第三方大屏 URL，如 `https://xxx/screen` | `<iframe src="...">` |
| **嵌入模式** | 勾选「嵌入模式」`isApp = true` | 嵌入代码 / JS | `<iframe srcdoc="...">`，独立隔离 |

网页地址在失焦时会自动补全 `http://`（`checkAddHttp`）。嵌入模式不做 HTTP 补全，内容原样写入 `srcdoc`。

---

## 限制

- **对方站点必须允许被嵌。** 若目标页设置了 `X-Frame-Options` 或 CSP `frame-ancestors`，浏览器会拦截。界面提示：「部分网站可能设置不允许嵌入而无法显示」。
- 这是把第三方页面当作画布上的一块区域管理（位置、大小、图层），**不会**把对方图表拆成本系统内组件。
- 编辑态无法操作 iframe 内部；截图时也会盖一层 mask，避免 iframe 内容干扰截图。

---

## 入口位置

| 场景 | 组件分组 | 文件 |
|------|----------|------|
| 数据大屏 | 「更多」→「网页」 | `src/custom-component/component-group/MoreComGroup.vue` |
| 仪表板 | 「更多」→「网页」 | `src/custom-component/component-group/DbMoreComGroup.vue` |

组件注册名：`DeFrame`，展示名：`visualization.web`（中文「网页」）。

---

## 关键文件

| 文件 | 说明 |
|------|------|
| `src/custom-component/de-frame/ComponentFrame.vue` | 网页模式：`<iframe :src="frameLinks.src">` |
| `src/custom-component/de-frame/ComponentAppFrame.vue` | 嵌入模式：`srcdoc` iframe，代码隔离执行 |
| `src/custom-component/de-frame/FrameLinks.vue` | 右侧「网页地址 / 嵌入代码」表单 |
| `src/custom-component/de-frame/Attr.vue` | 属性面板，挂载链接信息折叠项 |
| `src/custom-component/component-list.ts` | 组件定义与 `FRAMELINKS` 默认值 |
| `src/utils/components.ts` | 注册 `DeFrame` / `DeFrameAttr` |

---

## 渲染逻辑摘要

**网页模式**（`ComponentFrame.vue`）：

- `frameLinks.src` 有值 → 渲染 iframe
- 无值 → 占位文案「请配置网页信息..」
- 地址变更时通过 `frameLinksChange-{id}` 事件销毁并重建 iframe

**嵌入模式**（`ComponentAppFrame.vue`）：

- 将 `src` 包进独立 HTML（含 `<script>`）写入 `srcdoc`
- 每个组件一个隔离 iframe；删除组件即销毁，互不影响
