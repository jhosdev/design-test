# Motion Model Bench

The same motion-graphics prompts, run on different Claude models as Claude Code subagents, with cost and time for each run. Inspired by Charlie Hills' Opus 5.5 motion test.

**Gallery:** open `index.html`. Once GitHub Pages is on, it's at `https://jhosdev.github.io/design-test/`.

## How it works
- Each run is one self-contained `effect.html`: 1920×1080, fonts embedded as base64, no external requests.
- Every page exposes `window.seek(seconds)` and `window.DURATION`. A frame is a pure function of time, and any randomness uses a seeded PRNG, never `Math.random`.
- Rendering: headless Chromium (Playwright) seeks frame by frame at 30 fps, and `ffmpeg` encodes the screenshots to H.264 (`effect.mp4`).
- [HyperFrames](https://github.com/heygen-com/hyperframes) packages the same pipeline: a GSAP timeline, a seek adapter, parallel Chrome workers and a Claude Code plugin. It also works in this container.

## Layout
```
runs/<model>/<test>/effect.html | effect.mp4 | poster.png
runs/results.json          cost / minutes / turns per run
tools/session_cost.py      cost estimate from ~/.claude/projects/**/*.jsonl transcripts
tools/build_gallery.py     regenerates index.html
```

## Results (list-price estimates)
| Test | Opus 5.5 | Sonnet 5.5 |
|---|---|---|
| 1 Showreel | $1.57 · 14.2 min | $0.50 · 7.0 min |
| 2 Explainer | $2.51 · 31.8 min* | $0.74 · 8.2 min |
| 3 Chart | $1.12 · 6.9 min | $0.58 · 4.6 min |
| 4 App | $1.52 · 8.2 min | $0.66 · 6.5 min |

\*Includes about 23 minutes of MP4 rendering (1 fps PNG capture).

The costs come from Claude Code transcripts. Input and cache token counts are exact. Output tokens are estimated, because transcripts record usage when a message starts streaming, so treat each cost as roughly ±25%.

## Adding a model
1. Run the prompts in `tools/build_gallery.py` with a subagent on the new model, writing to `runs/<model>/<test>/`.
2. Add its transcript numbers to `runs/results.json`.
3. Run `python3 tools/build_gallery.py`.

## Cloud environment
`env/setup.sh` is a setup script for Claude Code cloud environments. Paste it into the environment's settings under **Setup script**. It takes about 25 seconds, and the environment cache keeps the result. It installs fnm, cloudflared, wrangler, hyperframes, a Playwright version that matches the preinstalled Chromium, serve, ruff and httpie. Node, bun, uv, Python, Rust, Go, Docker, ffmpeg and gh come with the base image.
