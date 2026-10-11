# fact_driller

Pick n random facts, get a PDF, copy them out by hand.

```sh
./drill.py          # 10 random facts, opens the PDF in tdf
./drill.py 5        # 5 facts
./drill.py -t em    # only facts/em
./drill.py --all    # every fact, shuffled
./drill.py -l       # list facts, least-drilled first, with drill counts
./drill.py --new    # proof just-added facts (uncommitted, else last facts/ commit)
```

Other flags: `--seed N` (reproducible pick), `-o path.pdf` (keep a copy),
`--no-open`, `--no-record`.

## Spaced-ish repetition

On quitting the viewer you are asked `Drilled all N? [Y/n]`; answering yes bumps
each shown fact's counter in `drills.json` (gitignored, local to this machine).

Selection weight is `1 / (1 + times drilled)`, so a fact drilled 9 times is
picked about a tenth as often as an untouched one. `--all` and `--new` ignore
the weighting and never prompt.

The PDF is throwaway: it is built in a temp directory, opened in
[`tdf`](https://github.com/itsjunetime/tdf) when it is on PATH (otherwise the
system viewer), and deleted when the viewer closes. Pass `-o` to keep one.

## Adding facts

`--new` renders just the facts you last touched, in order, so a fresh `.tex`
can be eyeballed. It uses whatever is uncommitted under `facts/`; if the tree
is clean it falls back to the last commit that touched `facts/`. Pass a rev to
pick another: `./drill.py --new HEAD~3`.

One file per fact under `facts/<topic>/<slug>.tex`. First line is the title as
a LaTeX comment, the rest is body LaTeX dropped into an `enumerate` item:

```latex
% Lorentz force
\[ \boldsymbol{F} = q(\boldsymbol{E} + \boldsymbol{v} \times \boldsymbol{B}) \]
```

New topic = new subdirectory. The preamble (`amsmath`, `amssymb`, geometry)
lives in `drill.py`.

Needs `pdflatex` on PATH; `tdf` optional.
