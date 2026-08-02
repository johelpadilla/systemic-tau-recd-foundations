#!/usr/bin/env python3
"""
Dense Feigenbaum cascade r-sweep for Note 4 conjectures.

Reports along r:
  - A3 abundance: mean excess3, highL3 rate, mean Res_pair (strong L3)
  - Variability: std of excess3(t), std of Res_pair(t), std of |τ_s|(t)
  - Organization: mean |τ_s|, mean Φ1, mean Φ2
  - Classical EWS: variance, AC1 (channel-mean)

Stations (approx logistic period-doubling):
  S_k: period-2/4 windows; S_∞⁻ near accumulation; S_∞ ~ r_∞;
  S_ch developed chaos; S_win period-3 window.

Usage
-----
  python3 cascade_r_sweep.py --quick
  python3 cascade_r_sweep.py --n_realizations 8 --n_steps 2200
  python3 cascade_r_sweep.py --no-res   # skip expensive Res_pair

Outputs under Fundacion_RECD/results/cascade_sweep/ and figures/.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[1]  # Fundacion_RECD
NESTED = ROOT.parent / "Investigaciones" / "nested-recd" / "src"
sys.path.insert(0, str(NESTED))

from nested_recd import (  # noqa: E402
    compute_recd_from_conjunctions,
    compute_res_pair,
    generate_multivariate_symbols,
    high_level3_rate,
    regime_lambda_proxy,
    alpha_weights,
    DELTA_FEIGENBAUM,
)

OUT_DIR = ROOT / "results" / "cascade_sweep"
FIG_DIR = ROOT / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

# Logistic period-doubling landmarks (standard references)
R_PERIOD2 = 3.0
R_PERIOD4 = 3.449490
R_PERIOD8 = 3.544090
R_PERIOD16 = 3.564407
R_INF = 3.5699456
R_P3_WINDOW = 3.828427  # onset of period-3 window (approx)
DELTA = DELTA_FEIGENBAUM  # ≈ 4.6692


def logistic_coupled(
    n_steps: int,
    n_comp: int = 4,
    r: float = 3.8,
    coupling: float = 0.05,
    noise: float = 0.003,
    seed: int = 0,
    burn_in: int = 400,
) -> np.ndarray:
    """Diffusive weakly coupled logistic maps (Note 4 Def. coupled)."""
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


def kendall_tau_pair(a: np.ndarray, b: np.ndarray) -> float:
    """O(n²) Kendall τ for short windows (window≈13)."""
    n = len(a)
    if n < 3:
        return 0.0
    conc = disc = 0
    for i in range(n - 1):
        da = a[i + 1 :] - a[i]
        db = b[i + 1 :] - b[i]
        prod = da * db
        conc += int(np.sum(prod > 0))
        disc += int(np.sum(prod < 0))
    den = conc + disc
    return (conc - disc) / den if den else 0.0


def compute_tau_s(X: np.ndarray, window: int = 13, stride: int = 1) -> np.ndarray:
    """Mean pairwise Kendall τ over sliding windows (Systemic Tau proxy)."""
    T, N = X.shape
    out = np.full(T, np.nan)
    pairs = [(i, j) for i in range(N) for j in range(i + 1, N)]
    for t in range(window - 1, T, stride):
        w = X[t - window + 1 : t + 1]
        vals = [kendall_tau_pair(w[:, i], w[:, j]) for i, j in pairs]
        out[t] = float(np.mean(vals))
    return out


def classical_ews(X: np.ndarray) -> Tuple[float, float]:
    """Channel-mean variance and lag-1 autocorrelation (after demean)."""
    vars_ = []
    ac1s = []
    for i in range(X.shape[1]):
        x = X[:, i] - np.mean(X[:, i])
        v = float(np.var(x))
        vars_.append(v)
        if len(x) > 2 and v > 1e-15:
            ac1s.append(float(np.corrcoef(x[:-1], x[1:])[0, 1]))
        else:
            ac1s.append(0.0)
    return float(np.mean(vars_)), float(np.mean(ac1s))


def station_label(r: float) -> str:
    if r < R_PERIOD2:
        return "S_fixed"
    if r < R_PERIOD4:
        return "S_k_p2"
    if r < R_PERIOD8:
        return "S_k_p4"
    if r < R_PERIOD16:
        return "S_k_p8"
    if r < R_INF - 0.002:
        return "S_inf_minus"
    if abs(r - R_INF) <= 0.004:
        return "S_inf"
    if abs(r - R_P3_WINDOW) < 0.015:
        return "S_win_p3"
    if r >= 3.7:
        return "S_ch"
    return "S_post_acc"


def dense_r_grid(mode: str = "full") -> np.ndarray:
    """r values denser near accumulation and covering stations."""
    if mode == "quick":
        return np.array(
            [3.20, 3.40, 3.50, 3.55, 3.565, R_INF, 3.60, 3.70, 3.80, 3.85, 3.90]
        )
    # landmarks + uniform fill
    core = [
        3.10,
        3.20,
        3.30,
        3.40,
        R_PERIOD4,
        3.48,
        3.52,
        R_PERIOD8,
        3.555,
        R_PERIOD16,
        3.567,
        R_INF,
        3.575,
        3.60,
        3.65,
        3.70,
        3.75,
        3.80,
        R_P3_WINDOW,
        3.85,
        3.90,
        3.95,
    ]
    # densify near r_inf
    near = np.linspace(R_INF - 0.012, R_INF + 0.025, 10)
    grid = np.unique(np.round(np.concatenate([core, near]), 6))
    return grid[(grid >= 3.05) & (grid <= 3.98)]


def run_one(
    r: float,
    seed: int,
    n_steps: int,
    n_comp: int,
    coupling: float,
    noise: float,
    window: int,
    excess_thresh: float,
    compute_res: bool,
    res_stride: int,
) -> Dict:
    X = logistic_coupled(
        n_steps=n_steps,
        n_comp=n_comp,
        r=r,
        coupling=coupling,
        noise=noise,
        seed=seed,
    )
    var_mean, ac1_mean = classical_ews(X)
    tau_s = compute_tau_s(X, window=window, stride=1)

    # abundance metrics independent of α: use fixed λ=0 for clock; report raw excess3
    res = compute_recd_from_conjunctions(
        X,
        tau_s=tau_s,
        window_tau=window,
        compute_res=False,
        lam_override=0.0,
    )
    excess3 = res["excess3"]
    phi1 = res["phi1"]
    phi2 = res["phi2"]
    # align tau to symbol length
    T_eff = len(phi1)
    tau_al = tau_s[-T_eff:] if len(tau_s) >= T_eff else tau_s

    mean_ex = float(np.nanmean(excess3))
    std_ex = float(np.nanstd(excess3))
    hl3 = high_level3_rate(excess3, thresh=excess_thresh)
    mean_phi1 = float(np.nanmean(phi1))
    mean_phi2 = float(np.nanmean(phi2))
    mean_abs_tau = float(np.nanmean(np.abs(tau_al)))
    std_abs_tau = float(np.nanstd(np.abs(tau_al)))
    mean_tau = float(np.nanmean(tau_al))

    # share f3 under regime λ(r) (design engine; reported separately)
    lam_r = regime_lambda_proxy(float(r))
    a1, a2, a3 = alpha_weights(np.array([lam_r]))
    # pseudo-share: E[α3 Φ3_bin] / E[α·Φ] style using mean binary phi3
    phi3_bin = res["phi3"]
    phi3_safe = np.nan_to_num(phi3_bin, nan=0.0)
    c1 = float(a1[0] * mean_phi1)
    c2 = float(a2[0] * mean_phi2)
    c3 = float(a3[0] * np.nanmean(phi3_safe))
    tot = c1 + c2 + c3 + 1e-12
    f3 = c3 / tot

    mean_res = std_res = np.nan
    if compute_res:
        S = res["S"]
        rp = compute_res_pair(S, window=window, stride=res_stride)
        mean_res = float(np.nanmean(rp))
        std_res = float(np.nanstd(rp))

    return {
        "r": float(r),
        "seed": int(seed),
        "station": station_label(r),
        "mean_excess3": mean_ex,
        "std_excess3": std_ex,
        "highL3": hl3,
        "mean_res_pair": mean_res,
        "std_res_pair": std_res,
        "mean_phi1": mean_phi1,
        "mean_phi2": mean_phi2,
        "mean_abs_tau": mean_abs_tau,
        "std_abs_tau": std_abs_tau,
        "mean_tau": mean_tau,
        "var_classical": var_mean,
        "ac1_classical": ac1_mean,
        "lam_regime": float(lam_r),
        "f3_share": float(f3),
        "alpha3": float(a3[0]),
    }


def aggregate(rows: List[Dict]) -> List[Dict]:
    """Mean±sem per r."""
    by_r: Dict[float, List[Dict]] = {}
    for row in rows:
        by_r.setdefault(row["r"], []).append(row)
    out = []
    keys = [
        "mean_excess3",
        "std_excess3",
        "highL3",
        "mean_res_pair",
        "std_res_pair",
        "mean_phi1",
        "mean_phi2",
        "mean_abs_tau",
        "std_abs_tau",
        "mean_tau",
        "var_classical",
        "ac1_classical",
        "f3_share",
    ]
    for r in sorted(by_r):
        lst = by_r[r]
        rec = {
            "r": r,
            "station": lst[0]["station"],
            "n": len(lst),
            "lam_regime": lst[0]["lam_regime"],
            "alpha3": lst[0]["alpha3"],
        }
        for k in keys:
            vals = np.array([x[k] for x in lst], dtype=float)
            rec[f"{k}_mean"] = float(np.nanmean(vals))
            rec[f"{k}_std"] = float(np.nanstd(vals))
            rec[f"{k}_sem"] = float(np.nanstd(vals) / max(np.sqrt(np.sum(np.isfinite(vals))), 1))
        out.append(rec)
    return out


def test_conjectures(agg: List[Dict]) -> Dict:
    """Operational checks for Note 4 Conj. mono / rinf / nontriv."""
    def pick(station_prefix: str) -> Optional[Dict]:
        cands = [a for a in agg if a["station"].startswith(station_prefix)]
        if not cands:
            return None
        # prefer denser stations
        return cands[len(cands) // 2]

    # S_k period-2-ish: r near 3.2–3.3
    sk = min(agg, key=lambda a: abs(a["r"] - 3.30))
    sch = min(agg, key=lambda a: abs(a["r"] - 3.85))
    sinf = min(agg, key=lambda a: abs(a["r"] - R_INF))

    mono_ex = sch["mean_excess3_mean"] > sk["mean_excess3_mean"]
    mono_hl = sch["highL3_mean"] > sk["highL3_mean"]
    mono_res = True
    if np.isfinite(sch["mean_res_pair_mean"]) and np.isfinite(sk["mean_res_pair_mean"]):
        mono_res = sch["mean_res_pair_mean"] > sk["mean_res_pair_mean"]

    # Conj rinf: variability of L3 / |τ| local max near r_inf vs deep chaos plateau
    # Compare std_excess3 and std_abs_tau at sinf vs sch
    rinf_var_ex = sinf["std_excess3_mean"]
    ch_var_ex = sch["std_excess3_mean"]
    rinf_var_tau = sinf["std_abs_tau_mean"]
    ch_mean_ex = sch["mean_excess3_mean"]
    sinf_mean_ex = sinf["mean_excess3_mean"]

    # nontriv: ΔA3 not just rescaling of Δ|τ| — sign mismatch check on sk→sch
    dA3 = sch["mean_excess3_mean"] - sk["mean_excess3_mean"]
    dTau = sch["mean_abs_tau_mean"] - sk["mean_abs_tau_mean"]
    # weaker operational: correlation of A3(r) vs |τ|(r) across grid not ±1
    a3 = np.array([a["mean_excess3_mean"] for a in agg])
    at = np.array([a["mean_abs_tau_mean"] for a in agg])
    if np.std(a3) > 1e-9 and np.std(at) > 1e-9:
        corr = float(np.corrcoef(a3, at)[0, 1])
    else:
        corr = float("nan")

    return {
        "conj_mono": {
            "excess3_chaos_gt_pre": mono_ex,
            "highL3_chaos_gt_pre": mono_hl,
            "res_pair_chaos_gt_pre": mono_res,
            "pre_r": sk["r"],
            "chaos_r": sch["r"],
            "pre_excess3": sk["mean_excess3_mean"],
            "chaos_excess3": sch["mean_excess3_mean"],
            "pre_highL3": sk["highL3_mean"],
            "chaos_highL3": sch["highL3_mean"],
            "pre_res_pair": sk["mean_res_pair_mean"],
            "chaos_res_pair": sch["mean_res_pair_mean"],
        },
        "conj_rinf": {
            "r_inf_used": sinf["r"],
            "std_excess3_at_rinf": rinf_var_ex,
            "std_excess3_at_chaos": ch_var_ex,
            "std_abs_tau_at_rinf": rinf_var_tau,
            "std_abs_tau_at_chaos": sch["std_abs_tau_mean"],
            "mean_excess3_at_rinf": sinf_mean_ex,
            "mean_excess3_at_chaos": ch_mean_ex,
            "mean_ex_chaos_ge_rinf": ch_mean_ex >= sinf_mean_ex - 1e-6,
            "note": "Evidence only; local max of variability needs denser comparison to neighbors",
        },
        "conj_nontriv": {
            "delta_A3_pre_to_chaos": dA3,
            "delta_abs_tau_pre_to_chaos": dTau,
            "corr_A3_vs_abs_tau_across_r": corr,
            "not_perfect_proxy": bool(np.isfinite(corr) and abs(corr) < 0.95),
        },
        "landmarks": {
            "R_INF": R_INF,
            "DELTA": DELTA,
            "R_P3": R_P3_WINDOW,
        },
    }


def plot_results(agg: List[Dict], stamp: str) -> List[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rs = np.array([a["r"] for a in agg])
    paths = []

    def series(key):
        return np.array([a[f"{key}_mean"] for a in agg])

    def err(key):
        return np.array([a[f"{key}_sem"] for a in agg])

    # Panel 1: A3 abundance
    fig, axes = plt.subplots(3, 1, figsize=(9, 9), sharex=True)
    for ax, key, ylab, color in [
        (axes[0], "mean_excess3", r"mean excess$^3$ (proxy A3)", "#1f77b4"),
        (axes[1], "highL3", r"highL3 rate (excess$^3$>1.75)", "#d62728"),
        (axes[2], "mean_res_pair", r"mean Res$_{\mathrm{pair}}$ (strong A3)", "#2ca02c"),
    ]:
        y = series(key)
        e = err(key)
        ax.errorbar(rs, y, yerr=e, fmt="o-", color=color, ms=3.5, lw=1.2, capsize=2)
        ax.axvline(R_INF, color="k", ls="--", lw=0.9, alpha=0.7, label=r"$r_\infty$")
        ax.axvline(R_P3_WINDOW, color="gray", ls=":", lw=0.9, alpha=0.7, label=r"P3 win")
        ax.set_ylabel(ylab)
        ax.grid(True, alpha=0.3)
    axes[0].legend(loc="best", fontsize=8)
    axes[-1].set_xlabel(r"logistic parameter $r$")
    fig.suptitle("Level-3 abundance along the Feigenbaum cascade", fontsize=12)
    fig.tight_layout()
    p1 = FIG_DIR / f"cascade_A3_vs_r_{stamp}.png"
    fig.savefig(p1, dpi=160)
    plt.close(fig)
    paths.append(p1)

    # Panel 2: variability + dual framing
    fig, axes = plt.subplots(3, 1, figsize=(9, 9), sharex=True)
    for ax, key, ylab, color in [
        (axes[0], "std_excess3", r"std$_t$ excess$^3$ (temporal var)", "#9467bd"),
        (axes[1], "std_abs_tau", r"std$_t$ $|\tau_s|$", "#8c564b"),
        (axes[2], "mean_abs_tau", r"mean $|\tau_s|$", "#e377c2"),
    ]:
        y = series(key)
        e = err(key)
        ax.errorbar(rs, y, yerr=e, fmt="o-", color=color, ms=3.5, lw=1.2, capsize=2)
        ax.axvline(R_INF, color="k", ls="--", lw=0.9, alpha=0.7)
        ax.axvline(R_P3_WINDOW, color="gray", ls=":", lw=0.9, alpha=0.7)
        ax.set_ylabel(ylab)
        ax.grid(True, alpha=0.3)
    axes[-1].set_xlabel(r"logistic parameter $r$")
    fig.suptitle(r"Variability near $r_\infty$ and dual $|\tau_s|$", fontsize=12)
    fig.tight_layout()
    p2 = FIG_DIR / f"cascade_variability_tau_{stamp}.png"
    fig.savefig(p2, dpi=160)
    plt.close(fig)
    paths.append(p2)

    # Panel 3: classical EWS vs A3
    fig, axes = plt.subplots(2, 1, figsize=(9, 6.5), sharex=True)
    axes[0].errorbar(rs, series("var_classical"), yerr=err("var_classical"),
                     fmt="o-", color="#17becf", ms=3.5, label="var (classical)")
    axes[0].errorbar(rs, series("ac1_classical"), yerr=err("ac1_classical"),
                     fmt="s-", color="#bcbd22", ms=3.5, label="AC1 (classical)")
    axes[0].axvline(R_INF, color="k", ls="--", lw=0.9, alpha=0.7)
    axes[0].legend(fontsize=8)
    axes[0].set_ylabel("classical EWS")
    axes[0].grid(True, alpha=0.3)
    # normalize A3 and var for visual comparison of shapes
    a3 = series("mean_excess3")
    v = series("var_classical")
    a3n = (a3 - a3.min()) / (a3.max() - a3.min() + 1e-12)
    vn = (v - v.min()) / (v.max() - v.min() + 1e-12)
    axes[1].plot(rs, a3n, "o-", color="#1f77b4", ms=3.5, label="excess3 (norm)")
    axes[1].plot(rs, vn, "^-", color="#17becf", ms=3.5, label="var (norm)")
    axes[1].axvline(R_INF, color="k", ls="--", lw=0.9, alpha=0.7)
    axes[1].legend(fontsize=8)
    axes[1].set_ylabel("normalized")
    axes[1].set_xlabel(r"logistic parameter $r$")
    axes[1].grid(True, alpha=0.3)
    fig.suptitle("Classical EWS vs Level-3 proxy (distinct measurement objects)", fontsize=12)
    fig.tight_layout()
    p3 = FIG_DIR / f"cascade_ews_vs_A3_{stamp}.png"
    fig.savefig(p3, dpi=160)
    plt.close(fig)
    paths.append(p3)

    # Panel 4: Φ1/Φ2/f3
    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.errorbar(rs, series("mean_phi1"), yerr=err("mean_phi1"), fmt="o-", ms=3, label=r"mean $\Phi_1$")
    ax.errorbar(rs, series("mean_phi2"), yerr=err("mean_phi2"), fmt="s-", ms=3, label=r"mean $\Phi_2$")
    ax.errorbar(rs, series("f3_share"), yerr=err("f3_share"), fmt="^-", ms=3, label=r"$f_3$ share (α(λ(r)))")
    ax.axvline(R_INF, color="k", ls="--", lw=0.9, alpha=0.7)
    ax.legend(fontsize=8)
    ax.set_xlabel(r"$r$")
    ax.set_ylabel("level / share")
    ax.set_title("Depth channels and share (abundance ≠ share)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    p4 = FIG_DIR / f"cascade_phi_f3_{stamp}.png"
    fig.savefig(p4, dpi=160)
    plt.close(fig)
    paths.append(p4)

    return paths


def write_markdown_report(agg: List[Dict], tests: Dict, paths: List[Path], stamp: str, meta: Dict) -> Path:
    md = OUT_DIR / f"REPORT_cascade_sweep_{stamp}.md"
    lines = [
        f"# Cascade r-sweep report — {stamp}",
        "",
        "Synthetic evidence for **Note 4** conjectures (Feigenbaum conjunction structure).",
        "Not theorems. nested-recd pipeline; weakly coupled logistic maps.",
        "",
        "## Configuration",
        "",
        "```json",
        json.dumps(meta, indent=2),
        "```",
        "",
        "## Conjecture checks (operational)",
        "",
        "```json",
        json.dumps(tests, indent=2),
        "```",
        "",
        "## Summary table (selected columns)",
        "",
        "| r | station | excess3 | highL3 | Res_pair | std_ex | |τ| | var | AC1 | f3 |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for a in agg:
        lines.append(
            f"| {a['r']:.5f} | {a['station']} | "
            f"{a['mean_excess3_mean']:.4f} | {a['highL3_mean']:.3f} | "
            f"{a['mean_res_pair_mean']:.4f} | {a['std_excess3_mean']:.4f} | "
            f"{a['mean_abs_tau_mean']:.3f} | {a['var_classical_mean']:.4f} | "
            f"{a['ac1_classical_mean']:.3f} | {a['f3_share_mean']:.3f} |"
        )
    lines += [
        "",
        "## Figures",
        "",
    ]
    for p in paths:
        rel = p.relative_to(ROOT) if p.is_relative_to(ROOT) else p
        lines.append(f"- `{rel}`")
    lines += [
        "",
        "## Reading guide",
        "",
        "- **Conj. mono**: chaos A3 > period-2/pre A3 (excess3 / highL3 / Res_pair).",
        "- **Conj. rinf**: look at `std_excess3` / `std_abs_tau` peaking near r_∞; mean A3 plateau more in S_ch.",
        "- **Conj. nontriv**: corr(A3(r), |τ|(r)) far from ±1; classical var shape ≠ A3 shape.",
        "- **f3** uses α(λ(r)) design engine — report separately from abundance.",
        "",
    ]
    md.write_text("\n".join(lines), encoding="utf-8")
    return md


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="Fewer r points and realizations")
    ap.add_argument("--n_realizations", type=int, default=None)
    ap.add_argument("--n_steps", type=int, default=None)
    ap.add_argument("--n_comp", type=int, default=4)
    ap.add_argument("--coupling", type=float, default=0.05)
    ap.add_argument("--noise", type=float, default=0.003)
    ap.add_argument("--window", type=int, default=13)
    ap.add_argument("--excess_thresh", type=float, default=1.75)
    ap.add_argument("--no-res", action="store_true", help="Skip Res_pair (faster)")
    ap.add_argument("--res-stride", type=int, default=8)
    args = ap.parse_args()

    mode = "quick" if args.quick else "full"
    n_real = args.n_realizations if args.n_realizations is not None else (3 if args.quick else 6)
    n_steps = args.n_steps if args.n_steps is not None else (1200 if args.quick else 2200)
    compute_res = not args.no_res
    r_grid = dense_r_grid(mode)

    meta = {
        "mode": mode,
        "n_realizations": n_real,
        "n_steps": n_steps,
        "n_comp": args.n_comp,
        "coupling": args.coupling,
        "noise": args.noise,
        "window": args.window,
        "excess_thresh": args.excess_thresh,
        "compute_res": compute_res,
        "res_stride": args.res_stride,
        "r_grid": r_grid.tolist(),
        "nested_recd_path": str(NESTED),
        "R_INF": R_INF,
        "DELTA": DELTA,
    }

    print("=== Feigenbaum cascade r-sweep (Note 4) ===")
    print(json.dumps({k: v for k, v in meta.items() if k != "r_grid"}, indent=2))
    print(f"r grid ({len(r_grid)} pts): {r_grid}")

    rows: List[Dict] = []
    t0 = time.time()
    total = len(r_grid) * n_real
    done = 0
    for r in r_grid:
        for k in range(n_real):
            seed = 10_000 + int(r * 10_000) + k * 17
            row = run_one(
                r=float(r),
                seed=seed,
                n_steps=n_steps,
                n_comp=args.n_comp,
                coupling=args.coupling,
                noise=args.noise,
                window=args.window,
                excess_thresh=args.excess_thresh,
                compute_res=compute_res,
                res_stride=args.res_stride,
            )
            rows.append(row)
            done += 1
            if done % max(1, total // 20) == 0 or done == total:
                print(
                    f"  [{done}/{total}] r={r:.5f} seed={seed} "
                    f"ex={row['mean_excess3']:.3f} hl3={row['highL3']:.2f} "
                    f"res={row['mean_res_pair']:.4f} |t|={row['mean_abs_tau']:.3f}"
                )

    stamp = time.strftime("%Y%m%d_%H%M%S")
    agg = aggregate(rows)
    tests = test_conjectures(agg)

    flat_csv = OUT_DIR / f"cascade_flat_{stamp}.csv"
    with open(flat_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    agg_csv = OUT_DIR / f"cascade_agg_{stamp}.csv"
    with open(agg_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(agg[0].keys()))
        w.writeheader()
        w.writerows(agg)

    json_path = OUT_DIR / f"cascade_results_{stamp}.json"
    with open(json_path, "w") as f:
        json.dump({"meta": meta, "aggregate": agg, "tests": tests, "n_rows": len(rows)}, f, indent=2)

    paths = plot_results(agg, stamp)
    # stable copies for paper
    import shutil

    stable = {
        f"cascade_A3_vs_r_{stamp}.png": "cascade_A3_vs_r.png",
        f"cascade_variability_tau_{stamp}.png": "cascade_variability_tau.png",
        f"cascade_ews_vs_A3_{stamp}.png": "cascade_ews_vs_A3.png",
        f"cascade_phi_f3_{stamp}.png": "cascade_phi_f3.png",
    }
    for src_name, dst_name in stable.items():
        src = FIG_DIR / src_name
        if src.exists():
            shutil.copy2(src, FIG_DIR / dst_name)

    report = write_markdown_report(agg, tests, paths, stamp, meta)

    print("\n=== CONJECTURE CHECKS ===")
    print(json.dumps(tests, indent=2))
    print(f"\nFlat CSV: {flat_csv}")
    print(f"Agg CSV:  {agg_csv}")
    print(f"JSON:     {json_path}")
    print(f"Report:   {report}")
    for p in paths:
        print(f"Figure:   {p}")
    print(f"Elapsed:  {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
