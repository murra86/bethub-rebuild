#!/usr/bin/env python3
"""Generate a field-level reference catalogue from the Racing API OpenAPI spec.

Regenerate:  python3 gen_racing_api_catalogue.py   (run from rebuild root)
Reads:       openapi.json
Writes:      racing_api_field_catalogue.md
Auto-generated tooling; the catalogue it emits is NOT hand-maintained.
"""
import json, re, datetime, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
spec = json.loads((ROOT / "openapi.json").read_text())


def clean(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "").replace("&amp;", "&")).strip()


def extract(desc, label):
    m = re.search(label + r"</b></td><td>(.*?)</td>", desc or "", re.S)
    return clean(m.group(1)) if m else ""


def type_of(prop):
    if prop is None:
        return "?"
    if "$ref" in prop:
        return prop["$ref"].split("/")[-1]
    if "anyOf" in prop:
        parts = [type_of(p) for p in prop["anyOf"]]
        nn = list(dict.fromkeys(p for p in parts if p != "null"))
        t = "|".join(nn) or "any"
        return t + (" (nullable)" if "null" in parts else "")
    t = prop.get("type", "any")
    if t == "array":
        return "array<" + type_of(prop.get("items", {})) + ">"
    return t


paths = spec.get("paths", {})
rows = []
for path in sorted(paths):
    for method, op in paths[path].items():
        if method not in ("get", "post", "put", "delete"):
            continue
        desc = op.get("description", "")
        rows.append((
            method.upper(), path,
            clean(op.get("summary", "")) or "—",
            extract(desc, r"Min\.?\s*Required Plan") or "—",
            extract(desc, r"Rate Limit") or "—",
        ))

schemas = spec.get("components", {}).get("schemas", {})
info = spec.get("info", {})
now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

out = []
out.append("# Racing API — field catalogue (generated)\n")
out.append(f"**Source:** `openapi.json` · **API:** {info.get('title')} v{info.get('version')}  ")
out.append(f"**Generated:** {now} · **Regenerate:** `python3 gen_racing_api_catalogue.py`\n")
out.append("Auto-generated, not hand-maintained — regenerate when the API version bumps. "
           "A grep reference: every endpoint and every response data point the API exposes. "
           "Curated capability + roles live in `data_sources.md`.\n")
out.append("---\n")
out.append(f"## Endpoints ({len(rows)})\n")
out.append("| Method · Path | Summary | Min plan | Rate limit |")
out.append("|---|---|---|---|")
for m, p, s, plan, rl in rows:
    out.append(f"| `{m} {p}` | {s} | {plan} | {rl} |")
out.append("\n---\n")
out.append(f"## Data schemas — fields ({len(schemas)})\n")
for name in sorted(schemas):
    sc = schemas[name]
    props = sc.get("properties", {})
    req = set(sc.get("required", []))
    out.append(f"### {name}")
    if not props:
        out.append("_(no listed properties)_\n")
        continue
    for fn in props:
        star = " *(req)*" if fn in req else ""
        out.append(f"- `{fn}` — {type_of(props[fn])}{star}")
    out.append("")

(ROOT / "racing_api_field_catalogue.md").write_text("\n".join(out))
print("schemas:", len(schemas), "endpoints:", len(rows))
