# AutoDL Art H3 图音母片

仅在用户选择 MiniMax H3／AutoDL 时读取。本路线使用 AutoDL Art 托管工作流，不是 MiniMax 官方接口，也不是租用 GPU 实例。本包未内置账户密钥；接口准备完成、拿到任务ID、生成成功、实际母片通过检查是不同状态。

2026-10-14从[工作流页面](https://www.autodl.art/large-model/comfyui/minimax_h3_image_audio_to_video_v2_15s)及[官方API说明](https://autodl.art/docs/comfyui_api/)核对：

- POST `/api/v1/comfyui/comfyui_workflow/minimax_h3_image_audio_to_video_v2_15s`；GET `/api/v1/comfyui/comfyui_workflow/result/{task_id}`，主机 `https://www.autodl.art`。
- 生成与结果查询使用分组为 `ComfyUI` 的 API 令牌：`Authorization: <api_token>`，无 Bearer 前缀；请求参数在顶层。不要把官网网页登录凭据与 API 令牌混用。
- `prompt` 必填，`duration` 为1–15整数秒，`resolution` 可选 `480p竖/768p竖/480p横/768p横`，`seed` 可选整数。`ref_image_0` 和 `ref_audio_0` 支持图片／音频 URL 或对应文件 Data URL。提示词使用 `<Picture 1>`、`<Audio 1>`。
- 凭据留在用户私密位置；项目只记凭据引用。输出 CDN 下载不携带 API Authorization，先保存 `.part`、完整解码后再正式归档。未知结果保留，禁止盲目再次 POST；已有ID只续查。

每段共用同一张已核对的正面形象，按音频真实停顿拆分，每段不超过接口时长。固定摄影机、人物尺度、服装和背景，要求连续自然发音、完整头肩、无新增人物／字幕／音乐；只讲当前锁定文稿。不得用上段变形尾帧继续生成。先生成一段代表片，检查原始输出的内容、身份、构图及嘴部连续帧，再生成剩余段；生成失败只重做对应段，计入已确认预算。

价格按当前工作流核对，不把官方 MiniMax 报价带入本路线。2026-10-14已结合官方工作流报价与用户明确授权的只读费用核验，确认本工作流计费基数为**生成视频秒数**：768p高峰价格为0.040元／生成视频秒。按该价格估算，15秒为0.60元，两段各15秒共1.20元；30款本地剪辑共用一份母片，无需调用数字人服务30次。这些是当日参数对应的计算示例，不是对新任务实际扣费的承诺；重试、其他分辨率、时段价格及平台舍入以当前报价和实际费用为准，预算保留余量。

`result.data.duration`在API文档中是处理耗时，网页日志另列排队／推理耗时；这些值都不能乘上述单价当作生成费用。保存 `currency=CNY`、`billing_basis=generated_video_seconds`、核价时间、分辨率／时段、预计费和实际费，提交前比较累计费用与用户预算。已验证的基数可复用，不要求每个任务重新翻旧账；单价可能变动时核对当前工作流。未知结果保留任务ID，先续查，避免重复计费。

需要查费用时优先使用已登录官网的[调用日志](https://www.autodl.art/large-model/call-logs)，只读取用户授权的任务范围。公开前端的控制台 `GET /api/v1/comfyui/workflow/tasks` 使用网页登录会话中的 token，直接放在 `Authorization`，同样不加 Bearer；它与生成／结果查询所选的 ComfyUI API 令牌来自不同认证流程。API 令牌请求控制台账单若返回“认证失败／登录失败”，不要盲改前缀或遍历猜测接口。当前公开契约未明确 API 令牌的独立单任务费用接口；结果查询接口也不能假设一定返回费用字段。官网会话失效时由用户在官网恢复登录，不提取或输出其会话令牌。

读取其他项目或历史账单不是生成任务自动扩展的授权。核价证据留在私密项目，只在可公开文档记录服务规则与计算方法；账户令牌、任务明细、账号信息和私人账目不随技能开源。不要以预计费用冒充已实际扣费。

指导音轨来自 Fish 不代表 H3 会原样保留。下载后比较实际语音内容和词时间：在一视频帧内匹配才可确认 `passthrough` 并沿用 Fish 母带；若改停顿或词轴，记 `retimed_native`，保留原生音画对，按实际音轨重新转写。暂不能判定时保留原生对并注明未知。不要覆盖为旧配音、拼成错位口型，或裁到目标秒数截断发音。

H3原生768p进入1080×1920剪辑可使图形与字幕更清楚，不代表人物恢复为原生1080p／2K。保留供应商原片、每段实际帧数／PTS、指导音轨、原生音轨、任务ID、输入SHA、接受／拒绝原因，再把接受的母片交给同一剪辑主线。既有完整母片直接复用，不重新调用服务。

## 公共适配器

[`scripts/autodl_h3_api.py`](../scripts/autodl_h3_api.py) 使用独立私密项目，提供 `prepare`、`submit`、`resume`。准备与本地缓存检查不读取凭据；只有真实 API 请求才读取明确指定的 AutoDL 凭据。已通过22项离线检查，包括真实 CLI 准备、本地合成音视频完整解码和模拟状态／传输。2026-10-14，公共适配器实际 GET 续查既有任务至成功、下载完整原生音画，通过FFmpeg全解码／ffprobe帧数探测、原片SHA与任务绑定收据核对；实际代表片的视觉和语音内容通过后，同一公共适配器 POST 新段落成功，保存了可信任务ID与预算占用。已有任务没有再次POST，旧状态、缓存身份、代表片接受和预算链路均有实际验证。该范围证明接口与状态衔接可用，不代表所有人像质量或30款成片已通过；仍按每个实际母片及最终编码分别审查。此前私密程序的提交不混作公共适配器测试。

Agent 维护下列项目元数据，用户仍在对话里提供选择和审核。例子中的素材、哈希和报价占位符需由实际项目替换；不要将私人项目文件一起提交到开源仓库。

`config/h3-provider.json`：

```json
{
  "base_url": "https://www.autodl.art",
  "workflow_id": "minimax_h3_image_audio_to_video_v2_15s",
  "resolution": "768p竖",
  "conservative_total_cap_cny": 40,
  "api_key_env": "AUTODL_ART_API_KEY"
}
```

只配置一种凭据来源：显式环境变量名 `api_key_env`、私密 `credentials_file`，或显式 `keychain: {"service": "AutoDL-Art", "account": "指定账户"}`。私密文件仅包含 `base_url`、`token`，Unix 权限为0600或0400；不放进仓库。不会使用 Fish 默认密钥或从网页提取登录会话。API 主机仅接受上述两个官方 HTTPS 域名。

`generation/segments.json`：

```json
{
  "portrait": "assets/presenter.png",
  "presenter_description": "依据实际已查看人像描述其形象、服装和背景。",
  "presenter_review": {"status": "accepted", "portrait_sha256": "实际已审图片SHA256"},
  "preflight_id": "seg01",
  "segments": [
    {
      "id": "seg01",
      "guide_audio": "audio/seg01.wav",
      "text": "本段已锁定对白。",
      "generation_seconds": 15,
      "seed": 42
    },
    {
      "id": "seg02",
      "guide_audio": "audio/seg02.wav",
      "text": "第二段已锁定对白。",
      "generation_seconds": 15,
      "seed": 43
    }
  ]
}
```

`preflight_id` 指定代表片，优先于旧兼容字段 `representative_segment`；都未设置时取第一段。每段可用 `portrait` 覆盖顶层图片路径，也可提供完整 `prompt`；自定义提示词须保留精确的锁定对白，宜用独立引号隔开摄影机要求和对白。默认提示词以简短英文要求沿用 `<Picture 1>` 的人物与构图、保留完整头肩、固定人物大小、连续单镜头及零摄影机运动／变焦／切镜，采用 `<Audio 1>` 的声音与时间；中文台词单独标为 `SPOKEN DIALOGUE ONLY` 并加引号。`presenter_description` 可省略，提供时明确标为不发声的视觉描述，不预设性别、服装或中近景。这种台词与动作要求隔离是降低歧义的制作选择，不能据此断言先前失败或识别出的异常词句由提示词造成。显式 `row.prompt` 保留原样，不改已有项目请求。指导音频必须是可读 WAV，时长大于0且不超过本段整数生成秒数。

`config/autodl-billing-evidence.json` 先记录未核实状态：

```json
{
  "workflow_id": "minimax_h3_image_audio_to_video_v2_15s",
  "verified": false,
  "currency": "CNY",
  "billing_basis": "generated_video_seconds",
  "resolution": "768p竖",
  "unit_price_cny": null,
  "checked_at": null
}
```

实际核价后，Agent 填入已确认的正数单价、时间和 `verified=true`；适配器不会把模板视为可提交的报价。分辨率须与请求相同；也兼容旧证据中的 `request_parameters_inspected.resolution`。项目中所有历史尝试与未知提交均占预算，不因从当前段落列表移除而消失。API 未说明单位的 `fee/cost/amount` 不自动当作人民币实际费；实际扣费与预计费分开记录。

从技能目录运行：

```bash
python3 scripts/autodl_h3_api.py prepare seg01 --project /absolute/private-project
python3 scripts/autodl_h3_api.py submit seg01 --project /absolute/private-project
python3 scripts/autodl_h3_api.py resume seg01 --project /absolute/private-project
```

也可显式传入项目内的 `--config`、`--plan`、`--billing` 相对路径。`prepare` 不联网、不付费，保存含 Data URL 的 `request.json` 和 `input-manifest.json`；再次准备相同输入保留原字节。`submit` 才是付费动作，须在用户已授权的预算内执行。已有任务状态时禁止重做准备，已有ID仅续查；API 响应不确定或没有可信ID会保留 `SUBMISSION_UNCERTAIN` 与预算占用，禁止自动再次提交。不要删除未知状态来绕过此保护。

代表片下载后由当前 Agent 实看片、听音和核对锁定对白，再写该段的 `quality-acceptance.json`。必须有 `status=accepted`、`raw_output_sha256`（兼容 `output_sha256`）、`portrait_sha256` 和 `guide_audio_sha256`，全部绑定真实文件；推荐同时记录 `request_sha256`、检查时间、语音与视觉证据及残差。适配器不自动生成接受记录，也不以文件存在代替接受。其余段使用相同已接受图片，并在代表片通过后才可提交。

所有提示词、图片、音频、生成秒数、分辨率和种子保持冻结；配置变化会阻止续查。新尝试使用新段落ID和目录，保留旧输入、原片与拒绝原因。迁移已提交任务时，保持原请求、状态和输入SHA；若旧程序采用不同默认提示词，先把其既有精确提示词显式固定到该段 `prompt`，不能重写原请求。兼容原 `task-state.json` 字段与 `DOWNLOADED` 的 `output_sha256`，不要求为既有合格哈希缓存补造下载收据。

输出 CDN 请求不带 Authorization，只允许 HTTPS且拒绝重定向；若供应商改成跳转下载，需要重新核对下载契约。新下载有任务／输入绑定收据，完整 FFmpeg 解码和帧数探测通过后归档。缓存每次复用检查SHA与完整解码；未知旧文件不会按名称被认领。可写输出拒绝符号链接和硬链接，下载临时文件用排他创建。项目锁防止两个进程重复预留／提交；中断遗留锁仅在确认进程停止并核对状态后处理。

有限离线回归：

```bash
python3 -m unittest discover -s tests -p test_autodl_h3_api.py -v
```

测试使用临时合成素材、模拟响应与虚构凭据，覆盖输入冻结、既有任务GET、预算、未知提交、代表片接受、缓存身份、下载认证隔离和文件别名；有 FFmpeg 时另检验真实合成音视频解码。没有调用私人账户、生产媒体或实际付费接口。
