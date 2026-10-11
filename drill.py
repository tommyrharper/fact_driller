#!/usr/bin/env python3
"""Pick n random facts from facts/ and show a throwaway PDF to copy out by hand."""

import argparse
import datetime
import glob
import os
import random
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
FACTS_DIR = os.path.join(ROOT, "facts")

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


def render(facts):
    body = "\n".join(
        "\\item \\textbf{%s}\n%s" % (title, tex) for title, tex, _ in facts
    )
    return (
        PREAMBLE.replace("DATE", datetime.date.today().isoformat())
        .replace("COUNT", str(len(facts)))
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
    p.add_argument("--no-open", action="store_true", help="do not open the PDF (needs --out)")
    args = p.parse_args()

    if args.no_open and not args.out:
        p.error("--no-open without --out would build a PDF and throw it away")

    facts = load_facts(args.topic)
    if not facts:
        sys.exit("no facts found in %s" % FACTS_DIR)

    if args.list:
        for title, _, rel in facts:
            print("%-50s %s" % (title, rel))
        print("%d facts" % len(facts))
        return

    rng = random.Random(args.seed)
    n = len(facts) if args.all else min(args.n, len(facts))
    if not args.all and args.n > len(facts):
        print("only %d facts available" % len(facts), file=sys.stderr)
    picked = rng.sample(facts, n)

    with tempfile.TemporaryDirectory() as tmp:
        pdf = os.path.join(tmp, "drill.pdf")
        build_pdf(render(picked), pdf)
        if args.out:
            shutil.copy(pdf, args.out)
            print(args.out)
        if not args.no_open:
            viewer = shutil.which("tdf") or ("open" if sys.platform == "darwin" else "xdg-open")
            subprocess.run([viewer, pdf])


if __name__ == "__main__":
    main()
