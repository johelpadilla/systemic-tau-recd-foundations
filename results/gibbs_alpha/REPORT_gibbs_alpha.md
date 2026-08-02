# Gibbs-α comparison report — 20260801_211200

Via B (Note 3) vs template α family.

**Bridge max L∞=0.163; corr(f3_T,f3_G)=0.997; corr(f3_T,excess3)=0.080 → abundance≠share**

## Shape bridge (normalized α on λ∈[0,2])

```json
{
  "max_L1": 0.32601882529120985,
  "max_Linf": 0.16300941264560492,
  "mean_L1": 0.2147328219259113,
  "kappa": 1.5,
  "note": "L1/L\u221e on L1-normalized families over \u03bb\u2208[0,2]"
}
```

## Cascade f3 shares (mean over seeds)

| r | λ | excess3 | highL3 | f3 template | f3 Gibbs | Δ(T−G) |
|---|---|---|---|---|---|---|
| 3.20 | 0.00 | 1.749 | 0.434 | 0.577 | 0.577 | 0.000 |
| 3.30 | 0.00 | 1.753 | 0.464 | 0.635 | 0.635 | 0.000 |
| 3.45 | 0.00 | 1.824 | 0.697 | 0.640 | 0.640 | 0.000 |
| 3.57 | 0.00 | 2.266 | 0.987 | 0.585 | 0.585 | 0.000 |
| 3.70 | 0.46 | 2.069 | 0.962 | 0.870 | 0.872 | -0.002 |
| 3.85 | 1.00 | 1.856 | 0.823 | 0.884 | 0.926 | -0.041 |

## Verdicts

```json
{
  "bridge": {
    "max_L1": 0.32601882529120985,
    "max_Linf": 0.16300941264560492,
    "mean_L1": 0.2147328219259113,
    "kappa": 1.5,
    "note": "L1/L\u221e on L1-normalized families over \u03bb\u2208[0,2]"
  },
  "corr_f3template_vs_excess3": 0.08032124960421426,
  "corr_f3gibbs_vs_excess3": 0.05942990116344381,
  "corr_f3template_vs_f3gibbs": 0.9967798921468837,
  "abundance_neq_share": true,
  "engines_similar_on_cascade": true,
  "headline": "Bridge max L\u221e=0.163; corr(f3_T,f3_G)=0.997; corr(f3_T,excess3)=0.080 \u2192 abundance\u2260share"
}
```

## Reading

- Bridge error finite ⇒ Conj. template↔Gibbs is a *shape* approximation, not identity.
- High corr(f3_T, f3_G) ⇒ both engines push L3 share the same qualitative way along r.
- Low corr(f3, excess3) ⇒ **abundance ≠ share** (Note 3 discipline).

## Figures

- `figures/gibbs_alpha_bridge_20260801_211200.png`
- `figures/gibbs_f3_cascade_20260801_211200.png`
- `figures/gibbs_share_vs_abundance_20260801_211200.png`
