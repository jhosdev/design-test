#!/usr/bin/env python3
"""Build index.html: one row per test, one column per model run.

Reads runs/<model>/<test>/{effect.html,effect.mp4,poster.png} and runs/results.json
({"<model>/<test>": {"cost_usd", "minutes", "turns", "note"}}).
"""
import html, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS = os.path.join(ROOT, "runs")
TESTS = [
    ("test1-showreel", "Showreel", "Make a dynamic 15-second motion graphics video that shows what an incredible motion designer you are. Go all out."),
    ("test2-explainer", "Explainer film", "Why do we dream? Answer it as a short motion graphics film."),
    ("test3-chart", "Chart animation", "Build effect.html from scratch: a bar chart titled Weekly reach with these values: Mon: 1,200, Tue: 1,800, Wed: 1,500, Thu: 2,400, Fri: 2,100, Sat: 3,200. The bars slim down and turn into a line through their own tops, and the last value gets a tag. Never change a value. One 8-second loop with window.seek(seconds), ending where it starts. Size: 1920 x 1080. Label sample numbers as examples."),
    ("test4-app", "App animation", "Build effect.html from scratch: a small card titled Q4 launch plan grows from its own corner into a full editor window called Campaign HQ, with a sidebar, a document and status chips. The card's title travels into the window's title bar. One 8-second loop with window.seek(seconds), ending where it starts. Size: 1920 x 1080. Embed the fonts."),
]
LABELS = {"opus-5-5": "Opus 5.5", "sonnet-5-5": "Sonnet 5.5", "haiku-4-5": "Haiku 4.5", "fable-5-1": "Fable 5.1"}
ORDER = ["fable-5-1", "opus-5-5", "sonnet-5-5", "haiku-4-5"]

results = {}
if os.path.exists(os.path.join(RUNS, "results.json")):
    results = json.load(open(os.path.join(RUNS, "results.json")))
models = sorted((m for m in os.listdir(RUNS) if os.path.isdir(os.path.join(RUNS, m))),
                key=lambda m: ORDER.index(m) if m in ORDER else 99)
e = html.escape


def card(model, test):
    d = os.path.join(RUNS, model, test)
    if not os.path.exists(os.path.join(d, "effect.html")):
        return f'<article class="run empty"><span class="chip">{e(LABELS.get(model, model))}</span><p>Not run yet</p></article>'
    rel = f"runs/{model}/{test}"
    r = results.get(f"{model}/{test}", {})
    media = (f'<video src="{rel}/effect.mp4" poster="{rel}/poster.png" muted loop playsinline preload="none"></video>'
             if os.path.exists(os.path.join(d, "effect.mp4")) else f'<img src="{rel}/poster.png" alt="">')
    stats = ""
    if r:
        stats = (f'<div class="stats"><b>${r["cost_usd"]:.2f}</b><span>{r["minutes"]:.1f} min · {r["turns"]} turns</span></div>')
    note = f'<p class="note">{e(r["note"])}</p>' if r.get("note") else ""
    return f'''<article class="run">
  <a class="media" href="{rel}/effect.html" aria-label="Open live {e(LABELS.get(model, model))} version">{media}</a>
  <div class="meta"><span class="chip {model}">{e(LABELS.get(model, model))}</span>{stats}</div>{note}
  <div class="links"><a href="{rel}/effect.html">Live HTML ↗</a><a href="{rel}/effect.mp4">MP4 ↗</a></div>
</article>'''


rows = []
for i, (slug, title, prompt) in enumerate(TESTS, 1):
    cards = "\n".join(card(m, slug) for m in models)
    rows.append(f'''<section class="test">
  <header><p class="eyebrow">Test {i}</p><h2>{e(title)}</h2></header>
  <details><summary>The prompt</summary><pre>{e(prompt)}</pre></details>
  <div class="grid">{cards}</div>
</section>''')

studio_cards = ""
sp = os.path.join(ROOT, "studio", "results.json")
if os.path.exists(sp):
    for it in json.load(open(sp)):
        rel = f"studio/{it['slug']}"
        studio_cards += f'''<article class="run">
  <a class="media" href="{rel}/effect.html" aria-label="Open live {e(it['title'])}"><video src="{rel}/effect.mp4" poster="{rel}/poster.png" muted loop playsinline preload="none"></video></a>
  <div class="meta"><span class="chip opus-5-5">Opus 5.5</span><div class="stats"><b>${it['cost_usd']:.2f}</b><span>{it['minutes']:.1f} min · {it['turns']} turns</span></div></div>
  <h3>{e(it['title'])}</h3><p class="note">{e(it['note'])}</p>
  <div class="links"><a href="{rel}/effect.html">Live HTML ↗</a><a href="{rel}/effect.mp4">MP4 ↗</a></div>
</article>'''
studio_html = f'''<section class="test" id="studio">
  <header><p class="eyebrow">Studio</p><h2>AI explainers</h2></header>
  <p class="lede">Follow-ups on the benchmark: the showreel prompt plus a topic, two long explainers you can present (Space, ← →), and a direct test of plain HTML versus the HyperFrames skills on the same prompt.</p>
  <div class="grid two">{studio_cards}</div>
</section>''' if studio_cards else ""

totals = {}
for key, r in results.items():
    m = key.split("/")[0]
    t = totals.setdefault(m, [0, 0])
    t[0] += r["cost_usd"]; t[1] += r["minutes"]
