# 暖黑口播画面配方

从本轮真实完整口播制作回流的可参数化布局。复制 composition.html 与 components.js 到工程 edit/，在 project.json 设置 composition_template 和 component_code。将 assets/huashu-engine/lib/fonts 中 NotoSansSC-800.woff、NotoSerifSC-sub.woff 复制到工程 assets/ 及 public/assets/，它们只用于展示文字。有字幕时，`motion.py build` 另行校验／下载真实常规字幕黑体及OFL许可，缓存到工程 assets/fonts/caption 并复制到 public；字幕独立使用 THCaptionSans 的400轮廓，不继承仅800的 TalkSans。测量前确认该字幕字体实际加载，字体下载规则见 [字体与排版](../../../references/typography.md)。

使用既有 shotbook 组件契约。steps 可额外设置 item_times 为与 items 等长的绝对秒数组，来自实际词轴，以便步骤依次跟随讲话。当前固定的 stock ID 只代表有标签的支持素材，不能替代口型一致的 A-roll；不使用该素材时删去对应事件即可。

模板为 1080×1920 的版式；其他画幅需重查留白与字幕安全区域。此配方已用于 75.38 秒完整文案的制作，仍须针对每条输出的实际编码帧审查，不代表任意文字或任意参考视频都自动通过。
