---
name: talking-head-motion
description: 完整网感口播制作流程：自拍原视频保留原声粗剪、抖音参考学习、30条来源对应28个动画与版式模块、语义分镜、人物反复出镜、花叔35艺术配方与8种语法、词轴同步、本地MP4、对话审核与当前Codex审片。用于真人或数字人口播、参考重建与可复用动画制作。
---

# 网感口播完整制作

把参考中的剪辑表达和动效迁移到新口播，交付本机完整 MP4、字幕和可重跑工程。Agent 负责理解、选材、编排、特殊效果重建与审片；脚本负责确定性制作、缓存、检查和渲染。学习规则不等于模型微调，代码集成不等于每条能力都已实测。

用户说“做出来”“开始做”即继续实施。沿用已确认的画幅、人物、风格、归属和授权，不反复询问。缺信息时先做无依赖部分。只有文案、尚无本人形象/音色时，可以交付有明确标签的样片，并将数字人阶段标为待接入。

## 先选择路线，再执行完整流程

阅读 [production-workflow.md](references/production-workflow.md) 的阶段表和 [editorial-playbook.md](references/editorial-playbook.md) 的视觉决策。建立 `brief.json`；首次学习参考再建 `style-pack.json`，模板在 `assets/templates/`。所有任务使用独立项目目录，未知归属使用通用项目。

## 画风展示与对话选择

- 网页负责展示可播放的不同画风、名称和编号，供用户观看比较；画风选择由用户在对话中告诉 Agent，不设置网页确认、填写或记录入口。
- 先检查本轮对话和本项目已确认的画风。用户已指定时直接沿用，用户的新指令覆盖旧选择；不再要求看网页、重新选择或重复确认。用户明确让 Agent 自选时，按内容推荐并说明采用哪款。
- 制作正式单版而用户尚未指定画风时，先展示或复用画风页面，再在对话中提醒：“画风已展示在网页，这条口播请告诉我用哪一款，名称或网页编号都可以。”可以结合内容简短推荐，但推荐不等于用户已经选择；不擅自锁定画风后渲染正式版。
- 选择待补充期间继续查看原片、整理文案、转写和准备素材等不依赖画风的工作。提醒后给用户回复机会，不反复追问；用户只要求展示时先完成展示，要求多款或全部画风时按该范围制作。
- 复用已验证、可播放的画风库或既有对照片，不因每次选择重新渲染35条完整视频。缺少所需预览时制作明确标注的代表片段；只有明确要求完整对照才按完整时长制作。
- 记录到 `brief.json` 的 `art_direction`：画风名称、实际配方ID和用户选择来源。用户说“第几款”时按当前网页的序号解析，不把网页序号当文件前缀或配方ID。艺术画风与8种动画语法分别处理：画风按用户选择，具体动画语法由 Agent 按句意安排，除非用户另有指定。

## Route by the available input

- Reference only: analyze its narrative and selected effects, write a style pack, rebuild important effects, then verify replacement content. Do not claim an arbitrary-video inverse-effects algorithm.
- Existing talking-head video: read [自拍原视频流程](references/raw-talking-head.md); keep its native picture and audio together. Tighten actual sentences if requested, accept the resulting A/V master, transcribe its final audio, make a semantic shotbook and render. Do not regenerate the person's voice or replace the footage with an avatar by default.
- Script only: establish project ownership, presenter and voice. Use available company voice/digital-human skills when applicable, then consume the accepted master. Read [provider-handoff.md](references/provider-handoff.md). Without a presenter, label a motion-only example as an example.
- Explicit API route: read [native-api-setup.md](references/native-api-setup.md); use the included Fish native adapter and an actually configured digital-human API. Keep provider billing, credentials and generated media separate from the distributable skill.
- No assets: find accessible references from primary sources, preserve URLs and distinguish documented examples from proven viral videos. Keep reference media in projects, separate from distributable skill assets.

Read [project-contract.md](references/project-contract.md) for schemas/commands, [reference-reconstruction.md](references/reference-reconstruction.md) for visual reconstruction, and [quality-review.md](references/quality-review.md) for acceptance. For artistically rendered B-roll, use the learned [Huashu integration](references/huashu-integration.md). When the user asks for 花叔完整风格、丰富场景、艺术动画 or complains about simple text cards, use [完整花叔制作](references/huashu-full-production.md): create content-specific scenes and actual object actions with the complete engine. Keep one art direction throughout each film. When the user requests 35画风口播、每种画风一条完整视频 or full-film style comparisons, read [完整画风对照](references/style-batch.md) and produce the requested number of complete talking-head films with the same accepted content, timing and presenter returns.

用户要求查看不同风格或增加人物出镜时，阅读 [presenter-led-styles.md](references/presenter-led-styles.md)。使用同一段已确认配音做风格对照，并把人物多次回到主画面写进分镜；不要用一次露脸加全片动效代替口播主线。

用户要求搜索抖音口播剪辑、下载前N条、增加语法或提取参考动画时，使用 [抖音参考学习与模块](references/douyin-grammars.md) 和 [28模块目录](assets/social-grammars/catalog.json)。先记录实际搜索顺序，再逐条查看完整时长概览与选定密集窗口，制作实际编码的复刻/复用对照片。教程界面、静态构图、生成式变脸与剪辑运动必须区分；重复案例归并，不能用30来源冒充30新语法。新增模块通过`broll-jobs.json`的`renderer:social`接入完整出片，整屏动画使用`position:full`。动态人物抠像尚未接入时明确限制，不用一张静态人像替代移动真人。用户说“由用户指定”表示保留画风选择权，并未指定具体画风。

