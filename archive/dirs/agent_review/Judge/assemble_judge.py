"""Judge assembly script — run after collecting the four agent outputs.

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
