# Agent Review — operator runbook

Hand-off package for the multi-agent governance review of the v3 rebuild design.
Each subdirectory contains the assembled prompt for one agent. The four
documents under review have already been inline-pasted into each prompt.

## What's in this directory

- `Software Developer/prompt.md` — assessor prompt, Claude Opus, fresh session.
- `Project Manager/prompt.md` — assessor prompt, Gemini.
- `Skeptic/prompt.md` — assessor prompt, Grok.
- `Open Questions/prompt.md` — assessor prompt, Claude Opus, fresh session (separate from Software Developer).
- `Judge/prompt_template.md` — judge prompt with documents inline-pasted; four
  agent-output markers preserved for later substitution.
- `Judge/assemble_judge.py` — script that assembles the final judge prompt
  once the four agent outputs are collected.

## Step-by-step

### 1. Run the four assessor agents (in any order, in parallel if you like)

For each of the four assessor subdirectories:

1. Open a **fresh session** in the agent's interface (Claude Opus / Gemini /
   Grok / Claude Opus). The two Claude Opus seats (Software Developer and
   Open Questions) must be **separate sessions** — do not reuse one session
   for both.
2. Paste the entire contents of `prompt.md` into the first message.
3. Send. Wait for the agent's response.
4. Save the agent's response back into the same subdirectory using the
   filename shown below. The filename matters — `assemble_judge.py` looks
   for these exact names.

| Agent              | Save response as                  |
|--------------------|-----------------------------------|
| Software Developer | `software_dev_assessment.md`      |
| Project Manager    | `pm_assessment.md`                |
| Skeptic            | `skeptic_assessment.md`           |
| Open Questions     | `open_questions_assessment.md`    |

If the agent's response is split across multiple turns (some interfaces
truncate long outputs), concatenate them into a single file in order. Do not
edit the content; preserve the agent's full output verbatim.

### 2. Move the four agent outputs into the Judge directory

Copy (or move) the four `*_assessment.md` files from their respective agent
subdirectories into `Judge/`. After this step, `Judge/` contains:

- `prompt_template.md` (already there)
- `assemble_judge.py` (already there)
- `software_dev_assessment.md` (you placed)
- `pm_assessment.md` (you placed)
- `skeptic_assessment.md` (you placed)
- `open_questions_assessment.md` (you placed)

### 3. Assemble the judge prompt

From the `Judge/` directory, run:

```
cd "/Users/tim/Desktop/Projects/bethub-rebuild/Agent Review/Judge"
python3 assemble_judge.py
```

The script writes `prompt.md` alongside the template. It fails loudly if any
of the four agent outputs is missing or any marker fails to substitute.

### 4. Run the judge

1. Open a **fresh Claude Opus session** — separate from the Software Developer
   and Open Questions sessions.
2. Paste the entire contents of `Judge/prompt.md` into the first message.
3. Send. Wait for the synthesis.
4. Save the response as `Judge/judge_synthesis.md`.

### 5. Hand back to operator-Claude session

Open a fresh operator-Claude session in claude.ai with rebuild-folder access.
The session's job is to read the judge synthesis (and the four agent outputs
if it wants to drill into a specific finding) and produce operator-facing
analysis of what the multi-agent review surfaced. This is Session 25 in the
rebuild's session sequence.

The operator-Claude session can locate everything by reading
`Agent Review/Judge/judge_synthesis.md` and the four
`Agent Review/<Agent>/prompt.md` plus their corresponding `*_assessment.md`
files (which will live in `Judge/` after step 2).

## Notes

- **Do not edit the assembled prompts.** They are byte-frozen at the moment
  of assembly. If a document changes, re-run the assembly script
  (`orchestration_pack/assemble_review.py`) to rebuild the package.
- **Each assessor sees only the four documents.** They do not see each other's
  prompts, each other's outputs, or any of the rebuild-folder governance
  files. The judge sees the four documents plus the four agent outputs.
- **Model assignments are locked** per the orchestration plan: Software
  Developer = fresh Claude Opus, Project Manager = Gemini, Skeptic = Grok,
  Open Questions = fresh Claude Opus (separate session), Judge = fresh
  Claude Opus (separate from both). Mixing model families across the
  assessor seats is the structural protection against within-family
  convergence.
