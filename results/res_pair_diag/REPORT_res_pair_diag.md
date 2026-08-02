# Res_pair diagnostics report — 20260801_210544

Why does $\mathrm{Res}_{\mathrm{pair}}$ peak in period-2 and collapse near $r_\infty$?

## Configuration

```json
{
  "n_realizations": 4,
  "n_steps": 1800,
  "n_comp": 4,
  "coupling": 0.05,
  "noise": 0.003,
  "stride": 8,
  "windows": [
    13,
    26,
    52,
    104
  ],
  "stations": [
    [
      3.2,
      "S_k_p2"
    ],
    [
      3.3,
      "S_k_p2"
    ],
    [
      3.45,
      "S_k_p4"
    ],
    [
      3.57,
      "S_inf"
    ],
    [
      3.7,
      "S_ch"
    ],
    [
      3.85,
      "S_ch"
    ]
  ],
  "quick": false
}
```

## Headline

**IPF converges (not the cause); sparsity not_supported; window partial_window_bias; p2-peak real_structure_or_few_state**

## Hypothesis verdicts

```json
{
  "windows_used": {
    "w_lo": 13,
    "w_hi": 104
  },
  "H1_window_bias": {
    "res_inf_w13": 0.0011598589581075637,
    "res_inf_w104": 0.01179096454329327,
    "res_ch_w13": 0.008721397207672486,
    "res_ch_w104": 1.259418472223751,
    "lift_inf": true,
    "lift_ch": true,
    "still_collapsed_at_w104": true,
    "verdict": "partial_window_bias"
  },
  "H2_sparsity": {
    "sparsity_p2_w13": 0.8743990384615385,
    "sparsity_inf_w13": 0.41354739010989006,
    "sparser_at_inf": false,
    "corr_sparsity_vs_Res": 0.4699458685564155,
    "verdict": "not_supported"
  },
  "H3_ipf": {
    "ipf_dev_p2_w13": 0.0003086258585240589,
    "ipf_dev_inf_w13": 1.97238618625346e-05,
    "ipf_failure_at_inf": false,
    "verdict": "ipf_ok_not_the_cause"
  },
  "H5_period2_peak": {
    "res_p2_w104": 0.07993293138340649,
    "res_inf_w104": 0.01179096454329327,
    "peak_persists": true,
    "verdict": "real_structure_or_few_state"
  },
  "full_block": {
    "full_p2": 0.008604072514233261,
    "full_inf": 0.0010454138661043018,
    "full_ch": 0.45435208367188806,
    "note": "full-block Res on ~800 symbols; still finite alphabet"
  },
  "headline": "IPF converges (not the cause); sparsity not_supported; window partial_window_bias; p2-peak real_structure_or_few_state"
}
```

## Summary table (mean Res_pair by r × window)

| r | station | w=13 | w=26 | w=52 | w=104 | sparsity_w13 | unique_w13 | IPF_dev_w13 | full_Res |
|---|---|---|---|---|---|---|---|---|---|---|
| 3.20 | S_k_p2 | 0.1921 | 0.3170 | 0.1844 | 0.0799 | 0.874 | 11.4 | 3.09e-04 | 0.0086 |
| 3.30 | S_k_p2 | 0.1813 | 0.3030 | 0.1832 | 0.0800 | 0.874 | 11.4 | 3.12e-04 | 0.0087 |
| 3.45 | S_k_p4 | 0.0972 | 0.2002 | 0.1505 | 0.0690 | 0.820 | 10.7 | 2.63e-04 | 0.0055 |
| 3.57 | S_inf | 0.0012 | 0.0047 | 0.0076 | 0.0118 | 0.414 | 5.4 | 1.97e-05 | 0.0010 |
| 3.70 | S_ch | 0.0036 | 0.0156 | 0.0407 | 0.0615 | 0.582 | 7.6 | 7.16e-05 | 0.0052 |
| 3.85 | S_ch | 0.0087 | 0.1495 | 0.9398 | 1.2594 | 0.970 | 12.6 | 2.74e-04 | 0.4544 |

## Reading guide

- **H1 (window):** if Res rises with w near $r_\infty$ but remains ≪ period-2, finite-window bias is *partial*, not full explanation.
- **H2 (sparsity):** high unique/w ⇒ each joint pattern appears ~once ⇒ pairwise maxent can fit sparse tables almost perfectly ⇒ Res→0.
- **H3 (IPF):** if final max_dev ≪ 1e-6, IPF converged; collapse is not numerical failure.
- **H5 (period-2 peak):** if Res stays high at w=104 in period-2, the peak is few-state joint structure (or true higher-order residual), not short-window noise.
- **Full-block:** long contiguous estimate; still limited by observed alphabet size.

## Figures

- `figures/res_pair_diag_window_20260801_210544.png`
- `figures/res_pair_diag_sparsity_20260801_210544.png`
- `figures/res_pair_diag_mechanisms_20260801_210544.png`
- `figures/res_pair_diag_fullblock_20260801_210544.png`

## Canon implication

Report excess3 and Res_pair separately (E1). Collapse near $r_\infty$ must be qualified by window length and support sparsity before claiming absence of strong L3.
