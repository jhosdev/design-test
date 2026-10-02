#!/usr/bin/env python3
"""Build index.html: one row per test, one column per model run.

Reads runs/<model>/<test>/ and studio/<slug>/ folders, each holding
effect.html, effect.mp4, thumb.webp (800px) and preview.mp4 (short 640px clip),
plus runs/results.json and studio/results.json for cost/time/notes.
Cards show a lazy thumbnail, play preview.mp4 on hover, and open a modal with the
full MP4 on click.
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
ITEMS = []  # one entry per card, serialized for the modal


def media_card(rel, chip_model, chip_label, title, r, prompt, heading=False):
    i = len(ITEMS)
    ITEMS.append({"rel": rel, "model": chip_model, "label": chip_label, "title": title,
                  "cost": r.get("cost_usd"), "minutes": r.get("minutes"), "turns": r.get("turns"),
                  "note": r.get("note", ""), "prompt": prompt})
    stats = (f'<div class="stats"><b>${r["cost_usd"]:.2f}</b><span>{r["minutes"]:.1f} min · {r["turns"]} turns</span></div>'
             if r else "")
    h3 = f"<h3>{e(title)}</h3>" if heading else ""
    note = f'<p class="note">{e(r["note"])}</p>' if r.get("note") else ""
    prio = ' fetchpriority="high"' if i < 2 else ' loading="lazy"'
    return f'''<article class="run">
  <button class="media" type="button" data-i="{i}" aria-label="Play {e(title)} ({e(chip_label)})">
    <img src="{rel}/thumb.webp" alt="" width="800" height="450" decoding="async"{prio}><span class="play" aria-hidden="true">▶</span>
  </button>
  <div class="meta"><span class="chip {chip_model}">{e(chip_label)}</span>{stats}</div>{h3}{note}
  <div class="links"><button type="button" class="open" data-i="{i}">Watch</button><a href="{rel}/effect.html" target="_blank" rel="noopener">Live HTML ↗</a></div>
</article>'''


def card(model, test, title, prompt):
    d = os.path.join(RUNS, model, test)
    if not os.path.exists(os.path.join(d, "effect.html")):
        return f'<article class="run empty"><span class="chip">{e(LABELS.get(model, model))}</span><p>Not run yet</p></article>'
    return media_card(f"runs/{model}/{test}", model, LABELS.get(model, model), title,
                      results.get(f"{model}/{test}", {}), prompt)


studio_cards = ""
sp = os.path.join(ROOT, "studio", "results.json")
if os.path.exists(sp):
    for it in json.load(open(sp)):
        studio_cards += media_card(f"studio/{it['slug']}", "opus-5-5", "Opus 5.5", it["title"], it, "", heading=True)
studio_html = f'''<section class="test" id="studio">
  <header><p class="eyebrow">Studio</p><h2>AI explainers</h2></header>
  <p class="lede">Follow-ups on the benchmark: the showreel prompt plus a topic, two long explainers you can present (Space, ← →), and a direct test of plain HTML versus the HyperFrames skills on the same prompt.</p>
  <div class="grid two">{studio_cards}</div>
</section>''' if studio_cards else ""

rows = []
for i, (slug, title, prompt) in enumerate(TESTS, 1):
    cards = "\n".join(card(m, slug, title, prompt) for m in models)
    rows.append(f'''<section class="test">
  <header><p class="eyebrow">Test {i}</p><h2>{e(title)}</h2></header>
  <details><summary>The prompt</summary><pre>{e(prompt)}</pre></details>
  <div class="grid">{cards}</div>
</section>''')

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
.media{{all:unset;box-sizing:border-box;position:relative;display:block;width:100%;aspect-ratio:16/9;background:#000;cursor:pointer;overflow:hidden}}
.media img,.media video{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:block}}
.media video{{opacity:0;transition:opacity .25s}}.media.on video{{opacity:1}}
.media:focus-visible{{outline:3px solid var(--link);outline-offset:-3px}}
.play{{position:absolute;right:12px;bottom:12px;width:40px;height:40px;border-radius:50%;display:grid;place-items:center;background:#0009;color:#fff;font-size:14px;backdrop-filter:blur(6px);transition:transform .2s,opacity .2s}}
.media:hover .play{{transform:scale(1.1)}}.media.on .play{{opacity:0}}
.links button{{all:unset;cursor:pointer;color:var(--link);font-size:14px}}.links button:hover{{text-decoration:underline}}
dialog{{width:min(1200px,calc(100vw - 32px));max-height:calc(100dvh - 32px);padding:0;border:1px solid var(--line);border-radius:18px;background:var(--panel);color:var(--text);overflow:auto}}
dialog::backdrop{{background:#02040cd9;backdrop-filter:blur(4px)}}
dialog video{{display:block;width:100%;aspect-ratio:16/9;background:#000}}
.vbar{{display:flex;flex-wrap:wrap;align-items:center;gap:12px 16px;padding:14px 18px}}
.vbar h3{{margin:0;font-size:20px;flex:1 1 240px}}.vbar .stats{{text-align:left}}.vbar .stats b{{display:inline;font-size:18px;margin-right:8px}}
.vbody{{padding:0 18px 18px}}.vbody .note{{margin:0 0 10px}}
.vlinks{{display:flex;flex-wrap:wrap;gap:10px;align-items:center}}
.vlinks a,.vlinks button{{all:unset;cursor:pointer;padding:8px 12px;border-radius:10px;border:1px solid var(--line);font-size:14px}}
.vlinks a.primary{{background:var(--link);color:var(--bg);border-color:transparent;font-weight:600}}
.vlinks a:focus-visible,.vlinks button:focus-visible{{outline:2px solid var(--link)}}
.vlinks .spacer{{flex:1}}@media (max-width:560px){{.vlinks .spacer{{flex-basis:100%;height:0}}.vlinks a.primary{{flex:1;text-align:center}}}}
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
<p class="lede">Same prompts, different Claude models, each run as a Claude Code subagent. Every piece is one self-contained HTML file driven by <code>window.seek(seconds)</code>; the MP4s are rendered by seeking frame-by-frame in headless Chromium and encoding with ffmpeg. Hover a card to preview, click to watch the full render, or open the live HTML.</p>
<p class="totals">{total_html}</p>
{studio_html}
{"".join(rows)}
<footer>Costs are API list-price estimates computed from Claude Code transcripts by <code>tools/session_cost.py</code> (±25%: output tokens are estimated). Minutes are wall-clock and include MP4 rendering (Opus Test 2 spent ~23 of its 32 min rendering 1,335 frames). Inspired by Charlie Hills' Opus 5.5 motion graphics test.</footer>
</main>
<dialog id="viewer" aria-labelledby="v-title">
  <video id="v-video" controls muted loop playsinline preload="metadata"></video>
  <div class="vbar"><span class="chip" id="v-chip"></span><h3 id="v-title"></h3><div class="stats" id="v-stats"></div></div>
  <div class="vbody"><p class="note" id="v-note"></p>
    <details id="v-promptbox"><summary>The prompt</summary><pre id="v-prompt"></pre></details>
    <div class="vlinks"><a class="primary" id="v-live" target="_blank" rel="noopener">Open live HTML ↗</a><a id="v-mp4" target="_blank" rel="noopener">MP4 ↗</a>
      <span class="spacer"></span><button type="button" id="v-prev" aria-label="Previous">←</button><button type="button" id="v-next" aria-label="Next">→</button><button type="button" id="v-close">Close (Esc)</button></div>
  </div>
</dialog>
<script>
const ITEMS={json.dumps(ITEMS)};
const dlg=document.getElementById('viewer'),vid=document.getElementById('v-video'),$=id=>document.getElementById(id);
let cur=-1;
function show(i){{
  cur=(i+ITEMS.length)%ITEMS.length;const it=ITEMS[cur];
  vid.poster=it.rel+'/thumb.webp';vid.src=it.rel+'/effect.mp4';vid.play().catch(()=>{{}});
  $('v-chip').className='chip '+it.model;$('v-chip').textContent=it.label;$('v-title').textContent=it.title;
  $('v-stats').innerHTML=it.cost!=null?`<b>$${{it.cost.toFixed(2)}}</b><span>${{it.minutes.toFixed(1)}} min · ${{it.turns}} turns</span>`:'';
  $('v-note').textContent=it.note||'';$('v-prompt').textContent=it.prompt||'';$('v-promptbox').hidden=!it.prompt;
  $('v-live').href=it.rel+'/effect.html';$('v-mp4').href=it.rel+'/effect.mp4';
  if(!dlg.open){{dlg.showModal();$('v-close').focus();}}
}}
dlg.addEventListener('close',()=>{{vid.pause();vid.removeAttribute('src');vid.load();}});
dlg.addEventListener('click',ev=>{{if(ev.target===dlg)dlg.close();}});
dlg.addEventListener('keydown',ev=>{{if(ev.key==='ArrowRight'){{ev.preventDefault();show(cur+1);}}if(ev.key==='ArrowLeft'){{ev.preventDefault();show(cur-1);}}}});
$('v-prev').onclick=()=>show(cur-1);$('v-next').onclick=()=>show(cur+1);$('v-close').onclick=()=>dlg.close();
document.querySelectorAll('[data-i]').forEach(b=>b.addEventListener('click',()=>show(+b.dataset.i)));
// Hover preview: create a small looping clip only on devices that can hover.
if(matchMedia('(hover:hover)').matches)document.querySelectorAll('.media').forEach(m=>{{
  let v=null;
  m.addEventListener('pointerenter',()=>{{
    if(!v){{v=document.createElement('video');Object.assign(v,{{muted:true,loop:true,playsInline:true,preload:'auto'}});
      v.src=ITEMS[+m.dataset.i].rel+'/preview.mp4';v.addEventListener('playing',()=>m.classList.add('on'));m.appendChild(v);}}
    v.play().catch(()=>{{}});
  }});
  m.addEventListener('pointerleave',()=>{{if(v){{v.pause();m.classList.remove('on');}}}});
}});
</script></body></html>'''
open(os.path.join(ROOT, "index.html"), "w").write(page)
print("wrote index.html with models:", models)
