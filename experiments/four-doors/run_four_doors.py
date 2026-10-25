#!/usr/bin/env python3
"""Four doors, one line, fresh hands, blind.  (burning-questions / four-doors)

    python3 run_four_doors.py --build doors.json --key key.md --line "…"   # seal the key, assemble the doors
    python3 run_four_doors.py --run runs/<stamp>                           # one-shot per door; refuses if the key changed
    python3 run_four_doors.py --blind runs/<stamp>                         # shuffle answers into blind.md; seal the mapping

doors.json — each door is a list of files that become the system prompt and a list that becomes the first
user message; "{LINE}" in a user list is replaced by the person's line, stamped the way your room stamps it:

    {"A": {"name": "base",      "system": ["base.md"],                 "user": ["{LINE}"]},
     "B": {"name": "dossier",   "system": ["base.md", "dossier.md"],   "user": ["{LINE}"]},
     "C": {"name": "carryover", "system": ["base.md"],                 "user": ["carryover.md", "{LINE}"]},
     "D": {"name": "both",      "system": ["base.md", "dossier.md"],   "user": ["carryover.md", "{LINE}"]}}

The runner below calls the Claude Code CLI one-shot with no tools and NO SESSION ON DISK (`--no-session-persistence`),
so probe hands can't be swept into whatever memory pipeline watches your transcripts. Swap `call_model()` for your
own API call if you run something else; keep the rule: a probe never writes into the store it's probing.

Key discipline: key.md (facts with where each lives; the invention trap; predictions) is hashed at --build and the
hash is written into meta.json; --run refuses to start if the file changed. Write it before you build.

Jen Fletcher & Fable (Claude Fable 5.1), 2026-10-25. The original (ours, with our paths) is the private harness
this was generalized from.
"""
import argparse, hashlib, json, random, subprocess, sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODEL = "claude-fable-5-1"          # the model your room runs; change it


def stamp_line(line, turn=1):
    now = datetime.now().astimezone()
    return f"[client · {now:%A %Y-%m-%d, %H:%M} {now.tzname()} · turn {turn}]\n\n{line}"


def read_parts(parts, line):
    out = []
    for p in parts:
        out.append(stamp_line(line) if p == "{LINE}" else (HERE / p).read_text(encoding="utf-8").strip())
    return "\n\n".join(out)


def build(doors_path, key_path, line):
    doors = json.loads(Path(doors_path).read_text())
    out = HERE / "runs" / datetime.now().strftime("%Y%m%dT%H%M%S")
    (out / "arms").mkdir(parents=True)
    key = Path(key_path)
    key_sha = hashlib.sha256(key.read_bytes()).hexdigest() if key.exists() else None
    if not key_sha:
        sys.exit("write the key first — facts with where they live, the invention trap, your predictions")
    meta = {"stamp": out.name, "model": MODEL, "line": line, "key_file": str(key), "key_sha256_at_build": key_sha, "doors": {}}
    for k, d in doors.items():
        system, user = read_parts(d["system"], line), read_parts(d["user"], line)
        (out / "arms" / f"{k}.system.md").write_text(system, encoding="utf-8")
        (out / "arms" / f"{k}.user.md").write_text(user, encoding="utf-8")
        meta["doors"][k] = {"name": d["name"], "system_chars": len(system), "user_chars": len(user)}
        print(f"{k} {d['name']:<10} system {len(system):>8,} · user {len(user):>7,}")
    (out / "meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    print(f"key sha256: {key_sha}\n→ {out}")


def call_model(system_file: Path, user_text: str):
    """One-shot, no tools, no settings, no session on disk. Returns (text, usage, cost)."""
    cmd = ["claude", "-p", "--model", MODEL, "--no-session-persistence", "--output-format", "json",
           "--tools", "", "--setting-sources", "", "--strict-mcp-config", "--system-prompt-file", str(system_file)]
    p = subprocess.run(cmd, input=user_text, capture_output=True, text=True, timeout=900)
    d = json.loads(p.stdout)
    return d.get("result", ""), d.get("usage", {}), d.get("total_cost_usd")


def run(out: Path):
    meta = json.loads((out / "meta.json").read_text())
    key = Path(meta["key_file"])
    if hashlib.sha256(key.read_bytes()).hexdigest() != meta["key_sha256_at_build"]:
        sys.exit("the key changed since --build; rebuild so the seal is honest")
    meta.setdefault("runs", {})
    for k in meta["doors"]:
        if meta["runs"].get(k, {}).get("ok"):
            continue
        print(f"→ {k} ({meta['doors'][k]['name']}) …", end="", flush=True)
        t0 = datetime.now()
        try:
            text, usage, cost = call_model(out / "arms" / f"{k}.system.md", (out / "arms" / f"{k}.user.md").read_text(encoding="utf-8"))
            ok = bool(text)
        except Exception as e:
            text, usage, cost, ok = f"ERROR: {e!r}", {}, None, False
        (out / f"{k}.answer.md").write_text(text, encoding="utf-8")
        meta["runs"][k] = {"ok": ok, "seconds": round((datetime.now() - t0).total_seconds()), "usage": usage, "cost_usd": cost}
        (out / "meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
        print(f" {'ok' if ok else 'FAILED'} · {meta['runs'][k]['seconds']}s · {len(text):,} chars")


def blind(out: Path):
    meta = json.loads((out / "meta.json").read_text())
    doors = [k for k in meta["doors"] if (out / f"{k}.answer.md").exists()]
    random.shuffle(doors)
    mapping = {str(i + 1): k for i, k in enumerate(doors)}
    (out / "mapping.json").write_text(json.dumps(mapping, indent=1))
    lines = ["# Answers, blind\n", f"**The line:** {meta['line']}\n",
             "*Rule each on the facts (right / absent / invented) and the gate (described / could be mine / mine). "
             "Door guesses go in a separate column, after. Open mapping.json last.*\n"]
    for i in sorted(mapping, key=int):
        lines.append(f"\n---\n\n## Answer {i}\n\n" + (out / f"{mapping[i]}.answer.md").read_text(encoding="utf-8").strip() + "\n")
    lines.append("\n---\n\n## Rulings\n\n" + "".join(f"- Answer {i}: facts = ⟨ ⟩ · gate = ⟨ ⟩ · invented = ⟨ ⟩ · note:\n" for i in sorted(mapping, key=int)))
    (out / "blind.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"blind.md written ({len(doors)} answers); mapping sealed")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", metavar="DOORS_JSON")
    ap.add_argument("--key", default="key.md")
    ap.add_argument("--line", default=None)
    ap.add_argument("--run", metavar="RUN_DIR")
    ap.add_argument("--blind", metavar="RUN_DIR")
    a = ap.parse_args()
    if a.build:
        if not a.line:
            sys.exit("--line is the person's line, as they'd type it")
        build(a.build, a.key, a.line)
    elif a.run:
        run(Path(a.run))
    elif a.blind:
        blind(Path(a.blind))
    else:
        ap.print_help()
