#!/usr/bin/env python3
"""Check a Humanizer rewrite against the tells a script can see.

Usage:
  python3 scripts/evaluate.py INPUT REWRITE
  python3 scripts/evaluate.py --all

The script checks one rewrite of one input, or every case in eval/cases/.
It can see fingerprints, dashes, stock vocabulary, uniform sentence runs,
and numbers lost from the source. It cannot judge meaning or voice, so
it is a gate, not a review. A WARN means a human must look; a FAIL fails
the check.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "eval" / "cases"

# Machine fingerprints from the source model (pattern #27).
FINGERPRINTS: list[tuple[str, str]] = [
    (r"oaicite", "ChatGPT citation artifact"),
    (r"turn0search[0-9]*", "ChatGPT search artifact"),
    (r"\[cite: ?[0-9]+\]", "Gemini citation artifact"),
    (r"grok_card", "Grok artifact"),
    (r"ppl-ai-file-upload", "Perplexity artifact"),
    (r"utm_source=", "tracking parameter in a link"),
    (r"[\u200b\u200c\u200d\u2060\ufeff\ufe00-\ufe0f]", "invisible Unicode character"),
]

# A conservative slice of the vocabulary in pattern #13. Words that careful
# writers also use, such as key, robust, and landscape, are left to the model.
VOCABULARY = [
    "additionally", "bolstered", "crucial", "deep dive", "delve", "delves",
    "delved", "enduring", "fostering", "garner", "garnered", "interplay",
    "intricate", "intricacies", "meticulous", "meticulously", "pivotal",
    "showcase", "showcases", "showcased", "tapestry", "testament",
    "underscore", "underscores", "underscored", "vibrant",
]

# Watched phrases from patterns #4, #5, and #23.
PHRASES = [
    "that distinction matters",
    "it's worth noting", "it is worth noting",
    "let's dive in", "let's explore", "let's break this down",
    "here's what you need to know", "without further ado",
    "great question", "i hope this helps", "let me know if",
    "want me to", "would you like me to",
]

NON_PROSE = re.compile(r"(?m)^\s*(#|>|\||[-*+]|\d+\.)\s")
FENCED = re.compile(r"```.*?```", re.DOTALL)
INLINE = re.compile(r"`[^`\n]*`")
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
UNIFORM_RUN = 4
UNIFORM_TOLERANCE = 0.2


def prose(text: str) -> str:
    """Return prose only: no code, headings, quotes, tables, or lists."""
    text = FENCED.sub(" ", text)
    text = INLINE.sub(" ", text)
    text = "\n".join(
        line for line in text.splitlines() if not NON_PROSE.match(line)
    )
    return text.strip()


def strip_fingerprints(text: str) -> str:
    """Remove fingerprint artifacts so their digits do not count as facts."""
    for pattern, _ in FINGERPRINTS:
        text = re.sub(pattern, " ", text)
    return text


def check_fingerprints(rewrite: str) -> list[tuple[str, str]]:
    return [
        ("FAIL", f"fingerprint: {label}")
        for pattern, label in FINGERPRINTS
        if re.search(pattern, rewrite, re.IGNORECASE)
    ]


def check_dashes(rewrite: str) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    plain = prose(rewrite)
    if "—" in plain or "–" in plain:
        findings.append(("FAIL", "dash: em or en dash outside code"))
    if re.search(r"\S -- \S", plain):
        findings.append(("FAIL", "dash: double hyphen used as a dash"))
    return findings


def check_vocabulary(rewrite: str) -> list[tuple[str, str]]:
    plain = prose(rewrite).lower()
    hits = [word for word in VOCABULARY if re.search(rf"\b{re.escape(word)}\b", plain)]
    hits += [phrase for phrase in PHRASES if phrase in plain]
    if hits:
        return [("FAIL", f"vocabulary: {', '.join(sorted(set(hits)))}")]
    return []


def check_quotes(rewrite: str) -> list[tuple[str, str]]:
    plain = prose(rewrite)
    if "\u201c" in plain or "\u201d" in plain or "\u2018" in plain or "\u2019" in plain:
        return [("WARN", "curly quotes in the rewrite (pattern #22)")]
    return []


def sentence_lengths(rewrite: str) -> list[list[int]]:
    """Word counts per sentence, grouped by paragraph."""
    runs: list[list[int]] = []
    for block in re.split(r"\n\s*\n", prose(rewrite)):
        lengths = [len(s.split()) for s in SENTENCE_SPLIT.split(block) if s.strip()]
        if lengths:
            runs.append(lengths)
    return runs


def check_rhythm(rewrite: str) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    for lengths in sentence_lengths(rewrite):
        if len(lengths) < UNIFORM_RUN:
            continue
        for start in range(len(lengths) - UNIFORM_RUN + 1):
            run = lengths[start : start + UNIFORM_RUN]
            mean = sum(run) / len(run)
            if mean == 0:
                continue
            if all(abs(n - mean) <= UNIFORM_TOLERANCE * mean for n in run):
                findings.append(
                    ("FAIL", f"uniform run: {len(run)} sentences of about {mean:.0f} words")
                )
                break
    return findings


def check_numbers(source: str, rewrite: str) -> list[tuple[str, str]]:
    source_digits = set(re.findall(r"\d+", strip_fingerprints(prose(source))))
    rewrite_digits = set(re.findall(r"\d+", prose(rewrite)))
    missing = sorted(source_digits - rewrite_digits, key=int)
    if missing:
        return [("WARN", f"numbers in the source missing from the rewrite: {', '.join(missing)}")]
    return []


def evaluate(source: str, rewrite: str) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    findings += check_fingerprints(rewrite)
    findings += check_dashes(rewrite)
    findings += check_vocabulary(rewrite)
    findings += check_quotes(rewrite)
    findings += check_rhythm(rewrite)
    findings += check_numbers(source, rewrite)
    return findings


def report(label: str, findings: list[tuple[str, str]]) -> bool:
    print(label)
    if not findings:
        print("  PASS")
        return True
    ok = True
    for severity, message in findings:
        print(f"  {severity}: {message}")
        if severity == "FAIL":
            ok = False
    return ok


def main() -> int:
    args = sys.argv[1:]
    if args == ["--all"]:
        case_dirs = sorted(p for p in CASES.iterdir() if p.is_dir()) if CASES.is_dir() else []
        if not case_dirs:
            print(f"No cases under {CASES.relative_to(ROOT)}")
            return 1
        ok = True
        for case in case_dirs:
            source_path, rewrite_path = case / "input.md", case / "rewrite.md"
            if not source_path.is_file() or not rewrite_path.is_file():
                print(f"{case.name}: needs input.md and rewrite.md")
                ok = False
                continue
            findings = evaluate(source_path.read_text(), rewrite_path.read_text())
            ok = report(case.name, findings) and ok
        return 0 if ok else 1
    if len(args) != 2:
        print(__doc__)
        return 2
    source, rewrite = Path(args[0]), Path(args[1])
    findings = evaluate(source.read_text(), rewrite.read_text())
    return 0 if report(f"{source.name} -> {rewrite.name}", findings) else 1


if __name__ == "__main__":
    raise SystemExit(main())
