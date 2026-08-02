# Cascade r-sweep report — 20260801_204449

Synthetic evidence for **Note 4** conjectures (Feigenbaum conjunction structure).
Not theorems. nested-recd pipeline; weakly coupled logistic maps.

## Configuration

```json
{
  "mode": "quick",
  "n_realizations": 3,
  "n_steps": 1200,
  "n_comp": 4,
  "coupling": 0.05,
  "noise": 0.003,
  "window": 13,
  "excess_thresh": 1.75,
  "compute_res": true,
  "res_stride": 8,
  "r_grid": [
    3.2,
    3.4,
    3.5,
    3.55,
    3.565,
    3.5699456,
    3.6,
    3.7,
    3.8,
    3.85,
    3.9
  ],
  "nested_recd_path": "/Users/johelpadilla/grok-safe/Investigaciones/nested-recd/src",
  "R_INF": 3.5699456,
  "DELTA": 4.6692016091
}
```

## Conjecture checks (operational)

```json
{
  "conj_mono": {
    "excess3_chaos_gt_pre": true,
    "highL3_chaos_gt_pre": true,
    "res_pair_chaos_gt_pre": false,
    "pre_r": 3.2,
    "chaos_r": 3.85,
    "pre_excess3": 1.7533910558798222,
    "chaos_excess3": 1.8606988291253177,
    "pre_highL3": 0.45548135781858656,
    "chaos_highL3": 0.8363939899833054,
    "pre_res_pair": 0.1996706363774217,
    "chaos_res_pair": 0.007195159244592422
  },
  "conj_rinf": {
    "r_inf_used": 3.5699456,
    "std_excess3_at_rinf": 0.08054867834396613,
    "std_excess3_at_chaos": 0.112781242679711,
    "std_abs_tau_at_rinf": 0.05098511016958404,
    "std_abs_tau_at_chaos": 0.09603806492441669,
    "mean_excess3_at_rinf": 2.364423000036193,
    "mean_excess3_at_chaos": 1.8606988291253177,
    "mean_ex_chaos_ge_rinf": false,
    "note": "Evidence only; local max of variability needs denser comparison to neighbors"
  },
  "conj_nontriv": {
    "delta_A3_pre_to_chaos": 0.10730777324549545,
    "delta_abs_tau_pre_to_chaos": -0.42568131457020353,
    "corr_A3_vs_abs_tau_across_r": -0.1853660716685342,
    "not_perfect_proxy": true
  },
  "landmarks": {
    "R_INF": 3.5699456,
    "DELTA": 4.6692016091,
    "R_P3": 3.828427
  }
}
```

## Summary table (selected columns)

| r | station | excess3 | highL3 | Res_pair | std_ex | |τ| | var | AC1 | f3 |
|---|---|---|---|---|---|---|---|---|---|
| 3.20000 | S_k_p2 | 1.7534 | 0.455 | 0.1997 | 0.0778 | 0.544 | 0.0204 | -0.999 | 0.545 |
| 3.40000 | S_k_p2 | 1.8117 | 0.655 | 0.1176 | 0.1033 | 0.219 | 0.0349 | -0.999 | 0.586 |
| 3.50000 | S_k_p4 | 1.9799 | 0.907 | 0.0330 | 0.1831 | 0.083 | 0.0413 | -0.996 | 0.579 |
| 3.55000 | S_k_p8 | 2.1414 | 0.956 | 0.0093 | 0.1683 | 0.149 | 0.0438 | -0.987 | 0.629 |
| 3.56500 | S_inf_minus | 2.2886 | 0.986 | 0.0019 | 0.1217 | 0.246 | 0.0456 | -0.962 | 0.585 |
| 3.56995 | S_inf | 2.3644 | 0.990 | 0.0000 | 0.0805 | 0.248 | 0.0459 | -0.949 | 0.543 |
| 3.60000 | S_post_acc | 2.3400 | 0.989 | 0.0001 | 0.1131 | 0.064 | 0.0467 | -0.949 | 0.732 |
| 3.70000 | S_ch | 1.9406 | 0.870 | 0.0074 | 0.1797 | 0.061 | 0.0498 | -0.891 | 0.831 |
| 3.80000 | S_ch | 1.7848 | 0.605 | 0.0147 | 0.1241 | 0.117 | 0.0467 | -0.736 | 0.872 |
| 3.85000 | S_ch | 1.8607 | 0.836 | 0.0072 | 0.1128 | 0.119 | 0.0556 | -0.686 | 0.884 |
| 3.90000 | S_ch | 1.9011 | 0.906 | 0.0081 | 0.1060 | 0.112 | 0.0661 | -0.620 | 0.883 |

## Figures

- `figures/cascade_A3_vs_r_20260801_204449.png`
- `figures/cascade_variability_tau_20260801_204449.png`
- `figures/cascade_ews_vs_A3_20260801_204449.png`
- `figures/cascade_phi_f3_20260801_204449.png`

## Reading guide

- **Conj. mono**: chaos A3 > period-2/pre A3 (excess3 / highL3 / Res_pair).
- **Conj. rinf**: look at `std_excess3` / `std_abs_tau` peaking near r_∞; mean A3 plateau more in S_ch.
- **Conj. nontriv**: corr(A3(r), |τ|(r)) far from ±1; classical var shape ≠ A3 shape.
- **f3** uses α(λ(r)) design engine — report separately from abundance.
