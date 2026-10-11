#!/usr/bin/env python3
"""Pick n random facts from facts/ and show a throwaway PDF to copy out by hand."""

import argparse
import datetime
import glob
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
FACTS_DIR = os.path.join(ROOT, "facts")
COUNTS_FILE = os.path.join(ROOT, "drills.json")

PREAMBLE = r"""\documentclass[12pt]{article}
\usepackage[a4paper,margin=2cm]{geometry}
\usepackage{amsmath,amssymb}
\usepackage{enumitem}
\pagestyle{empty}
\setlength{\parindent}{0pt}
\begin{document}
\textbf{\large Fact drill} \hfill DATE \quad (COUNT facts)
\vspace{1em}
\begin{enumerate}[itemsep=1em,leftmargin=*]
BODY
\end{enumerate}
\end{document}
"""


def load_facts(topic=None):
    pattern = os.path.join(FACTS_DIR, "**", "*.tex")
    facts = []
    for path in sorted(glob.glob(pattern, recursive=True)):
        rel = os.path.relpath(path, FACTS_DIR)
        if topic and not rel.startswith(topic):
            continue
        with open(path) as f:
            lines = f.read().strip().split("\n")
        if not lines[0].startswith("%"):
            sys.exit("%s: first line must be '%% Title'" % rel)
        facts.append((lines[0].lstrip("% ").strip(), "\n".join(lines[1:]).strip(), rel))
    return facts


def load_counts():
    try:
        with open(COUNTS_FILE) as f:
            return json.load(f)
    except (IOError, ValueError):
        return {}


def record_drill(facts):
    counts = load_counts()
    for _, _, rel in facts:
        counts[rel] = counts.get(rel, 0) + 1
    with open(COUNTS_FILE, "w") as f:
        json.dump(counts, f, indent=0, sort_keys=True)


def weighted_sample(facts, n, counts, seed=None):
    """n facts, each weighted 1/(1 + times drilled) - Efraimidis-Spirakis keys."""
    rng = random.Random(seed)
    key = lambda f: rng.random() ** (1 + counts.get(f[2], 0))
    return sorted(facts, key=key, reverse=True)[:n]


def git(*argv):
    proc = subprocess.run(
        ["git", "-C", ROOT] + list(argv), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )
    if proc.returncode != 0:
        sys.exit("--new needs a git repository")
    return proc.stdout.decode().splitlines()


def recently_added(rev):
    """Fact paths (relative to facts/) that are uncommitted, or touched by rev."""
    lines = git("status", "--porcelain", "-uall", "--", FACTS_DIR)
    source = "working tree"
    if not lines:
        if rev == "auto":
            rev = (git("log", "-1", "--format=%H", "--", FACTS_DIR) or ["HEAD"])[0]
        lines = ["   " + p for p in git("show", "--name-only", "--pretty=", rev, "--", FACTS_DIR)]
        source = "%s (%s)" % (rev, "".join(git("show", "-s", "--pretty=%s", rev)))
    paths = set()
    for line in lines:
        path = line[3:].split(" -> ")[-1].strip('"')
        paths.add(os.path.relpath(os.path.join(ROOT, path), FACTS_DIR))
    return paths, source


def render(facts):
    body = "\n".join(
        "\\item \\textbf{%s}\n%s" % (title, tex) for title, tex, _ in facts
    )
    return (
        PREAMBLE.replace("DATE", datetime.date.today().isoformat())
        .replace("COUNT facts", "%d fact%s" % (len(facts), "" if len(facts) == 1 else "s"))
        .replace("BODY", body)
    )


def build_pdf(tex, out_path):
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "drill.tex")
        with open(src, "w") as f:
            f.write(tex)
        proc = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "drill.tex"],
            cwd=tmp,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        if proc.returncode != 0:
            sys.stdout.write(proc.stdout.decode("utf-8", "replace"))
            kept = os.path.join(ROOT, "drill-failed.tex")
            shutil.copy(src, kept)
            sys.exit("pdflatex failed; source kept at %s" % kept)
        shutil.copy(os.path.join(tmp, "drill.pdf"), out_path)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("n", nargs="?", type=int, default=10, help="facts to drill (default 10)")
    p.add_argument("-t", "--topic", help="restrict to a facts/ subdirectory")
    p.add_argument("--seed", type=int, help="reproducible selection")
    p.add_argument("-o", "--out", help="also keep a copy of the PDF here")
    p.add_argument("-l", "--list", action="store_true", help="list available facts and exit")
    p.add_argument("--all", action="store_true", help="use every fact, in random order")
    p.add_argument("--new", nargs="?", const="auto", metavar="REV",
                   help="proof uncommitted facts; if the tree is clean, those touched by REV "
                        "(default: the last commit that touched facts/)")
    p.add_argument("--no-open", action="store_true", help="do not open the PDF (needs --out)")
    p.add_argument("--no-record", action="store_true", help="do not ask whether you drilled them")
    args = p.parse_args()

    if args.no_open and not args.out:
        p.error("--no-open without --out would build a PDF and throw it away")

    facts = load_facts(args.topic)
    if not facts:
        sys.exit("no facts found in %s" % FACTS_DIR)

    counts = load_counts()

    if args.list:
        for title, _, rel in sorted(facts, key=lambda f: (counts.get(f[2], 0), f[2])):
            print("%4d  %-50s %s" % (counts.get(rel, 0), title, rel))
        print("%d facts, %d drills" % (len(facts), sum(counts.values())))
        return

    if args.new:
        changed, source = recently_added(args.new)
        picked = [f for f in facts if f[2] in changed]
        if not picked:
            sys.exit("no new facts in %s; try --new <rev> or -t <path prefix>" % source)
        print("proofing %d fact(s) from %s" % (len(picked), source), file=sys.stderr)
    elif args.all:
        picked = random.Random(args.seed).sample(facts, len(facts))
    else:
        if args.n > len(facts):
            print("only %d facts available" % len(facts), file=sys.stderr)
        picked = weighted_sample(facts, min(args.n, len(facts)), counts, args.seed)

    with tempfile.TemporaryDirectory() as tmp:
        pdf = os.path.join(tmp, "drill.pdf")
        build_pdf(render(picked), pdf)
        if args.out:
            shutil.copy(pdf, args.out)
            print(args.out)
        if not args.no_open:
            viewer = shutil.which("tdf") or ("open" if sys.platform == "darwin" else "xdg-open")
            subprocess.run([viewer, pdf])

    if args.no_open or args.no_record or args.new or not sys.stdin.isatty():
        return
    try:
        answer = input("Drilled all %d? [Y/n] " % len(picked)).strip().lower()
    except EOFError:
        return
    if answer in ("", "y", "yes"):
        record_drill(picked)
        print("recorded; %d total drills" % sum(load_counts().values()))


if __name__ == "__main__":
    main()
