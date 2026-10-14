# Talking Head Motion · 30 Social Talking-Head Editing Styles

[简体中文](README.md) | [English](README.en.md)

**Choose an editing style and turn your recorded talking-head footage into a complete video.**

This Agent Skill centers on a fixed talking-head style library. It preserves the presenter and original voice, arranges emphasis captions, presenter windows, evidence and transitions by meaning, and exports MP4 locally. Preview styles on a read-only page; choose and revise them in the conversation.

## The core: styles you can name

Thirty reference sources have stable entries **TH-DY-01 through TH-DY-30**, each with a name and version. Multiple layouts from one source become named variants. Shared mechanisms are identified; thirty sources are not advertised as thirty unrelated original animation grammars.

A recipe fixes its palette, typography system, layout, presenter proportions, entrances, exits and transitions. Replace the script, presenter and evidence, then retime the actions to the new narration. Examples include green word tiles and comic emphasis, curved circular presenter windows, dashed cutouts and profile cards, mint three-card layouts, type behind the presenter, six-panel sequences, evidence charts and crack transitions.

[Catalogue](assets/fixed-styles/catalog.json) · [Selection and reuse](references/fixed-talking-head-styles.md) · [Native-frame protocol](references/native-frame-reconstruction.md). Reconstruction, replacement and review readiness is recorded per style; unfinished work is labeled. Original reference media and local project previews are not distributed with the repository.

The current recipe version is **0.1.0**: all thirty basic style identities are fixed. Detailed native windows and variants are added according to their actual completed scope. Basic mechanism previews and precise native-frame acceptance are recorded separately.

## Five production steps

```mermaid
flowchart LR
    A[Receive footage] --> B[Edit content and correct captions]
    B --> C[Choose a fixed editing style in chat]
    C --> D[Arrange presenter·captions·evidence·transitions]
    D --> E[Render locally and review in chat]
    E -->|Specific revisions| D
```

1. **Receive footage:** inspect the real framing, voice and content of a recording or accepted avatar master.
2. **Edit content:** cut mistakes, repeats and retakes with picture and original audio together; preserve useful pauses and correct the final master's captions.
3. **Choose a style:** reuse a confirmed choice or specify a name/ID in chat; freeze the recipe and version.
4. **Arrange the video:** use the chosen style according to meaning, keeping the presenter as the main thread and returning to them for key claims and the closing.
5. **Render and review:** deliver the complete MP4, SRT and project, inspect encoded output and synchronization, and handle feedback in chat.

Known recipes are reused directly. Each video does not require a new reference study, a full-library comparison or an art-scene pipeline. A style can be selected when footage is supplied; these are production dependencies, not a questionnaire. [Production workflow](references/production-workflow.md) · [Recorded footage](references/raw-talking-head.md) · [Editorial rules](references/editorial-playbook.md). Detailed references are currently in Chinese.

## Usage

> Use talking-head-motion to edit `/absolute/path/raw.mp4` in TH-DY-13. Preserve my original voice, return to the presenter for key claims, and export a complete 9:16 MP4.

Reuse an existing style choice. If none was supplied for a finished single-style video, the Agent shows existing previews and asks in chat while continuing independent footage/caption work. The web page offers playback, switching, frame comparison and downloads; it has no selection forms, feedback fields or ratings.

The Agent manages recipe locking internally:

```bash
python3 scripts/fixed_styles.py list
python3 scripts/fixed_styles.py bind /absolute/project --style TH-DY-13 --choice-source 'User selected TH-DY-13 in chat'
```

Once the master, final word times and shot plan are ready:

```bash
python3 scripts/produce.py /absolute/project --model small --expected-script script.txt
```

Scripts cache, compile, render and run technical checks. The current Agent then inspects the actual video. Command success does not replace semantic or visual judgment. [Project contract](references/project-contract.md).

## Optional branches

