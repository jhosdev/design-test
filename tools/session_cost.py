#!/usr/bin/env python3
"""Estimate API cost, wall time and turns for Claude Code transcripts.

Usage:
  python3 tools/session_cost.py <transcript.jsonl> [...]
  python3 tools/session_cost.py --dir ~/.claude/projects/<proj>/<session>/subagents

Transcripts live in ~/.claude/projects/<project>/<session-id>.jsonl
(subagents under <session-id>/subagents/agent-*.jsonl).
Costs are list-price estimates; subscription plans are billed differently.

Caveat: transcripts record usage from the *start* of each streamed message, so
input/cache numbers are exact but output_tokens is not. Output is estimated from
the content written (~3.5 chars/token) plus hidden thinking, sized from the
encrypted thinking signature (~5.3 chars/token). Treat cost as +/-25%.
"""
import glob, json, os, sys
from datetime import datetime

# $ per million tokens: input, output, cache read (Anthropic API list prices, 2026-09)
PRICES = {
    "claude-fable-5-1":  (10.0, 50.0, 0.25),
    "claude-opus-5-5":   (4.0, 20.0, 0.20),
    "claude-sonnet-5-5": (2.0, 10.0, 0.20),
    "claude-haiku-4-5":  (1.0, 5.0, 0.10),
}
CACHE_5M, CACHE_1H = 1.25, 2.0  # cache-write multipliers on input price


def price_for(model):
    for key, p in PRICES.items():
        if model and model.startswith(key):
            return p
    return None


def analyze(path):
    msgs, out_est, first, last, tool_uses = {}, {}, None, None, 0
    for line in open(path):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        ts = d.get("timestamp")
        if ts:
            t = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            first = first or t
            last = t
        if d.get("type") != "assistant":
            continue
        m = d.get("message", {})
        key = m.get("id") or id(d)
        if m.get("usage"):
            msgs[key] = (m.get("model"), m["usage"])  # entries of one message share usage
        for c in m.get("content") or []:
            if not isinstance(c, dict):
                continue
            if c.get("type") == "thinking":
                est = len(c.get("thinking", "")) / 3.5 or len(c.get("signature", "")) / 5.3
            elif c.get("type") == "text":
                est = len(c.get("text", "")) / 3.5
            elif c.get("type") == "tool_use":
                est = len(json.dumps(c.get("input", {}))) / 3.5
            else:
                est = 0
            out_est[key] = out_est.get(key, 0) + est
        tool_uses += sum(1 for c in m.get("content") or [] if isinstance(c, dict) and c.get("type") == "tool_use")

    cost, tok = 0.0, {"in": 0, "out": 0, "cache_read": 0, "cache_write": 0}
    models = set()
    for key, (model, u) in msgs.items():
        u = dict(u, output_tokens=max(u.get("output_tokens", 0), int(out_est.get(key, 0))))
        models.add(model)
        p = price_for(model)
        cc = u.get("cache_creation") or {}
        w5 = cc.get("ephemeral_5m_input_tokens", u.get("cache_creation_input_tokens", 0) if not cc else 0)
        w1 = cc.get("ephemeral_1h_input_tokens", 0)
        tok["in"] += u.get("input_tokens", 0)
        tok["out"] += u.get("output_tokens", 0)
        tok["cache_read"] += u.get("cache_read_input_tokens", 0)
        tok["cache_write"] += w5 + w1
        if p:
            pin, pout, pread = p
            cost += (u.get("input_tokens", 0) * pin + u.get("output_tokens", 0) * pout
                     + u.get("cache_read_input_tokens", 0) * pread
                     + w5 * pin * CACHE_5M + w1 * pin * CACHE_1H) / 1e6
    minutes = (last - first).total_seconds() / 60 if first else 0
    return {"file": os.path.basename(path), "models": sorted(m for m in models if m),
            "cost_usd": round(cost, 2), "minutes": round(minutes, 1),
            "turns": len(msgs), "tool_calls": tool_uses, "tokens": tok}


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["--dir"]:
        args = sorted(glob.glob(os.path.join(os.path.expanduser(args[1]), "*.jsonl")))
    print(json.dumps([analyze(p) for p in args], indent=2))
