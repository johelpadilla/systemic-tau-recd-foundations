# Fundación RECD

Paper de fundamentos:

**Systemic Tau and Hierarchical Ordinal Conjunctions: A Relational Theory of Critical Transitions**

+ **serie de notas formales** del roadmap teórico 1–6.

## Citation / DOI

- **Version DOI** (this release): see `zenodo/deposition_state.json` after publish  
- **Concept DOI** (all versions): [10.5281/zenodo.21287251](https://doi.org/10.5281/zenodo.21287251)  
- **Code (nested-recd)**: [10.5281/zenodo.21386071](https://doi.org/10.5281/zenodo.21386071)

## Lectura rápida

1. **`INDICE_NOTAS_FORMALES.md`** — respuestas al criterio de éxito + índice de PDFs  
2. **`ROADMAP_TEORICO.md`** — estado y canon C1–C38  
3. **`HANDOFF.md`** — continuidad de sesión  

## Archivos principales

| Archivo | Rol |
|---------|-----|
| `Systemic_Tau_RECD_Framework.tex` / `.pdf` | Paper de fundamentos (EN) |
| `Nota_Formal_Conjunciones_Ordinales.*` | Nota 1 — claims, Res |
| `Nota_Formal_Sinergia_Irreducible.*` | Nota 2 — L3 / excess3 / PID |
| `Nota_Formal_Ponderacion_Ontologica.*` | Nota 3 v0.2 — α(λ) + Gibbs |
| `Nota_Formal_Feigenbaum_Conjunciones.*` | Nota 4 v0.3 — cascada + diag Res_pair |
| `Nota_Formal_Invariantes_Robustez.*` | Nota 5 — robustez |
| `Nota_Formal_Categorias_Conjunciones.*` | Nota 6 — esbozo categórico |
| `scripts/cascade_r_sweep.py` | Barrido denso Feigenbaum |
| `scripts/res_pair_diagnostics.py` | Diagnóstico ventana / alfabeto / IPF |
| `scripts/gibbs_alpha_compare.py` | Gibbs-α vs template |
| `results/cascade_sweep/` | CSVs / JSON / informe del barrido |
| `results/res_pair_diag/` | Informe del diagnóstico Res_pair |
| `results/gibbs_alpha/` | Puente Gibbs + f3 en cascada |
| `COVER_LETTER_Chaos_PRE.md` | Carta de envío Chaos / PRE |
| `figures/` | Paneles sintéticos + cascada + diag |
| `references.bib` | Bibliografía del paper |

PDF del framework también en `../Publicaciones/`.

## Compilar

```bash
# Paper
pdflatex Systemic_Tau_RECD_Framework.tex && bibtex Systemic_Tau_RECD_Framework
pdflatex Systemic_Tau_RECD_Framework.tex && pdflatex Systemic_Tau_RECD_Framework.tex

# Notas 1–6
for f in Nota_Formal_Conjunciones_Ordinales Nota_Formal_Sinergia_Irreducible \
  Nota_Formal_Ponderacion_Ontologica Nota_Formal_Feigenbaum_Conjunciones \
  Nota_Formal_Invariantes_Robustez Nota_Formal_Categorias_Conjunciones; do
  pdflatex $f.tex && pdflatex $f.tex
done

# Barrido denso de r (opcional; ~10 min con Res_pair)
python3 scripts/cascade_r_sweep.py --n_realizations 6 --n_steps 2200

# Diagnóstico Res_pair (ventana / IPF; ~2 min)
python3 scripts/res_pair_diagnostics.py --n_realizations 4 --n_steps 1800

# Gibbs-α vs template (~20 s)
python3 scripts/gibbs_alpha_compare.py --n_realizations 4 --n_steps 1600
```
