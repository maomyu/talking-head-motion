# 花叔完整场景能力：从画面事件到整片

本模式用于用户明确要求按花叔的方法制作复杂动画、艺术画风、新题材场景，或认为参数化文字面板太简单时。它补齐完整场景引擎；已有 `assets/huashu-engine` 和 `render_huashu.py` 仍负责最多 8 秒的参数化 B-roll，保持原字节和旧缓存。

## 实际包含与边界

新增资源位于 `assets/huashu-full`，原仓库 commit、逐文件源指纹、修改和排除项见其中 `upstream.json`。包含 **35 个艺术场景、35 张配方、9 张解说语法卡、8 个参数化 renderer**，以及绘画/笔触/材质、相机、对象变形、拼贴、媒体、转场、整片场景引擎和原镜头表 lint/QA/film gate/deliver。

- **35 画风是材料与绘画机制，不是 35 种可无限套用的模板。** 原场景都画过同一个横屏房间；只用于能力预览、回归和学习笔法。做口播要按实际题材重写物和构图，不能把房间场景拿来填时长。原场景依然存在各配方中披露的短板，不应承诺全都达到艺术家原作水平。
- **第 9 张 `y6_presenter_explainer` 是讲解员场景路线，不是第 9 个 `--spec` 语法。** 需要项目自有、获准的人物帧库、姿态/脚底锚点及换帧动作。仅有帧表元数据不算可渲染或已实现。原作者人物图、花叔角色专用矢量骨架、示范片、帧库、配音与私人配置均未迁入。
- MIT 声明和字体 OFL 保持原文。`third_party/hanzi-strokes` 是原笔顺中线字符子集及 **Arphic Public License**，不是完整汉字数据库；不可把该数据错误标为 MIT。
- 原方法卡保留出处和历史示范路径；`demos/`、`reference_films/` 和其图/音频不在新包中。这些路径只能到原仓库学习，不能当作本地文件已存在。视频、图片、声音由主口播流程管理，本入口不接供应商、不生成新配音。

按需阅读：

| 任务 | 对应原方法 |
|---|---|
| 从参考提取运动机制 | [拆解](../assets/huashu-full/references/01-拆解.md)、[机制](../assets/huashu-full/references/02-机制.md) |
| 决定材料、构图与一帧 | [一帧先行](../assets/huashu-full/references/03-一帧先行四条路线.md)、[35 配方总表](../assets/huashu-full/references/风格配方/INDEX.md) |
| 绘画、世界画布与相机 | [纯代码绘制](../assets/huashu-full/references/04-纯代码绘制.md)、[风格作者接口](../assets/huashu-full/references/08-风格作者规范.md) |
| 口播词锚与全片 | [口播驱动](../assets/huashu-full/references/06-口播驱动的艺术短片.md)、[整片与经验回流](../assets/huashu-full/references/12-口播整片与经验回流.md) |
| 角色或讲解员 | [角色精细度](../assets/huashu-full/references/角色精细度.md)、[角色合成](../assets/huashu-full/references/10-角色.md)、[讲解员卡](../assets/huashu-full/references/动画语法/y6_presenter_explainer.md) |
| 新分镜及反 PPT 检查 | [镜头表](../assets/huashu-full/references/镜头表模板.md)、[色板](../assets/huashu-full/references/色板.md)、[原制作标准](../assets/huashu-full/source-SKILL.md) |

## 按花叔标准制作当前题材

先保留已定稿口播及实际时间轴，把每句话转成**可见的物和动作**。锁一套画风/色板；每镜 2–6 秒、相邻镜头换构图、文字主导镜头不超过 30%，开头与收尾落在物或人的动作上。原 lint 的参数化语法上限为 2 种，复杂表达用同一画风的自定义 scenes，而非堆更多模板。

例：口播“拍完又熬夜剪”，设计手机录像保存→素材散落到时间轴→字幕轨道不断挤满→时钟加速→回到人物反应；不是把五个短句轮流淡入一个固定面板。人物出现和 PiP 遵循本技能的口播规则，不为满足动画运动占比移除必要的人物表达。

运动应有事件：停→0.28 秒快推约 18–32%→停，或约 0.30 秒横移，或约 0.17 秒砸入（1.55→0.94→1）。可用 `CAM.track`、`MO.slam`；艺术场景为主动作加按材料变化的母题循环，不能全员呼吸与缓慢漂移替代动作。截图/录像/照片实际存在时以真实素材满幅呈现，由代码解释、标注和运镜。人物采用项目提供的真实母片或新获准帧库；不代码画人脸、不搬作者角色。

反 PPT 六项对照原标准：固定页框/列表翻页；照搬示范物件构图；只有抽象字/图标；空底只有中心小动；实际有素材却重画；颜色和画风无依据地混搭。自动 gate 只能发现运动、空帧和颜色等一部分问题，不能代替实际审片。

用户已经授权当前方向时继续完成，不把原文“三方向先挑”重新解释成每次必须停下来审批。若确有全新角色/画风选择且会改变成片，应先做可审阅的具体构图。

## 可执行入口

依赖：Python ≥3.9、ffmpeg/ffprobe、Playwright Chromium；QA 另需 numpy/Pillow。使用当前环境已安装的解释器；缺依赖时按实际环境安装。`uv run --with playwright --with numpy --with pillow python …` 也可作为隔离入口，首次 Chromium 未安装用 Playwright 官方安装命令。

下面把 `<skill>` 与 `<项目>` 换成真实路径。`init` 只创建新目录，不覆盖旧工程；产生一段实际可渲染的“纸质素材落入电脑时间轴”起步场景，**不算主题成片**。然后用镜头表改 `eras.js` 与 `scenes/*.js`。

