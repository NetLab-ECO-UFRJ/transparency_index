# Social Media Data Transparency Index

A joint research initiative by [NetLab/UFRJ](https://netlab.eco.ufrj.br) and the [Minderoo Centre for Technology & Democracy](https://www.minderoo.org/technology-and-democracy/) at the University of Cambridge.

This report evaluates social media platform transparency across three regions — Brazil, the European Union, and the United Kingdom — using a weighted 0–100 scoring methodology across two frameworks: **User-Generated Content (UGC)** and **Advertising (ADS)** data transparency.

## Reproduce

```bash
# Install uv and Quarto (https://quarto.org/docs/get-started/)
uv sync
uv run quarto render   # output → _output/
```

## Data & Code

Assessment data is stored as YAML in `data/`, scoring logic in `utils/`, and platform reports in `chapters/appendices/`.
