# Project contract and commands

The script resolves the skill location itself; use absolute project/media paths. Project-relative asset paths resolve against the project.

`brief.json.art_direction` records the user's artistic style selection as `name`, `recipe_id` and `selection_source` (the relevant conversation instruction). It is Agent-managed production metadata, separate from the core `project.json.style` colour palette. Resolve a spoken gallery number using that page's actual `data.json` before saving the recipe ID; missing selection triggers the reminder in SKILL.md.

`<skill>` 表示此技能的安装目录，执行时替换为绝对路径。

```bash
python3 <skill>/scripts/motion.py doctor
python3 <skill>/scripts/motion.py init /absolute/project --video /absolute/master.mp4
python3 <skill>/scripts/motion.py analyze /absolute/reference.mp4 --out /absolute/project/analysis --every 0.5
python3 <skill>/scripts/motion.py transcribe /absolute/project --model small --language zh
python3 <skill>/scripts/motion.py build /absolute/project
python3 <skill>/scripts/motion.py render /absolute/project
python3 <skill>/scripts/motion.py check /absolute/project
```

`transcribe` uses installed faster-whisper on CPU and can download its model on first use. It writes real timestamps, never uniform guessed times. Accepted timestamps can instead be imported into `words.json`: `[{"text":"关键", "start":0.2, "end":0.5}]`. Verified sentence cues may be provided as `caption-cues.json`: `[{"text":"一句话", "start":0, "end":2}]`. Check imported timing against final audio. A project without audio is explicitly motion-only.

Prefer reviewed natural clauses in `caption-cues.json` over automatic character-count cuts for formal Chinese narration. Keep words together, use actual first/last word timestamps, and compare caption content with the locked script. A working warm-dark layout with optional word-anchored `item_times` is provided in `assets/recipes/warm-editorial/`; its README explains local font staging and the optional project-template fields. This is a reusable layout recipe, not a generated digital-human master.

Use `--expected-script approved-script.txt` to reject gross transcript disagreement without overwriting previous accepted words. `--prompt-file` is a short vocabulary/style hint; a full repeated script in Whisper's initial prompt can cause omitted speech. Tiny/base models may produce traditional text or homophone errors; their output remains pending text review even when script agreement passes. Correct text against actual narration while preserving valid timing, or use a better model/alignment stage. Do not present ASR inference as exact phoneme synchronization.

`project.json` contains `schema_version:1`, `name`, `source:{video,audio}`, `canvas:{width,height,fps}`, `duration`, `style:{background,foreground,accent}`, `review_limit:3`, and `status`. Video and separate replacement audio together are rejected; supply an already accepted master A/V pair. Audio-only and video-only projects are supported.

For a project-specific style or choreography, optional `composition_template` and `component_code` paths select local template/JS files instead of the defaults. Keep the template placeholders and composition/media contracts. Both paths and contents enter the input fingerprint; a change requires rebuild before render. Keep locally referenced fonts/media in `public/` and preserve their project sources and licenses.

`shotbook.json` has an `events` array. Initial components:

| Component | Properties | Use |
|---|---|---|
| `kinetic-title` | `text`, optional `kicker`, `position` top/center | Masked rise and spring settle |
| `steps` | `title`, `items` (1–6), `position` | Staggered process cards |
| `quote` | `text`, optional `kicker`, `position` | One strong claim |
| `split-compare` | `title`, `left`, `right`, `position` | Two alternatives |
| `evidence` | `asset`, `title`, optional `caption`, `position` | Real screenshot with reveal and push |
| `broll` | `asset` (video), optional `title`, `position` | Locally rendered animation or real supporting clip; its audio is muted |

Events carry explicit `start`,`end` or `anchor` and positive `duration`. `anchor` is `{ "text":"关键短语", "occurrence":1, "offset":0 }`, spans adjacent ASR tokens and ignores punctuation/spaces. Missing occurrences fail. Approximate timing inside multi-character tokens needs visual checking.

```json
{"events":[
  {"id":"hook","component":"kinetic-title","anchor":{"text":"不用调时间轴"},"duration":2.3,"text":"不用调时间轴","position":"top"},
  {"id":"steps","component":"steps","start":4,"end":8,"title":"三个步骤","items":["理解参考","重建动效","编排口播"]}
]}
```

Initial events occupy one graphics lane and cannot overlap; subtitles use another lane. Simultaneous graphics or more effects can use project-local custom HTML/JS. Text wraps and receives fit checks; run actual runtime/encoded-frame checks for long text.

Video `broll` also accepts `position:"full"`: the authored clip fills the canvas directly with no extra card or entry tween. Other component types reject this position. The accepted narration continues, and captions remain above the clip. `broll-jobs.json` accepts `renderer:"social"` for [social modules](douyin-grammars.md); omitted renderer remains Huashu. Use the same master time as `presenter_video`'s `video_start` when the shot includes the moving presenter.

For accepted presenter footage, an event can use `"presenter":"pip"` to move it into a right-side small window above the caption region for that event, returning to full view afterward. Inspect the actual face crop and caption relationship; the geometry is a preset, not face detection.

Build writes `public/index.html`, staged local assets, `resolved-shotbook.json` and `subtitles.srt`. Render saves command logs and fingerprints; identical verified outputs can be reused. Changed inputs invalidate QA. Because supporting clips are silent, final rendering preserves the accepted master narration and channel layout instead of relying on the renderer's mix. Optional music/SFX mixing requires its own loudness and synchronization review. `check` validates full decode, dimensions, frame count and A/V duration, and extracts encoded samples. Mechanical success sets `rendered_needs_visual_review`, not `complete`.

Only after inspecting the delivered video, run `accept PROJECT --note "What was checked"`. It requires current passing mechanical checks and records the actual review.