用户要求真实拍摄视频复刻、原片完整逐帧分析、原配色/语法精确一致，或指出四秒机制样片不细致时，必须改用 [原生逐帧重建](references/native-frame-reconstruction.md)。保留完整原片并实际遍历每帧原生 PTS；连续审阅所有重要动画帧，测量真实动作而非猜 easing。人物使用动态视频/每帧 alpha，按原生窗口时长重建，分别验证颜色、字形、轨迹、遮罩、层序与转场。网页增加同步原速和前后逐帧对照，审核仍在对话。未经逐项对照不得标“百分百”；素材、字体或被遮挡区域无法恢复时公开具体差异，不能重放原成片冒充逆向重建。

## 最短可执行入口

先用 `motion.py init PROJECT --video MASTER` 接受现成口播，或 `--audio NARRATION` 创建音频演示。完成参考学习、词轴/字幕复核与分镜后：

`<skill>` 表示此技能的安装目录，执行时替换为绝对路径。

```bash
python3 <skill>/scripts/produce.py /absolute/project --model small --expected-script script.txt
```

该命令续跑转写（需要时）、缓存的花叔片段、组件编译、浏览器审计、MP4 渲染及完整解码检查。语义分镜由 Agent 写，不用固定每隔几秒插卡片代替理解。命令成功停在待实片审阅；运行日志、缓存、次数和输出 hash 全部保存在工程。

## Production loop

1. Work in a named project directory. Run `python3 scripts/motion.py doctor`. The pinned runtime is under `assets/runtime`; install dependencies there if missing. No global CLI install is needed.
2. Analyze references and view contact sheets/dense transition frames. Record observed motion and semantic purpose; scene detection and similarity scores do not understand either.
3. Reconstruct parameterized effects. Prove reuse with two different text lengths/assets. Source-frame replay is not reusable effect reconstruction. Adapt unfamiliar effects in project-local HTML/JS and document parameters instead of mapping everything to fades.
4. Use `init`, prepare final word timestamps, and author `shotbook.json`. Anchor meaningful events to words, not old reference seconds. Bind evidence to actual assets. Missing assets must fail rather than become empty successful shots.
5. Build, run HyperFrames gates, render a representative preview, then the accepted full duration. Register one paused, seekable timeline under the composition ID. Render assets are local. Protect speaker and subtitle readability. `render` automatically runs the full browser `check` gate; archive its warnings and diagnose their actual effect rather than claiming zero findings.
6. Run `check` on the exported MP4, then continue reviewing with the current Codex agent. Read actual encoded frames, dense transition windows, final narration transcripts and local audio measurements; record timecoded findings and verification limits. Do not stop at mechanical success or ask for another model account. The default reviewer is the current conversation's model; Gemini is optional only if the user requests additional remote review. Read [quality-review.md](references/quality-review.md).
7. Fix timecoded problems and re-render, bounded by the project review limit (default 3). Cache accepted generation outputs/task IDs. On exhaustion, return a pending-review preview and unresolved issues.
8. Match the requested review unit: each animation shot means a playable narrated shot; each art style as a talking-head video means one complete film per requested style. Give full-film timecodes, actual encoded posters and mechanisms in a local review page. Use `scripts/review_gallery.py` and `scripts/serve_review.py` for shot review, or [style-batch.md](references/style-batch.md) for complete-film comparisons. A three-second art preview does not satisfy a request for complete talking-head videos.

## Invariants

- Transcribe the accepted final narration. If a digital-human generator retimes guide audio, preserve its native A/V pair; never substitute old guide audio/timestamps.
- A-roll is the presenter; B-roll supports the message. Style rules do not prove model fine-tuning or viral performance.
- 默认由对话驱动审核：网页只提供播放、切换、同时间对照、镜头跳转和下载。选定画风、修改意见和确认通过都在对话中处理，由 Agent 关联实际视频版本保存；不添加意见表单、打分、记录时间、保存或导出意见入口。
- With available presenter footage, default to recurrent presenter-led editing: return to the face for the opening, key assertions, emotional turns and closing; use PiP where it supports explanation. Inspect actual face crop and return blocks. A labelled stock layout demo does not establish lip-sync or the user's identity.
- Preserve source media. Stage a seekable copy. Match canvas/fps to the brief; larger export dimensions cannot restore missing detail.
- Follow existing ownership/archive rules. Unknown media is not assigned to a client automatically.
- Identical-content replicas can use image differences; new words/faces/assets require motion/layout/semantic review rather than an arbitrary whole-frame SSIM target.
- 花叔整片：镜头表 lint 先行，一镜 2–6 秒，物体动作贯穿，文字主导镜头 ≤30%，参数化语法最多两种；复杂表达写自定义 scenes。按原规则跑实际 MP4 gate、逐镜 QA 和独立审片，不能用指标通过替代风格判断。既定风格和已有角色继续制作；全新角色/画风选择依原标准准备可审阅的构图。

Return MP4, subtitles, project path, verification evidence and material limitations. External publication requires a user request. The deliverable is the rendered video.

## 交付说明必须分层

- 已实测：列出当前 MP4、帧率/尺寸/时长、字幕来源、实看范围和复用测试。
- 已接入待实测：新的动画语法、具体数字人提供方或远程质检必须明确其验证程度。
- 待用户材料：本人人物/音色、正式内容、归属及需要的真实证据；不要把这些当成能从网上随意替代的本人素材。

用户审核重点是成片的节奏、读字、人物、证据和参考对应，而非代码细节。样片只有功能验证通过时照实说；不要称它为完整本人数字人口播或成熟爆款复刻。