- **Create a talking-head master:** edit existing footage directly. A photo plus accepted audio goes to the provider selected by the user, without regenerating speech; script-only projects first need speech and an authorized portrait. The public package includes the Fish speech adapter and an [AutoDL H3 adapter](scripts/autodl_h3_api.py) for preparing, submitting and resuming segments. H3 passed 22 offline checks and synthetic-media decoding; a live GET resume of an existing task succeeded on 2026-10-14. Public-adapter submission and downloading remain untested live. Configure the actual account, confirm costs and review the real master before it joins the same workflow. [Configuration and scope](references/autodl-h3.md) · [Provider handoff](references/provider-handoff.md).
- **Compare all 30 editing styles:** when requested, use one presenter and one complete audio track for every version. Group previews by openings, emphasis, explanations, evidence, transitions, and endings. Choose in the conversation; the workbench only previews and downloads. [Shared-master comparison](references/fixed-style-comparison.md).
- **Learn a new style:** retain the complete reference, inspect native RGB/PTS, measure important motion, rebuild separate layers and review the encoded output. Publish a recipe version after validation; ordinary reuse does not repeat this research. [Native reconstruction](references/native-frame-reconstruction.md).
- **Artistic inserts:** 35 art palettes/material recipes and eight general animation grammars are available for special explanatory or artistic shots. They are separate optional assets, not additional mandatory style decisions for every talking-head edit. [Optional art capability](references/huashu-integration.md).

The current Codex reviews output by default; Gemini is optional. Voice generation, avatar generation and art rendering are not mandatory for editing your recording.

## Install

You need Git, Python, Node.js, FFmpeg/ffprobe and Chromium. Preserve existing local changes before updating an installed skill or using a different destination.

```bash
git clone https://github.com/maomyu/talking-head-motion.git "$HOME/.codex/skills/talking-head-motion"
cd "$HOME/.codex/skills/talking-head-motion"
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
cd assets/runtime
npm ci --ignore-scripts --no-audit --no-fund
cd ../..
python3 scripts/motion.py doctor
```

Reuse working dependencies instead of downloading them again. Node dependencies are pinned; no global HyperFrames installation is needed. Install FFmpeg/ffprobe separately. The full-resolution ledger requires a C compiler; first-time ASR model downloads need network access. Other compatible clients can use their skill directories, with review capabilities supplied by the client.

## Validation

- Stable identity, encoded windows, native timing, colour/geometry measurements and remaining differences are reported separately. See [native validation](assets/reference-engine/validation.json) and [earlier mechanism checks](assets/social-grammars/validation.json). The earlier four-second demos are not fine native reconstructions.
- All thirty originals were fully decoded: 89,080 frames. Machine traversal does not prove complete visual understanding or successful arbitrary replacement in every style. Unknown original fonts, occluded artwork and missing source projects remain explicit limitations.
- Silent stock-presenter studies establish only their tested animation/framing. Personal footage, avatar lip-sync and a user's first recording require their own review.
- Synchronization, captions, visuals, evidence and technical checks have separate scopes. Enlargement cannot restore detail; sampled frames and transcripts do not establish complete real-time listening.
- This is not an arbitrary-video inverse-effects algorithm or a guarantee of viral performance. Keep meaningful output review without turning internal production detail into user approval forms.

## Attribution and licenses

This project's maintained talking-head workflow, adaptation implementation and documentation use [MIT](LICENSE). The thirty fixed entries are built through reference study and local reconstruction; source links, shared mechanisms and validation scopes are preserved. Reference media belongs to its original creators and stays in private production projects.

The optional art engine/recipes come from [alchaincyf/huashu-art-motion](https://github.com/alchaincyf/huashu-art-motion). Original copyright, MIT license and source commit `9ff59339f934e08483ba0a5b1db20f4c2c421b35` are preserved. Fonts retain their SIL OFL 1.1 licenses and the stroke subset uses the Arphic Public License. Segmentation weights, original videos, extracted glyph artwork, credentials and generated project media are not bundled. See [third-party notices](THIRD_PARTY_NOTICES.md).

Research into Hypit, Talkcraft and other sources informed methods; their code/media is not bundled, and this project is not an official product of those authors or services.
