# Reference reconstruction

Inspect the whole narrative before local effects: hook, argument, evidence, pacing, A-roll/B-roll changes and caption system. Separate persistent layers from cuts. `analyze` produces metadata, cut candidates, sparse frames and contact sheets; it does not identify original source code or invent a verified style pack.

For fast effects use a dense window: `analyze reference.mp4 --out analysis/fast --start 4 --end 6 --every 0.1`.

Write project-local `style-pack.json`: source/timecodes, semantic trigger, layout, palette, typography, path/scale, easing, enter/hold/exit duration, layering, assets, component ID/parameters, limitations and verification state. New narration changes event timings.

Rebuild a useful 2–5 second segment first, compare equivalent content, then replace with short/long Chinese text and a different asset. Inspect encoded results. Original-frame playback proves replay fidelity rather than reusable reconstruction.

Candidate references: [video-replica-studio](https://github.com/taotao135791-bit/video-replica-studio), [make-awesome-video](https://github.com/NewTurn2017/make-awesome-video), and [Huashu](https://github.com/alchaincyf/huashu-art-motion). Initial bundled components are independently authored. Retain actual licenses/notices when importing code. Hypit uses a separate runtime and modified Apache license. SeeCut/Talkcraft have noncommercial restrictions and are not vendored as commercial core.

Until a reference has been viewed and matched effects tested, the included preset is a development style, not a learned replica.
