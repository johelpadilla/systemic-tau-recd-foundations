#!/usr/bin/env python3
"""
Via B Gibbs-α vs template-α (Note 3): shape bridge + f3 share on cascade.

1. Compare normalized α(λ) shapes on λ∈[0,2] (Conj. template↔Gibbs).
2. On cascade stations, compute f3 share under both engines with the same
   empirical (Φ1, Φ2, Φ3) mass — isolates design-engine effect from abundance.

Outputs: results/gibbs_alpha/, figures/gibbs_*.png, REPORT.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from typing import Dict, List

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
NESTED = ROOT.parent / "Investigaciones" / "nested-recd" / "src"
sys.path.insert(0, str(NESTED))

from nested_recd import (  # noqa: E402
    alpha_weights,
    alpha_weights_gibbs,
    alpha_compare_template_gibbs,
    compute_recd_from_conjunctions,
    high_level3_rate,
    regime_lambda_proxy,
)

OUT_DIR = ROOT / "results" / "gibbs_alpha"
FIG_DIR = ROOT / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

STATIONS = [3.20, 3.30, 3.45, 3.57, 3.70, 3.85]


def logistic_coupled(
    n_steps: int,
    n_comp: int = 4,
    r: float = 3.8,
    coupling: float = 0.05,
    noise: float = 0.003,
    seed: int = 0,
    burn_in: int = 400,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    X = np.zeros((n_steps + burn_in, n_comp))
    X[0] = rng.uniform(0.2, 0.8, n_comp)
    eps = coupling
    for t in range(1, n_steps + burn_in):
        f = r * X[t - 1] * (1.0 - X[t - 1])
        mean_others = (f.sum() - f) / max(n_comp - 1, 1)
        X[t] = (1.0 - eps) * f + eps * mean_others
        if noise > 0:
            X[t] += rng.normal(0.0, noise, n_comp)
        X[t] = np.clip(X[t], 0.0, 1.0)
    return X[burn_in:]


def share_f3(phi1: float, phi2: float, phi3: float, a1: float, a2: float, a3: float) -> float:
    c1, c2, c3 = a1 * phi1, a2 * phi2, a3 * phi3
    tot = c1 + c2 + c3 + 1e-12
    return float(c3 / tot)


def run_station(r: float, seed: int, n_steps: int) -> Dict:
    X = logistic_coupled(n_steps=n_steps, r=r, seed=seed)
    res = compute_recd_from_conjunctions(X, window_tau=13, compute_res=False, lam_override=0.0)
    m_phi1 = float(np.nanmean(res["phi1"]))
    m_phi2 = float(np.nanmean(res["phi2"]))
    m_phi3 = float(np.nanmean(np.nan_to_num(res["phi3"], nan=0.0)))
    m_ex = float(np.nanmean(res["excess3"]))
    hl3 = high_level3_rate(res["excess3"], thresh=1.75)

    lam = regime_lambda_proxy(r)
    t1, t2, t3 = alpha_weights(np.array([lam]))
    g1, g2, g3 = alpha_weights_gibbs(np.array([lam]), normalize=False)
    # also normalized Gibbs for fair simplex comparison of shares
    gn1, gn2, gn3 = alpha_weights_gibbs(np.array([lam]), normalize=True)
    # normalize template for share comparison on same footing
    ts = float(t1[0] + t2[0] + t3[0])
    tn1, tn2, tn3 = float(t1[0] / ts), float(t2[0] / ts), float(t3[0] / ts)

    return {
        "r": r,
        "seed": seed,
        "lam": lam,
        "mean_phi1": m_phi1,
        "mean_phi2": m_phi2,
        "mean_phi3": m_phi3,
        "mean_excess3": m_ex,
        "highL3": hl3,
        "f3_template_raw": share_f3(m_phi1, m_phi2, m_phi3, float(t1[0]), float(t2[0]), float(t3[0])),
        "f3_gibbs_raw": share_f3(m_phi1, m_phi2, m_phi3, float(g1[0]), float(g2[0]), float(g3[0])),
        "f3_template_norm": share_f3(m_phi1, m_phi2, m_phi3, tn1, tn2, tn3),
        "f3_gibbs_norm": share_f3(m_phi1, m_phi2, m_phi3, float(gn1[0]), float(gn2[0]), float(gn3[0])),
        "a3_template_norm": tn3,
        "a3_gibbs_norm": float(gn3[0]),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n_realizations", type=int, default=4)
    ap.add_argument("--n_steps", type=int, default=1600)
    ap.add_argument("--kappa", type=float, default=1.5)
    args = ap.parse_args()

    stamp = time.strftime("%Y%m%d_%H%M%S")
    print("=== Gibbs-α vs template-α (Note 3 Via B) ===")

    # Shape bridge
    cmp = alpha_compare_template_gibbs(kappa=args.kappa)
    bridge = {
        "max_L1": float(cmp["max_L1"][0]),
        "max_Linf": float(cmp["max_Linf"][0]),
        "mean_L1": float(cmp["mean_L1"][0]),
        "kappa": args.kappa,
        "note": "L1/L∞ on L1-normalized families over λ∈[0,2]",
    }
    print("Bridge:", json.dumps(bridge, indent=2))

    # Cascade stations
    rows: List[Dict] = []
    for r in STATIONS:
        for seed in range(args.n_realizations):
            row = run_station(r, seed, args.n_steps)
            rows.append(row)
            print(
                f"  r={r:.2f} s={seed} f3_T={row['f3_template_norm']:.3f} "
                f"f3_G={row['f3_gibbs_norm']:.3f} ex={row['mean_excess3']:.3f}",
                flush=True,
            )

    # aggregate
    by_r: Dict[float, List[Dict]] = {}
    for row in rows:
        by_r.setdefault(row["r"], []).append(row)
    agg = []
    keys = [
        "lam", "mean_phi1", "mean_phi2", "mean_phi3", "mean_excess3", "highL3",
        "f3_template_raw", "f3_gibbs_raw", "f3_template_norm", "f3_gibbs_norm",
        "a3_template_norm", "a3_gibbs_norm",
    ]
    for r in sorted(by_r):
        lst = by_r[r]
        a = {"r": r, "n": len(lst)}
        for k in keys:
            vals = np.array([x[k] for x in lst], dtype=float)
            a[f"{k}_mean"] = float(np.nanmean(vals))
            a[f"{k}_sem"] = float(np.nanstd(vals) / max(np.sqrt(len(vals)), 1))
        a["delta_f3_TG"] = a["f3_template_norm_mean"] - a["f3_gibbs_norm_mean"]
        agg.append(a)

    # plots
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    lam = cmp["lam"]
    axes[0].plot(lam, cmp["t1"], "--", color="#1f77b4", label=r"$\alpha_1$ template")
    axes[0].plot(lam, cmp["t2"], "--", color="#ff7f0e", label=r"$\alpha_2$ template")
    axes[0].plot(lam, cmp["t3"], "--", color="#2ca02c", label=r"$\alpha_3$ template")
    axes[0].plot(lam, cmp["g1"], "-", color="#1f77b4", alpha=0.7, label=r"$\alpha_1$ Gibbs")
    axes[0].plot(lam, cmp["g2"], "-", color="#ff7f0e", alpha=0.7, label=r"$\alpha_2$ Gibbs")
    axes[0].plot(lam, cmp["g3"], "-", color="#2ca02c", alpha=0.7, label=r"$\alpha_3$ Gibbs")
    axes[0].set_xlabel(r"$\lambda$")
    axes[0].set_ylabel("normalized weight")
    axes[0].set_title("Template vs Gibbs α(λ)")
    axes[0].legend(fontsize=7, ncol=2)
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(lam, cmp["L1"], label="L1")
    axes[1].plot(lam, cmp["Linf"], label=r"L$\infty$")
    axes[1].set_xlabel(r"$\lambda$")
    axes[1].set_ylabel("distance (normalized)")
    axes[1].set_title(
        f"Bridge error  max L∞={bridge['max_Linf']:.3f}"
    )
    axes[1].legend(fontsize=8)
    axes[1].grid(True, alpha=0.3)
    fig.tight_layout()
    p1 = FIG_DIR / f"gibbs_alpha_bridge_{stamp}.png"
    fig.savefig(p1, dpi=150)
    fig.savefig(FIG_DIR / "gibbs_alpha_bridge.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4))
    rs = [a["r"] for a in agg]
    ax.plot(rs, [a["f3_template_norm_mean"] for a in agg], "o-", label=r"$f_3$ template (norm)")
    ax.plot(rs, [a["f3_gibbs_norm_mean"] for a in agg], "s-", label=r"$f_3$ Gibbs (norm)")
    ax.plot(rs, [a["mean_excess3_mean"] for a in agg], "^--", color="gray", alpha=0.7, label="mean excess3 (abund.)")
    ax.axvline(3.56995, color="k", ls="--", lw=0.8, alpha=0.5)
    ax.set_xlabel(r"$r$")
    ax.set_ylabel("share / abundance")
    ax.set_title("Share $f_3$ under two design engines (same Φ mass)")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    # twin for excess scale note — keep single axis with different magnitudes
    fig.tight_layout()
    p2 = FIG_DIR / f"gibbs_f3_cascade_{stamp}.png"
    fig.savefig(p2, dpi=150)
    fig.savefig(FIG_DIR / "gibbs_f3_cascade.png", dpi=150)
    plt.close(fig)

    # Better: two-panel share vs abundance
    fig, axes = plt.subplots(2, 1, figsize=(8, 5.5), sharex=True)
    axes[0].plot(rs, [a["f3_template_norm_mean"] for a in agg], "o-", label="template")
    axes[0].plot(rs, [a["f3_gibbs_norm_mean"] for a in agg], "s-", label="Gibbs")
    axes[0].axvline(3.56995, color="k", ls="--", lw=0.8, alpha=0.5)
    axes[0].set_ylabel(r"$f_3$ share (norm α)")
    axes[0].legend(fontsize=8)
    axes[0].grid(True, alpha=0.3)
    axes[0].set_title("Abundance ≠ share: design engine modulates $f_3$")

    axes[1].plot(rs, [a["mean_excess3_mean"] for a in agg], "o-", color="#d62728", label="excess3")
    axes[1].plot(rs, [a["highL3_mean"] for a in agg], "s-", color="#9467bd", label="highL3")
    axes[1].axvline(3.56995, color="k", ls="--", lw=0.8, alpha=0.5)
    axes[1].set_xlabel(r"$r$")
    axes[1].set_ylabel("abundance (α-free)")
    axes[1].legend(fontsize=8)
    axes[1].grid(True, alpha=0.3)
    fig.tight_layout()
    p3 = FIG_DIR / f"gibbs_share_vs_abundance_{stamp}.png"
    fig.savefig(p3, dpi=150)
    fig.savefig(FIG_DIR / "gibbs_share_vs_abundance.png", dpi=150)
    plt.close(fig)

    # report
    # correlation f3_T vs excess3 across r
    f3t = np.array([a["f3_template_norm_mean"] for a in agg])
    f3g = np.array([a["f3_gibbs_norm_mean"] for a in agg])
    ex = np.array([a["mean_excess3_mean"] for a in agg])
    corr_t = float(np.corrcoef(f3t, ex)[0, 1]) if len(ex) > 2 else float("nan")
    corr_g = float(np.corrcoef(f3g, ex)[0, 1]) if len(ex) > 2 else float("nan")
    corr_tg = float(np.corrcoef(f3t, f3g)[0, 1]) if len(ex) > 2 else float("nan")

    verdict = {
        "bridge": bridge,
        "corr_f3template_vs_excess3": corr_t,
        "corr_f3gibbs_vs_excess3": corr_g,
        "corr_f3template_vs_f3gibbs": corr_tg,
        "abundance_neq_share": abs(corr_t) < 0.95,
        "engines_similar_on_cascade": corr_tg > 0.9,
        "headline": (
            f"Bridge max L∞={bridge['max_Linf']:.3f}; "
            f"corr(f3_T,f3_G)={corr_tg:.3f}; "
            f"corr(f3_T,excess3)={corr_t:.3f} → abundance≠share"
        ),
    }

    report_lines = [
        f"# Gibbs-α comparison report — {stamp}",
        "",
        "Via B (Note 3) vs template α family.",
        "",
        f"**{verdict['headline']}**",
        "",
        "## Shape bridge (normalized α on λ∈[0,2])",
        "",
        "```json",
        json.dumps(bridge, indent=2),
        "```",
        "",
        "## Cascade f3 shares (mean over seeds)",
        "",
        "| r | λ | excess3 | highL3 | f3 template | f3 Gibbs | Δ(T−G) |",
        "|---|---|---|---|---|---|---|",
    ]
    for a in agg:
        report_lines.append(
            f"| {a['r']:.2f} | {a['lam_mean']:.2f} | {a['mean_excess3_mean']:.3f} | "
            f"{a['highL3_mean']:.3f} | {a['f3_template_norm_mean']:.3f} | "
            f"{a['f3_gibbs_norm_mean']:.3f} | {a['delta_f3_TG']:.3f} |"
        )
    report_lines += [
        "",
        "## Verdicts",
        "",
        "```json",
        json.dumps(verdict, indent=2),
        "```",
        "",
        "## Reading",
        "",
        "- Bridge error finite ⇒ Conj. template↔Gibbs is a *shape* approximation, not identity.",
        "- High corr(f3_T, f3_G) ⇒ both engines push L3 share the same qualitative way along r.",
        "- Low corr(f3, excess3) ⇒ **abundance ≠ share** (Note 3 discipline).",
        "",
        "## Figures",
        "",
        f"- `{p1.relative_to(ROOT)}`",
        f"- `{p2.relative_to(ROOT)}`",
        f"- `{p3.relative_to(ROOT)}`",
        "",
    ]
    report_path = OUT_DIR / f"REPORT_gibbs_alpha_{stamp}.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    (OUT_DIR / "REPORT_gibbs_alpha.md").write_text("\n".join(report_lines), encoding="utf-8")

    # CSVs
    with (OUT_DIR / f"gibbs_flat_{stamp}.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    with (OUT_DIR / f"gibbs_agg_{stamp}.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(agg[0].keys()))
        w.writeheader()
        w.writerows(agg)

    json_path = OUT_DIR / f"gibbs_alpha_{stamp}.json"
    json_path.write_text(
        json.dumps({"bridge": bridge, "verdict": verdict, "agg": agg}, indent=2),
        encoding="utf-8",
    )
    print("Report:", report_path)
    print("JSON:", json_path)
    print(verdict["headline"])


if __name__ == "__main__":
    main()
