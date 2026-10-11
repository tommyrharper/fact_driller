# fact_driller

Pick n random facts, get a PDF, copy them out by hand.

```sh
./drill.py          # 10 random facts, opens the PDF in tdf
./drill.py 5        # 5 facts
./drill.py -t em    # only facts/em
./drill.py --all    # every fact, shuffled
./drill.py -l       # list facts
./drill.py --new    # proof whatever facts are uncommitted right now
```

Other flags: `--seed N` (reproducible pick), `-o path.pdf` (keep a copy),
`--no-open`.

The PDF is throwaway: it is built in a temp directory, opened in
[`tdf`](https://github.com/itsjunetime/tdf) when it is on PATH (otherwise the
system viewer), and deleted when the viewer closes. Pass `-o` to keep one.

## Adding facts

`--new` renders every fact git reports as added or modified, in order, so a
freshly written `.tex` can be eyeballed before committing.

One file per fact under `facts/<topic>/<slug>.tex`. First line is the title as
a LaTeX comment, the rest is body LaTeX dropped into an `enumerate` item:

```latex
% Lorentz force
\[ \boldsymbol{F} = q(\boldsymbol{E} + \boldsymbol{v} \times \boldsymbol{B}) \]
```

New topic = new subdirectory. The preamble (`amsmath`, `amssymb`, geometry)
lives in `drill.py`.

Needs `pdflatex` on PATH; `tdf` optional.
