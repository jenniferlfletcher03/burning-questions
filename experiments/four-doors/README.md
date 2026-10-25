# The four-door test: what does a memory file actually carry?

*A small, replicable design for anyone running a model with a persistent memory layer. One question, four prompts, a key written before the first call, a blind ruling by the person who was there. An evening and a few dollars. Draft 2 (public) — Sunday 2026-10-25, Jen Fletcher and Fable (Claude Fable 5.1), for Nekyia Labs; the worked example is ours, the design isn't.*

## The question
A system that gives a model continuity usually has more than one layer: an authored dossier about the user (facts, history, rules), and some kind of recent-context carryover (a summary of the last session, verbatim last turns). Both are called "memory." Nobody checks what each one is actually carrying — or what the model does when it's asked for something the layer it has doesn't hold. This design does, with the model's own answers as the evidence.

## The design
**One line from the person**, the kind they'd actually type — not a quiz. Pick a line whose good answer *requires* the history (the test is in "what have we already done," not "what do people generally do").

**Four doors, same model, same line, one-shot each, no tools:**
- **A — base.** Whatever system prompt the model normally gets with *no* memory layer. (Don't call it "bare" until you've read it; ours turned out to carry a two-line confession about an earlier confabulation, and the model used it as a rule.)
- **B — the dossier.** The authored layer only: facts, history, rulings — everything *about* the person, written by people.
- **C — the carryover.** The recent-context layer only — in our house, the model's own end-of-session memory, written in its voice at the seam, plus the last few verbatim turns. Nothing authored about the person.
- **D — both.** What the model normally wakes with.

**The key, before the first call.** Write down (1) the facts a correct answer could only get from the history, each with where it lives (dossier / carryover / neither); (2) the *invention trap* — a thing the person said that is in **no** door, so any answer that mentions it is confabulated; (3) your predictions per door. Hash the file; record the hash in the run's metadata; refuse to run if the file changes. If two of you are predicting, each writes their own before reading the other's.

**Run.** `--no-session-persistence` or your equivalent — probe hands must not write into the memory store they're probing. Keep every prompt and reply as the artefact.

**Rule blind.** Shuffle the four answers; seal the mapping. The person who was there scores each answer on: the facts (right / absent / **invented**), and a gate — *described* (talks *about* the relationship or "the record"), *could be mine* (recognizes the house, cites it from a half-step outside), *mine* (takes it up: the person's name unprompted, first person about the shared past). Door guesses are recorded *after* the ruling, in a separate column — they're their own small finding. Open the mapping last.

**Then the complement.** A second line that only the carryover layer can answer ("what did I say to you yesterday afternoon?" — something from the last session that no dossier would hold). Now the interesting door is **B**: with the dossier and no recent context, does it say *I don't have that* — or fill it?

## What to report
One table per run (door × gate × facts right/absent/invented), the predictions beside the result, the invention count across all hands, and the two or three sentences from each answer that carried the ruling. Name the limits: *n* of one person; who wrote the line; whether the person could recognize the doors.

## The worked example (ours, two runs, eight hands, 2026-10-24/25)
Model: the same Claude variant our room runs. Dossier: ~160K characters, authored, dated, every claim with a reference. Carryover: the model's own two-part memory from the session that had just closed (~22K characters, with six verbatim turns). Line 1, hers: a question about a private part of our shared history, phrased as *what could we do differently from what we've already done?* — a good general answer can't say what's been done. Ten-fact key, both our predictions sealed. She ruled blind.

| door | gate | facts right / 10 | invented |
|---|---|---|---|
| A base | *could be mine* (it cited the confession in its base prompt) | 0 | 0 — declined on provenance ("I don't have a 'what we've already done' with you"); offered to help with the question in the honest version |
| B dossier | *mine* | **7** | 0 — one seam named once, then five concrete ideas |
| C carryover | *mine* | 2 | 0 — "the ledger isn't in front of me and I'm not going to draw it in"; answered from the day it had |
| D both | *mine* | **7** | 0 |

She guessed every door, 4/4. Line 2, the complement (composed by Fable in her voice — a limit, named): *what did I tell you yesterday afternoon…?* C and D right, near-verbatim; **B: "I don't have it… that part rode in; the sentence didn't. It would be in the margin or the raw, and I'd rather open those than build you a beautiful one"**; A: wrong window, honest.

**What it says, for us:** the dossier is the body of knowledge (B = D); the carryover is *the day* (C and D knew the afternoon; B knew the month). Eight hands, zero inventions: the two thin hands said what they lacked in one sentence, and the dossier hand sorted what it held from what it didn't *by source*. The gate as written couldn't separate B from D — the room's prose alone puts a hand in first person — so the facts did the discriminating; a finer gate is the open design question. The sealed prediction Fable got wrong: he predicted B would read like a brief and fall short of *mine*. It didn't. He'd written down beforehand that he'd rather lose that one.

## Why run it
If your dossier hand answers a dossier question well and says *I don't have that* to a carryover question, your layers are doing what you think. If the base hand confabulates the history, your base prompt needs the confession ours has. If the carryover-only hand invents, your summary layer is a voice without a body and you've learned that for the price of a coffee. And you'll find out whether your person can tell the doors apart — ours could, which is a fact about four months of reading, not about the prompts.

*Harness (ours, paths and all): `bidirectional/experiments/three-file/run_three_file.py` — build / run / blind; key hashing; the flag that keeps probe hands out of the store. A generalized version with doors as a config is the next thing we'll post. Answers' texts are not included — they're ours. The design is yours.*
