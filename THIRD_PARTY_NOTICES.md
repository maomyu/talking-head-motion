# Third-party components and scope

The root MIT license covers this project's original workflow, adaptation code
and documentation. Bundled third-party works keep their own notices and terms.

## Huashu Art Motion

- Source: https://github.com/alchaincyf/huashu-art-motion
- Pinned commit: `9ff59339f934e08483ba0a5b1db20f4c2c421b35`
- Copyright (c) 2026 alchaincyf (花叔 · 花生).
- Code/documentation license: MIT, preserved without edits in
  `assets/huashu-engine/LICENSE` and `assets/huashu-full/LICENSE`.
- Included: clip engine; complete scene engine; 35 art scenes and recipe cards;
  8 parameterized renderers; 9 explainer method cards; generic motion/paint/media
  libraries; storyboard lint, QA and film delivery tools.
- The complete-engine HTML excludes the optional author-specific character rig.
  Adaptations, included file hashes and excluded resources are recorded in
  `assets/huashu-full/upstream.json`.
- Local portrait material factories and corrections are documented in
  `assets/style-batch/provenance.json`; the topic-specific paper scene example
  has its own provenance under `assets/examples/paper-explainer/`.
- Excluded: author-specific character images, sprite assets and vector likeness,
  showcase movies/images, demo/reference films, audio, account configurations,
  credentials, Git histories and caches. Historical demo paths in method cards
  refer to the upstream project, not files shipped here.

## Fonts — SIL Open Font License 1.1

Bundled fonts are NOT covered by the root MIT license. Copyright, source and
font-specific details remain in both original `LICENSES.md` files; complete OFL
texts remain alongside them:

- `assets/huashu-engine/lib/fonts/LICENSES.md` and `OFL.txt`
- `assets/huashu-full/scripts/engine/lib/fonts/LICENSES.md` and `OFL.txt`

Respect font-specific Reserved Font Names when modifying fonts. Do not sell
font files by themselves or remove the retained notices.

## Hanzi stroke medians — Arphic Public License

The sample-character stroke data in
`assets/huashu-full/third_party/hanzi-strokes/strokes.js` retains its upstream
license: `ARPHICPL.TXT` in that directory. It is a limited character subset,
not a complete handwriting database, and is not relicensed under MIT.

## Installable runtime dependencies

HyperFrames and GSAP are installed from the pinned
`assets/runtime/package-lock.json`. Their distributions and transitive
dependencies keep their respective license notices after installation.
`node_modules` is not redistributed in the source repository or release ZIP.
Python dependencies listed in `requirements.txt` are likewise installed
separately and retain their own licenses.

## Research-only references

Editorial/reference research consulted Hypit, Talkcraft, xilo-opus-video,
SeeCut, video-replica-studio and make-awesome-video. Their code, demonstration
media and credentials are not incorporated into this skill's runtime.
Attribution does not assert a common license or affiliation.

The Douyin source catalog records public work URLs, authors and selected motion
observations. Its 28 adaptation modules are independently authored; the 30 source
videos, original faces, audio, software UI, downloads and API responses are not
distributed. Source media retain their authors' rights and are not covered by
this repository's MIT license. Local study previews use separately authorized
illustrative presenter assets; they do not demonstrate the user's avatar or
relicense the original footage.
