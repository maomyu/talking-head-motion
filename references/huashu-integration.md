# Huashu animation integration

User-selected source: [alchaincyf/huashu-art-motion](https://github.com/alchaincyf/huashu-art-motion). The original `assets/huashu-engine` contains eight parameterized clip renderers and remains unchanged for existing pipelines. The additional `assets/huashu-full` contains the full scene/camera/drawing/transition engine, 35 art scenes and recipes, nine grammar cards and the original lint/QA/delivery workflow. Each directory has pinned provenance in `upstream.json`. Author character artwork, private configuration and demo media are excluded. Preserve MIT, font OFL and the hanzi-strokes Arphic Public License separately. Read [huashu-full-production.md](huashu-full-production.md) for substantive animation or whole-film requests.

Learned principles: an effect expresses a concrete event; hold → brief movement → hold is often better for narration than constant drift. Use real evidence as the main picture when available, with code for annotations/camera movement. Maintain one palette/style and vary composition. Choose animation grammar by the actual statement, not by decorative abundance.

| Grammar | Good narration use |
|---|---|
| `y3_whiteboard` | A relationship, process or causal chain drawn on one board |
| `y2_vox` | Documents/screenshots with annotations and information collage |
| `y5_kinetic_type` | A short important term or contrast |
| `t3_finance_chart` | Actual numerical comparisons, axes before data |
| `t1_3b1b` | Geometric/quantitative transformations |
| `t2_keynote_ui` | Product/interface explanation |
| `y1_kurzgesagt` | Illustrative spatial/scientific explanation |
| `y4_storytime` | Narrative reaction using supplied authorized character assets |

Read the corresponding bundled [grammar card index](huashu-grammar-cards/index.md) when designing an unfamiliar grammar. The cards preserve upstream context; full-film/demo paths in them refer to the original repository, not bundled assets. `y6_presenter_explainer`, the ninth card, is a full scene route requiring actual authorized presenter assets, not another parameterized renderer. Keep capability coverage separate from verification of a particular new film.

`python3 scripts/render_huashu.py PROJECT --spec broll.json --out broll/process.mp4` renders a local silent clip. The spec needs `grammar`, `duration` (<=8 seconds), `fps`, `width`, `height`, a shared `theme` and ordered `cues`. For full themes use `bg,surface,ink,sub,accent,accent2`. Optional `timeline_start` maps the segment into the master. A cue can specify `anchor` instead of `at`; the wrapper resolves it from accepted final words into local time. Add the MP4 as a `broll` event in the main shotbook, without replacing narration.

The upstream measurements/gates concern its animation films. Use them for diagnosing B-roll motion, not as universal pass/fail thresholds for readable talking-head footage. Do not promise pixel-exact arbitrary effect recovery. Inferred quality must be validated on the actual encoded output; use independent review for substantive Huashu-derived animation delivery as requested by its workflow.
