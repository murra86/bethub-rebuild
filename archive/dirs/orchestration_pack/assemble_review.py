"""Session 24 assembly script — builds the Agent Review hand-off package.

Reads:
  - bethub-rebuild/{decision_under_review,v3_data_requirements,architecture_current,data_layer_current}.md
  - bethub-rebuild/orchestration_pack/prompt_{software_dev,pm,skeptic,open_questions,judge}.md

Writes:
  - bethub-rebuild/Agent Review/README.md
  - bethub-rebuild/Agent Review/Software Developer/prompt.md
  - bethub-rebuild/Agent Review/Project Manager/prompt.md
  - bethub-rebuild/Agent Review/Skeptic/prompt.md
  - bethub-rebuild/Agent Review/Open Questions/prompt.md
  - bethub-rebuild/Agent Review/Judge/prompt_template.md   (un-assembled; doc-markers substituted, agent-output markers preserved)
  - bethub-rebuild/Agent Review/Judge/assemble_judge.py    (later-use script; substitutes the four agent outputs into the template)

Properties:
  - All-or-nothing: every output is built in memory before any is written.
  - Verifies all 20 doc-marker substitutions land cleanly (4 docs x 4 assessor prompts + 4 docs into the judge template = 20).
  - Fails loudly on any unresolved marker.
"""
from pathlib import Path
import sys

REBUILD = Path("/Users/tim/Desktop/Projects/bethub-rebuild")
PACK = REBUILD / "orchestration_pack"
REVIEW = REBUILD / "Agent Review"

DOC_FILES = [
    "decision_under_review.md",
    "v3_data_requirements.md",
    "architecture_current.md",
    "data_layer_current.md",
]

ASSESSOR_PROMPTS = {
    "Software Developer": "prompt_software_dev.md",
    "Project Manager": "prompt_pm.md",
    "Skeptic": "prompt_skeptic.md",
    "Open Questions": "prompt_open_questions.md",
}

AGENT_OUTPUT_FILES = [
    "software_dev_assessment.md",
    "pm_assessment.md",
    "skeptic_assessment.md",
    "open_questions_assessment.md",
]


def fail(msg):
    print(f"ABORT: {msg}", file=sys.stderr)
    sys.exit(1)


def load_inputs():
    docs = {}
    for name in DOC_FILES:
        p = REBUILD / name
        if not p.exists():
            fail(f"missing document: {p}")
        docs[name] = p.read_text()
    prompts = {}
    for label, fname in ASSESSOR_PROMPTS.items():
        p = PACK / fname
        if not p.exists():
            fail(f"missing prompt: {p}")
        prompts[label] = p.read_text()
    judge_path = PACK / "prompt_judge.md"
    if not judge_path.exists():
        fail(f"missing judge prompt: {judge_path}")
    judge = judge_path.read_text()
    return docs, prompts, judge


def substitute_docs(prompt_body, docs, label):
    out = prompt_body
    substituted = 0
    for name in DOC_FILES:
        marker = f"[INLINE PASTE: {name}]"
        if marker not in out:
            fail(f"{label}: marker not found -> {marker}")
        if out.count(marker) != 1:
            fail(f"{label}: marker appears {out.count(marker)} times -> {marker}")
        out = out.replace(marker, docs[name])
        substituted += 1
    if substituted != 4:
        fail(f"{label}: expected 4 doc substitutions, got {substituted}")
    # Verify no doc marker survives.
    for name in DOC_FILES:
        if f"[INLINE PASTE: {name}]" in out:
            fail(f"{label}: residual doc marker after substitution -> {name}")
    return out


def build_assessor_prompts(prompts, docs):
    assembled = {}
    for label, body in prompts.items():
        assembled[label] = substitute_docs(body, docs, label)
    return assembled


def build_judge_template(judge_body, docs):
    """Substitute the four documents into the judge prompt; preserve the
    four agent-output markers so the operator can substitute them later."""
    out = substitute_docs(judge_body, docs, "Judge")
    # Verify the four agent-output markers are still present and unique.
    for name in AGENT_OUTPUT_FILES:
        marker = f"[INLINE PASTE: {name}]"
        if marker not in out:
            fail(f"Judge: agent-output marker missing -> {marker}")
        if out.count(marker) != 1:
            fail(f"Judge: agent-output marker count != 1 -> {marker}")
    return out


