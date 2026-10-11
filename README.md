# fact_driller

Pick n random facts, get a PDF, copy them out by hand.

```sh
./drill.py          # 10 random facts, opens the PDF
./drill.py 5        # 5 facts
./drill.py -t em    # only facts/em
./drill.py --all    # every fact, shuffled
./drill.py -l       # list facts
```

Other flags: `--seed N` (reproducible pick), `-o path.pdf`, `--no-open`.
PDFs land in `out/` (gitignored), named by timestamp.

## Adding facts

One file per fact under `facts/<topic>/<slug>.tex`. First line is the title as
a LaTeX comment, the rest is body LaTeX dropped into an `enumerate` item:

```latex
% Lorentz force
\[ \boldsymbol{F} = q(\boldsymbol{E} + \boldsymbol{v} \times \boldsymbol{B}) \]
```

New topic = new subdirectory. The preamble (`amsmath`, `amssymb`, geometry)
lives in `drill.py`.

Needs `pdflatex` on PATH.
