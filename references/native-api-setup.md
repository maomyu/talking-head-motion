# Native API production

Use this route when the user requests API integration. Website subscription credits, OAuth/MCP credits and developer API billing are separate. Do not route an explicit API request back to a paid website download flow.

## Fish narration

Official endpoint: `POST https://api.fish.audio/v1/tts`. Set the `model` header to an exact supported name. As checked on 2026-10-11, `s2.1-pro-free` is free; `s2.1-pro` costs $15 per million UTF-8 input bytes. An omitted or unrecognized model falls back to paid `s2.1-pro`; the adapter rejects this condition and never silently upgrades.

Use a provider-authorized preset `reference_id`, or route voice cloning to an appropriate voice-profile workflow. A preset does not require a fabricated reference-audio sample. Keep the exact narration, request parameters, provider-original WAV, a 48 kHz mono copy, duration and hashes. Generation success leaves listening and content review pending.

Store credentials in an environment variable or an explicitly approved OS secret store. Profile files contain identifiers only:

```json
{
  "provider": "fish-audio-native-api",
  "model": "s2.1-pro-free",
  "reference_id": "5d29a99739c14d4ca3e4fe42193105b2",
  "speed": 1.0,
  "api_key_env": "FISH_API_KEY",
  "keychain": {
    "service": "codex.talking-head-motion.fish-audio",
    "account": "default"
  }
}
```

Plan without credentials or network:

```bash
python3 scripts/fish_api.py plan --profile PROJECT/config/fish-api-profile.json --text PROJECT/script.txt --output PROJECT/review/api-plan
```

After service access is authorized, synthesize the formal opening for delivery checks, then the full accepted text. A short opening is part of the formal script; do not rewrite the user's publication into a test announcement.

```bash
python3 scripts/fish_api.py generate --profile PROJECT/config/fish-api-profile.json --text PROJECT/script.txt --output PROJECT/audio/full-v1 --submit
```

Paid models additionally require an adequate explicit `--allow-paid --max-usd` budget. The budget is per new request; the Agent also tracks the production's total. The adapter caches complete matching outputs and refuses automatic resubmission of uncertain/failed requests. HTTP errors do not authorize upgrading the model. For a deliberate new attempt, first review the prior state, record the reason and budget, then use a new output directory.

On macOS, `secret_store.py set --service ... --account ...` reads a hidden terminal prompt; `--stdin` supports a trusted local secret handoff. It never accepts a secret in an argument or prints it. Key creation/storage consent follows the active tools' policy; this reference does not add a second universal approval gate.

## Digital-human API handoff

Choose the provider from actual account access, quality needs, cost and supported duration. Do not assume Fish's website avatar menu is a documented Fish REST endpoint. Record the documented API and quote separately from narration.

When MiniMax is selected, use its documented H3 V2 API rather than assuming a ComfyUI workflow is mandatory. `POST https://api.minimax.io/v2/video_generation` uses a `content` array and returns a persistent task ID. For a preset portrait plus narration, use the reference route: `text` + `image_url` with `role=reference_image` + `audio_url` with `role=reference_audio`. The official API forbids mixing any reference role with `first_frame`/`last_frame`. Each reference audio is 2–15 seconds, total reference audio ≤15 seconds; H3 output is integer 4–15 seconds, at 768P or 2K. Check region/account access and current pricing first. As checked on 2026-10-11, H3 output is $0.08/sec at 768P or $0.13/sec at 2K; reference video adds input-duration charges. H3 Max is a different fast variant and must not be substituted silently.

Reference audio is not proof of unchanged output speech or exact lipsync. Generate one representative segment, keep its native A/V pair and check words, duration, identity and continuous mouth frames. Record passthrough versus retimed/generated audio; do not overwrite an altered native soundtrack with the old Fish narration. An available SDK/API schema is not a tested account connection.

If the user prioritizes narration and editing before the avatar, finish a full narration/motion edit and record avatar generation as deferred. Reusable online talking-person footage can serve as reference or B-roll with source/license records; its original mouth movements do not match a newly synthesized script. Do not imply the stock person is the user or endorses their product, and do not treat a silent stock clip as a spoken mother clip.

An economical documented option is Alibaba Cloud `wan2.2-s2v`: Beijing account/key and workspace ID; one frontal image plus clean audio; 480P/720P; audio **strictly shorter than 20 seconds** per call. As checked on 2026-10-11, prices are ¥0.5/second and ¥0.9/second respectively. Free quota depends on the actual account and expiry. A 1080×1920 final export does not restore detail absent from a 720P mother clip.

Split the accepted full audio at natural pauses under 20 seconds, preserve sample-aligned segment boundaries and total duration. Confirm segmentation and budget before paid submission. Save every task ID immediately; poll it instead of submitting again. Download successful outputs before their 24-hour links expire. Inspect a representative real segment before continuing the batch, then verify face consistency and mouth continuity across boundaries. The digital-human provider connector must be available and tested before claiming this phase is connected.

Alibaba's documented upload adapter supplies account/model-bound `oss://` temporary resources, which require `X-DashScope-OssResourceResolve: enable`. They expire after 48 hours and are suitable for a bounded local generation run, not a durable deployed product; deployed production uses a stable storage configuration. Never expose local files through an improvised public tunnel. Do not log temporary upload signatures, API keys or signed download URLs into a distributed skill.

Feed the accepted native A/V pair to the local editing pipeline, transcribe its final audio and continue the normal shotbook/render/Codex review loop. Do not claim full-video completion after TTS.

Official sources:

- [Fish TTS](https://docs.fish.audio/api-reference/endpoint/openapi-v1/text-to-speech)
- [Fish prices](https://docs.fish.audio/developer-guide/models-pricing/pricing-and-rate-limits)
- [Wan speech-to-video API and prices](https://help.aliyun.com/zh/model-studio/wan-s2v-api)
- [Alibaba temporary upload resources](https://help.aliyun.com/zh/model-studio/get-temporary-file-url)
- [MiniMax H3 V2 API](https://platform.minimax.io/docs/api-reference/video-generation-v2-create)
- [MiniMax prices](https://platform.minimax.io/docs/pricing/overview)