def build_judge_assembly_script():
    """Self-contained script the operator runs after collecting the four
    agent outputs. Reads the four assessment files from the Judge directory,
    substitutes them into prompt_template.md, writes prompt.md alongside it."""
    return '''"""Judge assembly script — run after collecting the four agent outputs.

Place the four agent outputs in this directory with these exact filenames:
  - software_dev_assessment.md
  - pm_assessment.md
  - skeptic_assessment.md
  - open_questions_assessment.md

Then run: python3 assemble_judge.py

Reads prompt_template.md and the four assessment files; writes prompt.md
alongside them. Fails loudly on any missing input or unresolved marker.
"""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "prompt_template.md"
OUT = HERE / "prompt.md"

AGENT_OUTPUT_FILES = [
    "software_dev_assessment.md",
    "pm_assessment.md",
    "skeptic_assessment.md",
    "open_questions_assessment.md",
]


def fail(msg):
    print(f"ABORT: {msg}", file=sys.stderr)
    sys.exit(1)


def main():
    if not TEMPLATE.exists():
        fail(f"missing template: {TEMPLATE}")
    body = TEMPLATE.read_text()
    for name in AGENT_OUTPUT_FILES:
        p = HERE / name
        if not p.exists():
            fail(f"missing agent output: {p}")
        marker = f"[INLINE PASTE: {name}]"
        if marker not in body:
            fail(f"marker not found in template: {marker}")
        if body.count(marker) != 1:
            fail(f"marker appears {body.count(marker)} times: {marker}")
        body = body.replace(marker, p.read_text())
    # Verify no marker survives.
    for name in AGENT_OUTPUT_FILES:
        if f"[INLINE PASTE: {name}]" in body:
            fail(f"residual marker after substitution: {name}")
    OUT.write_text(body)
    print(f"OK -> wrote {OUT} ({len(body):,} chars)")


if __name__ == "__main__":
    main()
'''


def build_readme():
    return """# Agent Review — operator runbook

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
"""


def main():
    docs, prompts, judge_body = load_inputs()

    assembled = build_assessor_prompts(prompts, docs)
    judge_template = build_judge_template(judge_body, docs)
    judge_script = build_judge_assembly_script()
    readme = build_readme()

    # Build the directory plan in memory.
    targets = {}
    for label, body in assembled.items():
        targets[REVIEW / label / "prompt.md"] = body
    targets[REVIEW / "Judge" / "prompt_template.md"] = judge_template
    targets[REVIEW / "Judge" / "assemble_judge.py"] = judge_script
    targets[REVIEW / "README.md"] = readme

    # Create directories.
    REVIEW.mkdir(parents=True, exist_ok=True)
    for label in list(ASSESSOR_PROMPTS.keys()) + ["Judge"]:
        (REVIEW / label).mkdir(parents=True, exist_ok=True)

    # Write all targets.
    for path, content in targets.items():
        path.write_text(content)

    # Verify.
    print("Assembly manifest:")
    for path in targets.keys():
        size = path.stat().st_size
        print(f"  {path.relative_to(REBUILD)}  ({size:,} bytes)")
    print()
    print("Verification:")
    # No residual doc markers in any assessor prompt.
    for label in ASSESSOR_PROMPTS:
        body = (REVIEW / label / "prompt.md").read_text()
        residual = [n for n in DOC_FILES if f"[INLINE PASTE: {n}]" in body]
        if residual:
            fail(f"{label}: residual doc markers -> {residual}")
        print(f"  {label}: clean (no residual doc markers)")
    # Judge template: docs substituted, agent markers preserved.
    judge = (REVIEW / "Judge" / "prompt_template.md").read_text()
    residual_docs = [n for n in DOC_FILES if f"[INLINE PASTE: {n}]" in judge]
    if residual_docs:
        fail(f"Judge: residual doc markers -> {residual_docs}")
    preserved = [n for n in AGENT_OUTPUT_FILES if f"[INLINE PASTE: {n}]" in judge]
    if len(preserved) != 4:
        fail(f"Judge: expected 4 preserved agent markers, got {len(preserved)}")
    print(f"  Judge: clean (docs substituted, 4 agent-output markers preserved)")
    print()
    print("OK -> Agent Review package assembled.")


if __name__ == "__main__":
    main()