```sh
python3 <skill>/scripts/huashu_full.py catalog
python3 <skill>/scripts/huashu_full.py breakdown --video <参考视频> --out <项目>/拆解
python3 <skill>/scripts/huashu_full.py init <项目>/代码工程 --width 1080 --height 1920
python3 <skill>/scripts/huashu_full.py lint <项目>/镜头表.md --script <项目>/文稿.txt
python3 <skill>/scripts/huashu_full.py render <项目>/代码工程 --solo project_intro --from 0 --to 3 --fps 24 --no-counter --out <项目>/镜01.mp4
python3 <skill>/scripts/huashu_full.py render <项目>/代码工程 --solo project_intro --stills 0.5,2 --no-counter --out <项目>/静帧/镜01
python3 <skill>/scripts/huashu_full.py render <项目>/代码工程 --fps 24 --out <项目>/动画轨.mp4
python3 <skill>/scripts/huashu_full.py qa <项目>/代码工程 --ids project_intro --out <项目>/qa/镜01
```

自定义场景接口为 `SCENES[id] = { init(IMG)?, draw(c, local_time, global_time) }`，在 `eras.js` 以 `{id,dur,transition?}` 登记。显式登记素材到 `assets`/`EXTRA_ASSETS`；使用项目内有来源记录的图片或逐帧母片，不让远程 URL 进入确定性渲染。复制后的工程属于项目，可组合 `lib/paint.js`、`brush.js`、`render.js`、`post.js`、`media.js`、`camera.js` 等。缺场景、转场、字形、素材的 pageerror/boot failure 不能忽略。

新写过的完整纸本口播例子在 [paper-explainer](../assets/examples/paper-explainer/README.md)：手机吐底片、字幕擦改、照片翻找、动效尺、剪片、实物叠放、累计白板与合卷。它提供实际复杂场景代码，须按新内容重写事件和构图；图库循环不能搬进真人原声母片。

原 35 场景仅按 1920×1080 排过，能力审核用原横屏坐标；**不能把画布直接缩到竖屏造成裁切**。新竖屏 scenes 按 `window.STAGE.W/H` 或库接口重新构图。每个原画风能力预览命令如下，`09_postimp` 可换成 catalog 中任一个 ID：

```sh
python3 <skill>/scripts/huashu_full.py render bundled --film gallery --solo 09_postimp --from 0 --to 3 --fps 24 --no-counter --out <审核目录>/09_postimp.mp4
```

入口记录日志、引擎源指纹、实际 MP4 SHA-256、ffprobe 帧/尺寸/FPS/时长，并完整解码；记录不等于画面审阅。它不改变原 renderer 的字节，也不改已有口播音轨。先渲动画轨再由主流程按实际口播时间混音，禁止 `-shortest` 悄悄截断原口播。

## 验收与验证范围

镜头表 lint 无红灯后再制作；每个动画段跑原 QA，并查看实际编码后的多时刻与切点。原 QA 输出动感/确定性/取景线索，浅底无字幕动画可加 `subzone_gate.py`；纹理底不适用。独立 agent 审看完整成片并写入项目 `审片/` 后再交付；按原整片经验规则，长片至少两位未参与制作的审片人。修复后复验真实新输出并绑定新 hash，旧报告只留作历史。

纯动画轨使用原 `film_gate.py` / `deliver.py` 的红灯规则：快速运动帧占比低于 0.035、成片中段连续超过 0.3 秒的空画面、非题材要求蓝紫底超过 30%。实际 `film_gate.py` 对短于 20 秒的片段（默认 `FILM_GATE_MIN_S=20`）会把快动红灯降为黄灯提示，空画面等事实硬伤仍拦；不能把短样例黄灯误报为整片已过。以上是该引擎的制作门禁，**不是所有口播主画面的通用留存标准**。混合口播须分别报告动画轨门禁与最终人物/字幕/声音检查，不靠大量字幕或真实人像绕过动画问题。

```sh
python3 <skill>/scripts/huashu_full.py deliver <项目>/成片.mp4 --root <项目> --qa <项目>/qa/重点镜头 --out <项目>/output
python3 <skill>/assets/huashu-full/scripts/deliver.py --verify <项目>/output/交付说明.md
```

最终交付包含每个动画镜头 MP4、完整稿、可播放审核索引、所选画风与机制、原始与最终声音一致性、媒体许可、实际编码帧检查及独立审片。只有静帧/引擎启动验证时必须明确写“未做完整新题材成片验收”；原能力预览过解码也不等于新口播完成。

## 可重跑的逐镜审核页

项目中保存 `storyboard.json`（fps、shots 的 id/start/end/object/action/camera/presenter、captions 的 start/end/text；格式见纸本例子的 story-example.json）。最终 MP4 合格后运行：

```sh
python3 <skill>/scripts/review_gallery.py --project <项目> --film <项目>/output/成片.mp4
python3 <skill>/scripts/serve_review.py --dir <项目>/审核页面 --port 49709
```

如要额外显示原画风能力预览，传 `--styles /absolute/35画风审核manifest.json`（previews 中的 video/poster 为真实本地路径）。无此参数只显示当前稿的分镜。视频不随技能包分发。`--reuse` 只沿用母片指纹、边界、片段指纹均一致的既有视频；否则重新导出并完整解码。首次导出逐镜可能从句中开始，必须结合完整稿审核。网页仅用于播放、浏览分镜和下载；用户通过对话提出意见，由 Agent 关联实际视频 hash记录，新版重新核对。不要生成意见输入、保存或导出记录入口。服务只绑定本机回环地址；由 Agent 打开并保留审核标签页。
