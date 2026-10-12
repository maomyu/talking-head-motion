# 完整生产、续跑与交付

| 阶段 | Agent 行为 | 文件/能力 | 进入下一阶段的条件 |
|---|---|---|---|
| 输入 | 沿用已知偏好，补充主题、归属、人物、参考 | `brief.json` | 信息不足的部分列为假设/未知 |
| 画风 | 网页展示可用画风；对话已指定就沿用，未指定时展示后提醒选择 | 画风页、`brief.json.art_direction` | 正式单版按用户选择或其明确自选授权制作；等待时继续不依赖画风的工作 |
| 参考 | 叙事拆解、密集运动窗口、效果重建 | `analysis/`、`style-pack.json` | 已查看参考；复用测试有编码视频 |
| 内容 | 论点、证据、读法，定稿后再生成 | `script.txt`、素材来源 | 不伪造事实/证据 |
| 人声 | 现成视频原音，或适用工作室的声音流程 | `generation-ledger.json` | 输出可播放，保存任务 ID 与授权音色 |
| 数字人 | 使用授权形象和已配置的生成服务 | 原始母片 + 提供方记录 | 新形象先查代表短段；保留 native A/V |
| 精剪 | 现有精剪 skill 或逐段同切音视频 | `accepted-master.mp4` | 无截断字音和不自然跳切 |
| 对齐 | 转写最终母片，复核同音错字 | `words.json`、字幕 cue | 真实时间戳；重新生成会使旧对齐失效 |
| 编排 | 人物/证据/动效选择，绑定语义词 | `shotbook.json`、`broll-jobs.json` | 每镜表达清楚，素材存在 |
| 动画 | 本地组件、花叔片段、自写特殊效果 | `broll/`、`public/` | 内容可替换，时长/布局通过 |
| 渲染 | 确定时间线，HyperFrames 浏览器检查后编码 | `output.mp4`、`render.json` | 本地完整 MP4，无错误假成功 |
| 质检 | 完整解码 + 当前 Codex 审编码帧/内容 | `mechanical-review.json`、`codex-review.json` 或审片记录 | 默认不需外部模型；当前输出的证据通过，旧 hash 无效 |
| 交付 | MP4、字幕、工程、局限、复用经验 | `subtitles.srt`、风格包更新 | 发布另按用户要求执行 |

## 可重跑的命令

准备好已接受的母片、语义分镜和词轴后：

`<skill>` 表示此技能的安装目录，执行时替换为绝对路径。

```bash
python3 <skill>/scripts/produce.py /absolute/project --model small --expected-script script.txt
```

它执行可缺省的转写、列在 `broll-jobs.json` 中的花叔片段或抖音机制模块、build、浏览器检查、渲染、完整编码检查，并保存阶段日志、B-roll 缓存和渲染历史。默认 `renderer:huashu`，新增模块用 `renderer:social`；整屏镜头用 `position:full`，随后回到人物。选择与限制见 [抖音参考学习](douyin-grammars.md)。它不会凭空写稿、选证据或冒充审片；这些是上表中 Agent 的工作。状态成功停在 `needs_editorial_review`，当前 Codex 接着查看编码帧、内容和本地音频检查，按时间码修复；不要求用户另配 Gemini。ASR 推断仍需文字复核；有已校正词轴/已验证字幕 cue 时复用它们。

`production-run.json` 记录失败阶段和日志。错误后修输入、再次执行同命令；相同 spec/词轴的 B-roll 和相同内容的完整输出复用。音频变化时旧转写不能续用。默认 `review_limit:3` 约束这里的成片渲染尝试；特殊新范围可说明理由后修改项目额度。单个 `motion.py render` 是底层调试命令，不代替生产循环的次数管理。

本地核心无需声音/数字人 API；这两步按 `provider-handoff.md` 接现有能力。只给文案又没有人物配置时，继续做布局/风格预览，将母片阶段标为待接入。费用上限、模型和上传权限来自项目 brief；没有配置时不盲发付费任务。

## 本机安装与可迁移

运行 `motion.py doctor`。必要工具：Python 3、Node、FFmpeg/ffprobe、Chrome/Chromium。渲染 runtime 在 `assets/runtime/package-lock.json` 固定；在该目录 `npm ci --ignore-scripts --no-audit --no-fund` 可重建，避免依赖全局命令。转写另需 faster-whisper，抽帧联系表需 Pillow，花叔 renderer 需 Python Playwright 和可启动 Chromium。首次 ASR 模型下载需要网络。

软件版本、字体和原始许可证随工程/skill 记录。八种语法的实现已集成，不等于八种均实测通过；使用新语法时按它的语法卡制作代表短片并审片。开发验证报告和样片保存在工作区，不把它们当作用户素材。

Python 可选依赖的本机验证版本在 `requirements.txt`；其他机器先建虚拟环境，再安装需要的依赖。Playwright 若没有浏览器，使用该环境的 `python -m playwright install chromium`。本机已存在运行环境时不要重复下载。核心渲染依赖、ASR 模型和付费提供方是不同的依赖，分别检查。