total_html = " ".join(f'<span class="chip {m}">{e(LABELS.get(m, m))}</span> ${c:.2f} · {mins:.0f} min &nbsp;'
                      for m, (c, mins) in sorted(totals.items(), key=lambda x: ORDER.index(x[0]) if x[0] in ORDER else 99))

page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Motion Model Bench</title>
<style>
:root{{--bg:#070b1a;--panel:#0e1530;--line:#1f2a52;--text:#e8ecff;--muted:#8d97c2;--opus:#f0a27a;--sonnet:#9fb3ff;--haiku:#8fe3c0;--fable:#e6c46b;--link:#9fb3ff}}
@media (prefers-color-scheme: light){{:root:not([data-theme="dark"]){{--bg:#f5f7ff;--panel:#fff;--line:#dfe4f5;--text:#101633;--muted:#58607f;--link:#2f45c8}}}}
:root[data-theme="light"]{{--bg:#f5f7ff;--panel:#fff;--line:#dfe4f5;--text:#101633;--muted:#58607f;--link:#2f45c8}}
*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(1200px 500px at 50% -10%,#1b2d7a55,transparent),var(--bg);color:var(--text);font:15px/1.5 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Inter,sans-serif}}
main{{max-width:1240px;margin:0 auto;padding:48px 16px 80px}}
h1{{font-size:clamp(32px,6vw,56px);letter-spacing:-.03em;margin:0 0 8px}}h1 em{{font-style:normal;color:var(--link)}}
.lede{{color:var(--muted);max-width:760px}}.totals{{margin:18px 0 8px;color:var(--muted);font-variant-numeric:tabular-nums}}
.test{{margin-top:56px;border-top:1px solid var(--line);padding-top:28px}}.eyebrow{{font:600 12px/1 ui-monospace,monospace;letter-spacing:.18em;text-transform:uppercase;color:var(--muted);margin:0}}
h2{{margin:6px 0 10px;font-size:28px;letter-spacing:-.02em}}
details{{margin-bottom:18px}}summary{{cursor:pointer;color:var(--muted);font-size:13px}}pre{{white-space:pre-wrap;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px;font:13px/1.6 ui-monospace,monospace;color:var(--text)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:18px}}
.grid.two{{grid-template-columns:repeat(auto-fit,minmax(min(100%,460px),1fr))}}
.run{{background:var(--panel);border:1px solid var(--line);border-radius:16px;overflow:hidden;display:flex;flex-direction:column}}
.run.empty{{padding:18px;color:var(--muted);justify-content:center;min-height:160px}}
.media{{display:block;aspect-ratio:16/9;background:#000}}.media video,.media img{{width:100%;height:100%;object-fit:cover;display:block}}
.meta{{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:14px 16px 4px}}
.chip{{font:600 12px/1 ui-monospace,monospace;letter-spacing:.12em;text-transform:uppercase;padding:7px 10px;border-radius:999px;background:var(--line);color:var(--text)}}
.chip.opus-5-5{{background:var(--opus);color:#2a1206}}.chip.sonnet-5-5{{background:var(--sonnet);color:#0b1640}}.chip.haiku-4-5{{background:var(--haiku);color:#062a1c}}.chip.fable-5-1{{background:var(--fable);color:#2a2006}}
.stats{{text-align:right;font-variant-numeric:tabular-nums}}.stats b{{display:block;font-size:24px;letter-spacing:-.02em}}.stats span{{color:var(--muted);font-size:13px}}
.run h3{{margin:10px 16px 0;font-size:18px;letter-spacing:-.01em}}
.note{{margin:6px 16px 0;color:var(--muted);font-size:14px}}
.links{{display:flex;gap:16px;padding:12px 16px 16px;margin-top:auto}}.links a{{color:var(--link);text-decoration:none;font-size:14px}}.links a:hover{{text-decoration:underline}}
footer{{margin-top:64px;color:var(--muted);font-size:13px}}
</style></head><body><main>
<h1>Motion <em>Model Bench</em></h1>
<p class="lede">Same prompts, different Claude models, each run as a Claude Code subagent. Every piece is one self-contained HTML file driven by <code>window.seek(seconds)</code>; the MP4s are rendered by seeking frame-by-frame in headless Chromium and encoding with ffmpeg. Click a video for the live HTML. Hover or tap to play.</p>
<p class="totals">{total_html}</p>
{studio_html}
{"".join(rows)}
<footer>Costs are API list-price estimates computed from Claude Code transcripts by <code>tools/session_cost.py</code> (±25%: output tokens are estimated). Minutes are wall-clock and include MP4 rendering (Opus Test 2 spent ~23 of its 32 min rendering 1,335 frames). Inspired by Charlie Hills' Opus 5.5 motion graphics test.</footer>
</main>
<script>
document.querySelectorAll('.media video').forEach(v=>{{
  const play=()=>{{v.preload='auto';v.play().catch(()=>{{}})}},stop=()=>v.pause();
  v.parentElement.addEventListener('mouseenter',play);v.parentElement.addEventListener('mouseleave',stop);
  new IntersectionObserver(es=>es.forEach(x=>x.isIntersecting&&matchMedia('(hover:none)').matches?play():stop()),{{threshold:.6}}).observe(v);
}});
</script></body></html>'''
open(os.path.join(ROOT, "index.html"), "w").write(page)
print("wrote index.html with models:", models)
