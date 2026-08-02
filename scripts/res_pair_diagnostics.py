#!/usr/bin/env python3
"""
Diagnose Res_pair collapse near r_∞ on the Feigenbaum cascade grid.

Hypothesis battery (Note 4 scholium):
  H1  Window bias: longer w restores Res_pair near accumulation / chaos.
  H2  Alphabet sparsity: near r_∞ support explodes → KL under-estimated
      (few repeats per cell ⇒ P nearly saturates pairwise constraints).
  H3  IPF non-convergence: residual fails because IPF max_dev stays large.
  H4  True structure vs proxy: Res_pair tracks TC residual; excess3 does not
      share the same trajectory (already known); document TC(P) vs TC(P^(2)).
  H5  Period-2 peak is *not* pure artifact: with long w, Res stays high at
      S_k period-2 (synchronized few-state joint violates pairwise maxent).

Key stations: r ∈ {3.20, 3.30, 3.45, 3.57, 3.70, 3.85}
Windows:      w ∈ {13, 26, 52, 104}
Plus full-series (one long block) Res as asymptotic probe.

Outputs: results/res_pair_diag/, figures/res_pair_diag_*.png, REPORT.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
NESTED = ROOT.parent / "Investigaciones" / "nested-recd" / "src"
sys.path.insert(0, str(NESTED))

from nested_recd import (  # noqa: E402
    generate_multivariate_symbols,
    pairwise_maxent_ipf,
    kl_divergence,
    compute_res_pair,
)
from nested_recd.ordinal_levels import _empirical_joint_table  # noqa: E402

OUT_DIR = ROOT / "results" / "res_pair_diag"
FIG_DIR = ROOT / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

STATIONS = [
    (3.20, "S_k_p2"),
    (3.30, "S_k_p2"),
    (3.45, "S_k_p4"),
    (3.57, "S_inf"),
    (3.70, "S_ch"),
    (3.85, "S_ch"),
]
WINDOWS = [13, 26, 52, 104]


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


def entropy_bits(p: np.ndarray) -> float:
    p = p.ravel()
    p = p[p > 0]
    return float(-np.sum(p * np.log2(p)))


def total_correlation(p: np.ndarray) -> float:
    """TC = sum_i H(X_i) - H(X)."""
    N = p.ndim
    h_joint = entropy_bits(p)
    h_marg = 0.0
    for i in range(N):
        axes = tuple(a for a in range(N) if a != i)
        mi = p.sum(axis=axes)
        h_marg += entropy_bits(mi)
    return h_marg - h_joint


def ipf_with_diag(
    p_emp: np.ndarray, max_iter: int = 200, tol: float = 1e-10
) -> Tuple[np.ndarray, int, float]:
    """IPF returning (p2, n_iter, final_max_dev)."""
    p_emp = np.asarray(p_emp, dtype=float)
    if p_emp.ndim < 2:
        return p_emp.copy(), 0, 0.0
    N = p_emp.ndim
    marg1 = []
    for i in range(N):
        axes = tuple(a for a in range(N) if a != i)
        marg1.append(p_emp.sum(axis=axes))
    p = marg1[0]
    for i in range(1, N):
        p = p[..., None] * marg1[i]
    p = np.broadcast_to(p, p_emp.shape).astype(float).copy()

    def pair_marg(pp, i, j):
        axes = tuple(a for a in range(N) if a not in (i, j))
        m = pp.sum(axis=axes) if axes else pp.copy()
        if i > j:
            m = m.T
        return m

    targets = {(i, j): pair_marg(p_emp, i, j) for i in range(N) for j in range(i + 1, N)}
    final_dev = 0.0
    n_it = 0
    for it in range(max_iter):
        n_it = it + 1
        max_dev = 0.0
        for i in range(N):
            for j in range(i + 1, N):
                cur = pair_marg(p, i, j)
                tgt = targets[(i, j)]
                ratio = np.ones_like(tgt)
                mask = cur > 0
                ratio[mask] = tgt[mask] / cur[mask]
                shape = [1] * N
                shape[i] = p.shape[i]
                shape[j] = p.shape[j]
                p = p * ratio.reshape(shape)
                s = p.sum()
                if s > 0:
                    p /= s
                max_dev = max(max_dev, float(np.max(np.abs(cur - tgt))))
        final_dev = max_dev
        if max_dev < tol:
            break
    return p, n_it, final_dev


def window_diagnostics(win: np.ndarray) -> Dict[str, float]:
    """Rich diagnostics on one (w, N) symbol window."""
    win = np.asarray(win)
    w, N = win.shape
    # unique joint patterns
    rows = [tuple(win[t]) for t in range(w)]
    from collections import Counter

    cnt = Counter(rows)
    n_unique = len(cnt)
    max_mult = max(cnt.values()) if cnt else 0
    # per-channel alphabet
    k_i = [len(np.unique(win[:, i])) for i in range(N)]
    alph_prod = int(np.prod(k_i)) if k_i else 1

    try:
        p_emp, _ = _empirical_joint_table(win)
    except ValueError:
        return {
            "res_pair": np.nan,
            "n_unique_joint": float(n_unique),
            "max_mult": float(max_mult),
            "sparsity": float(n_unique) / max(w, 1),
            "alph_prod": float(alph_prod),
            "fill_frac": float(n_unique) / max(alph_prod, 1),
            "H_joint": np.nan,
            "TC": np.nan,
            "TC_pair": np.nan,
            "Res_TC": np.nan,
            "ipf_iters": np.nan,
            "ipf_dev": np.nan,
            "mean_k_i": float(np.mean(k_i)),
        }

    p2, n_it, dev = ipf_with_diag(p_emp)
    res = kl_divergence(p_emp, p2)
    H = entropy_bits(p_emp)
    tc = total_correlation(p_emp)
    tc2 = total_correlation(p2)
    # TC residual beyond pairwise = TC - TC(P^(2)); should ≈ Res when
    # P^(2) is the true I-projection (exact for exponential family).
    return {
        "res_pair": float(res),
        "n_unique_joint": float(n_unique),
        "max_mult": float(max_mult),
        "sparsity": float(n_unique) / max(w, 1),
        "alph_prod": float(alph_prod),
        "fill_frac": float(n_unique) / max(alph_prod, 1),
        "H_joint": float(H),
        "TC": float(tc),
        "TC_pair": float(tc2),
        "Res_TC": float(tc - tc2),
        "ipf_iters": float(n_it),
        "ipf_dev": float(dev),
        "mean_k_i": float(np.mean(k_i)),
    }


def sliding_diag(
    S: np.ndarray, window: int, stride: int
) -> Dict[str, float]:
    T, N = S.shape
    keys = [
        "res_pair",
        "n_unique_joint",
        "max_mult",
        "sparsity",
        "alph_prod",
        "fill_frac",
        "H_joint",
        "TC",
        "TC_pair",
        "Res_TC",
        "ipf_iters",
        "ipf_dev",
        "mean_k_i",
    ]
    acc = {k: [] for k in keys}
    for t in range(window - 1, T, stride):
        d = window_diagnostics(S[t - window + 1 : t + 1])
        for k in keys:
            acc[k].append(d[k])
    out = {}
    for k in keys:
        arr = np.asarray(acc[k], dtype=float)
        out[f"mean_{k}"] = float(np.nanmean(arr))
        out[f"std_{k}"] = float(np.nanstd(arr))
        out[f"frac_res_lt_1e-3"] = (
            float(np.mean(arr < 1e-3)) if k == "res_pair" else out.get(f"frac_res_lt_1e-3", np.nan)
        )
    # fix frac for res only
    rarr = np.asarray(acc["res_pair"], dtype=float)
    out["frac_res_lt_1e-3"] = float(np.mean(rarr < 1e-3))
    out["frac_res_lt_1e-2"] = float(np.mean(rarr < 1e-2))
    out["n_windows"] = float(len(rarr))
    return out


def full_series_diag(S: np.ndarray, max_rows: int = 800) -> Dict[str, float]:
    """One-shot Res on a long contiguous block (asymptotic probe)."""
    block = S[-max_rows:] if len(S) > max_rows else S
    d = window_diagnostics(block)
    return {f"full_{k}": v for k, v in d.items()}


def run_one(
    r: float,
    station: str,
    seed: int,
    n_steps: int,
    n_comp: int,
    coupling: float,
    noise: float,
    windows: List[int],
    stride: int,
) -> List[Dict]:
    X = logistic_coupled(
        n_steps=n_steps,
        n_comp=n_comp,
        r=r,
        coupling=coupling,
        noise=noise,
        seed=seed,
    )
    S = generate_multivariate_symbols(X, m=3, delay=1)
    rows = []
    full = full_series_diag(S, max_rows=min(800, len(S)))
    for w in windows:
        sd = sliding_diag(S, window=w, stride=max(stride, w // 4))
        row = {
            "r": float(r),
            "station": station,
            "seed": int(seed),
            "window": int(w),
            **sd,
            **full,
        }
        rows.append(row)
    return rows


def aggregate(rows: List[Dict]) -> List[Dict]:
    """Mean over seeds for each (r, window)."""
    groups: Dict[Tuple[float, int], List[Dict]] = {}
    for row in rows:
        groups.setdefault((row["r"], row["window"]), []).append(row)
    out = []
    metric_keys = [k for k in rows[0] if k not in ("r", "station", "seed", "window")]
    for (r, w), lst in sorted(groups.items()):
        agg = {
            "r": r,
            "window": w,
            "station": lst[0]["station"],
            "n_seeds": len(lst),
        }
        for k in metric_keys:
            vals = np.array([x[k] for x in lst], dtype=float)
            agg[f"{k}_mean"] = float(np.nanmean(vals))
            agg[f"{k}_sem"] = float(np.nanstd(vals) / max(np.sqrt(len(vals)), 1))
        out.append(agg)
    return out


def _cmap(ws: List[int]) -> Dict[int, str]:
    base = {13: "#1f77b4", 26: "#ff7f0e", 52: "#2ca02c", 104: "#d62728"}
    fallback = ["#9467bd", "#8c564b", "#e377c2", "#7f7f7f"]
    out = {}
    fi = 0
    for w in ws:
        if w in base:
            out[w] = base[w]
        else:
            out[w] = fallback[fi % len(fallback)]
            fi += 1
    return out


def plot_results(agg: List[Dict], stamp: str) -> List[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    paths = []
    rs = sorted({a["r"] for a in agg})
    ws = sorted({a["window"] for a in agg})
    colors = _cmap(ws)
    w_lo, w_hi = ws[0], ws[-1]

    def fetch(r, w, key):
        return next(a for a in agg if a["r"] == r and a["window"] == w)[key]

    # Fig A: Res_pair vs r for each window
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    for w in ws:
        xs = rs
        ys = [fetch(r, w, "mean_res_pair_mean") for r in rs]
        es = [fetch(r, w, "mean_res_pair_sem") for r in rs]
        ax.errorbar(
            xs, ys, yerr=es, marker="o", ms=4, lw=1.4,
            label=f"w={w}", color=colors[w], capsize=2,
        )
    ax.axvline(3.56995, color="k", ls="--", lw=0.8, alpha=0.6, label=r"$r_\infty$")
    ax.set_xlabel(r"logistic $r$")
    ax.set_ylabel(r"mean $\mathrm{Res}_{\mathrm{pair}}$")
    ax.set_title(r"H1 — Window length vs $\mathrm{Res}_{\mathrm{pair}}$ collapse")
    ax.legend(fontsize=8, ncol=2)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    p = FIG_DIR / f"res_pair_diag_window_{stamp}.png"
    fig.savefig(p, dpi=150)
    fig.savefig(FIG_DIR / "res_pair_diag_window.png", dpi=150)
    plt.close(fig)
    paths.append(p)

    # Fig B: sparsity / n_unique
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.8), sharex=True)
    for ax, metric, ylab in [
        (axes[0], "mean_sparsity_mean", r"sparsity = unique/w"),
        (axes[1], "mean_n_unique_joint_mean", r"mean unique joint patterns"),
    ]:
        for w in [w_lo, w_hi]:
            ys = [fetch(r, w, metric) for r in rs]
            ax.plot(rs, ys, "o-", ms=4, label=f"w={w}", color=colors[w])
        ax.axvline(3.56995, color="k", ls="--", lw=0.8, alpha=0.6)
        ax.set_xlabel(r"$r$")
        ax.set_ylabel(ylab)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
    fig.suptitle("H2 — Alphabet / support sparsity along cascade", fontsize=11)
    fig.tight_layout()
    p = FIG_DIR / f"res_pair_diag_sparsity_{stamp}.png"
    fig.savefig(p, dpi=150)
    fig.savefig(FIG_DIR / "res_pair_diag_sparsity.png", dpi=150)
    plt.close(fig)
    paths.append(p)

    # Fig C: mechanisms
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.6))
    for w in ws:
        xs = [a["mean_sparsity_mean"] for a in agg if a["window"] == w]
        ys = [a["mean_res_pair_mean"] for a in agg if a["window"] == w]
        axes[0].scatter(xs, ys, s=40, label=f"w={w}", color=colors[w], alpha=0.85)
    axes[0].set_xlabel("sparsity (unique/w)")
    axes[0].set_ylabel(r"mean $\mathrm{Res}_{\mathrm{pair}}$")
    axes[0].set_title("Res vs sparsity")
    axes[0].legend(fontsize=7)
    axes[0].grid(True, alpha=0.3)

    for w in [w_lo, w_hi]:
        ys = [fetch(r, w, "mean_Res_TC_mean") for r in rs]
        axes[1].plot(rs, ys, "o-", ms=4, label=f"w={w}", color=colors[w])
    axes[1].axvline(3.56995, color="k", ls="--", lw=0.8, alpha=0.6)
    axes[1].set_xlabel(r"$r$")
    axes[1].set_ylabel(r"TC − TC($P^{(2)}$)")
    axes[1].set_title("H4 — TC residual")
    axes[1].legend(fontsize=8)
    axes[1].grid(True, alpha=0.3)

    for w in [w_lo, w_hi]:
        ys = [fetch(r, w, "mean_ipf_dev_mean") for r in rs]
        axes[2].semilogy(rs, ys, "o-", ms=4, label=f"w={w}", color=colors[w])
    axes[2].axvline(3.56995, color="k", ls="--", lw=0.8, alpha=0.6)
    axes[2].set_xlabel(r"$r$")
    axes[2].set_ylabel("IPF final max_dev")
    axes[2].set_title("H3 — IPF convergence")
    axes[2].legend(fontsize=8)
    axes[2].grid(True, alpha=0.3)

    fig.tight_layout()
    p = FIG_DIR / f"res_pair_diag_mechanisms_{stamp}.png"
    fig.savefig(p, dpi=150)
    fig.savefig(FIG_DIR / "res_pair_diag_mechanisms.png", dpi=150)
    plt.close(fig)
    paths.append(p)

    # Fig D: full-block
    fig, ax = plt.subplots(figsize=(8, 4))
    y_full = [fetch(r, w_lo, "full_res_pair_mean") for r in rs]
    y_lo = [fetch(r, w_lo, "mean_res_pair_mean") for r in rs]
    y_hi = [fetch(r, w_hi, "mean_res_pair_mean") for r in rs]
    ax.plot(rs, y_lo, "o-", label=f"windowed w={w_lo}", color=colors[w_lo])
    ax.plot(rs, y_hi, "s-", label=f"windowed w={w_hi}", color=colors[w_hi])
    ax.plot(rs, y_full, "^-", label="full-block (~800)", color="#9467bd")
    ax.axvline(3.56995, color="k", ls="--", lw=0.8, alpha=0.6)
    ax.set_xlabel(r"$r$")
    ax.set_ylabel(r"$\mathrm{Res}_{\mathrm{pair}}$")
    ax.set_title("Windowed vs full-block residual")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    p = FIG_DIR / f"res_pair_diag_fullblock_{stamp}.png"
    fig.savefig(p, dpi=150)
    fig.savefig(FIG_DIR / "res_pair_diag_fullblock.png", dpi=150)
    plt.close(fig)
    paths.append(p)

    return paths


def hypothesis_verdict(agg: List[Dict]) -> Dict:
    """Operational tests of H1–H5. Uses min window (typ. 13) and max available w."""
    ws = sorted({a["window"] for a in agg})
    w_lo, w_hi = ws[0], ws[-1]

    def get(r, w, key):
        m = next(a for a in agg if abs(a["r"] - r) < 1e-9 and a["window"] == w)
        return m[key]

    r_p2, r_inf, r_ch = 3.20, 3.57, 3.85
    res_inf_lo = get(r_inf, w_lo, "mean_res_pair_mean")
    res_inf_hi = get(r_inf, w_hi, "mean_res_pair_mean")
    res_ch_lo = get(r_ch, w_lo, "mean_res_pair_mean")
    res_ch_hi = get(r_ch, w_hi, "mean_res_pair_mean")
    res_p2_lo = get(r_p2, w_lo, "mean_res_pair_mean")
    res_p2_hi = get(r_p2, w_hi, "mean_res_pair_mean")

    h1_inf_lift = res_inf_hi > 2.0 * max(res_inf_lo, 1e-12)
    h1_ch_lift = res_ch_hi > 2.0 * max(res_ch_lo, 1e-12)
    still_collapsed = res_inf_hi < 0.25 * res_p2_hi

    sp_inf = get(r_inf, w_lo, "mean_sparsity_mean")
    sp_p2 = get(r_p2, w_lo, "mean_sparsity_mean")
    h2_sparser = sp_inf > sp_p2 + 0.05

    spars = [a["mean_sparsity_mean"] for a in agg]
    ress = [a["mean_res_pair_mean"] for a in agg]
    corr_sp_res = float(np.corrcoef(spars, ress)[0, 1]) if len(spars) > 2 else float("nan")

    dev_inf = get(r_inf, w_lo, "mean_ipf_dev_mean")
    dev_p2 = get(r_p2, w_lo, "mean_ipf_dev_mean")
    h3_ipf_fail = dev_inf > 1e-4

    h5_p2_peak = res_p2_hi > res_inf_hi and res_p2_hi > 0.05

    full_inf = get(r_inf, w_lo, "full_res_pair_mean")
    full_p2 = get(r_p2, w_lo, "full_res_pair_mean")
    full_ch = get(r_ch, w_lo, "full_res_pair_mean")

    return {
        "windows_used": {"w_lo": w_lo, "w_hi": w_hi},
        "H1_window_bias": {
            f"res_inf_w{w_lo}": res_inf_lo,
            f"res_inf_w{w_hi}": res_inf_hi,
            f"res_ch_w{w_lo}": res_ch_lo,
            f"res_ch_w{w_hi}": res_ch_hi,
            "lift_inf": h1_inf_lift,
            "lift_ch": h1_ch_lift,
            f"still_collapsed_at_w{w_hi}": still_collapsed,
            "verdict": (
                "partial_window_bias"
                if (h1_inf_lift or h1_ch_lift) and still_collapsed
                else (
                    "window_bias_explains"
                    if (h1_inf_lift or h1_ch_lift) and not still_collapsed
                    else "window_bias_insufficient"
                )
            ),
        },
        "H2_sparsity": {
            f"sparsity_p2_w{w_lo}": sp_p2,
            f"sparsity_inf_w{w_lo}": sp_inf,
            "sparser_at_inf": h2_sparser,
            "corr_sparsity_vs_Res": corr_sp_res,
            "verdict": (
                "supported"
                if h2_sparser and corr_sp_res < -0.3
                else ("partial" if h2_sparser or corr_sp_res < -0.3 else "not_supported")
            ),
        },
        "H3_ipf": {
            f"ipf_dev_p2_w{w_lo}": dev_p2,
            f"ipf_dev_inf_w{w_lo}": dev_inf,
            "ipf_failure_at_inf": h3_ipf_fail,
            "verdict": "ipf_failure" if h3_ipf_fail else "ipf_ok_not_the_cause",
        },
        "H5_period2_peak": {
            f"res_p2_w{w_hi}": res_p2_hi,
            f"res_inf_w{w_hi}": res_inf_hi,
            "peak_persists": h5_p2_peak,
            "verdict": "real_structure_or_few_state" if h5_p2_peak else "artifact_only",
        },
        "full_block": {
            "full_p2": full_p2,
            "full_inf": full_inf,
            "full_ch": full_ch,
            "note": "full-block Res on ~800 symbols; still finite alphabet",
        },
        "headline": None,
    }


def write_report(
    agg: List[Dict],
    verdict: Dict,
    cfg: Dict,
    fig_paths: List[Path],
    stamp: str,
) -> Path:
    path = OUT_DIR / f"REPORT_res_pair_diag_{stamp}.md"
    ws = sorted({a["window"] for a in agg})
    # fill headline
    if "H1_window_bias" in verdict and "verdict" in verdict.get("H1_window_bias", {}):
        h1 = verdict["H1_window_bias"]["verdict"]
        h2 = verdict["H2_sparsity"]["verdict"]
        h3 = verdict["H3_ipf"]["verdict"]
        h5 = verdict["H5_period2_peak"]["verdict"]
        parts = []
        if h3 == "ipf_ok_not_the_cause":
            parts.append("IPF converges (not the cause)")
        else:
            parts.append(f"IPF: {h3}")
        if h2 in ("supported", "partial"):
            parts.append(f"sparsity {h2}")
        else:
            parts.append(f"sparsity {h2}")
        parts.append(f"window {h1}")
        parts.append(f"p2-peak {h5}")
        verdict["headline"] = "; ".join(parts)
    else:
        verdict.setdefault("headline", "see table / reduced mode")

    w_header = " | ".join(f"w={w}" for w in ws)
    lines = [
        f"# Res_pair diagnostics report — {stamp}",
        "",
        "Why does $\\mathrm{Res}_{\\mathrm{pair}}$ peak in period-2 and collapse near $r_\\infty$?",
        "",
        "## Configuration",
        "",
        "```json",
        json.dumps(cfg, indent=2),
        "```",
        "",
        "## Headline",
        "",
        f"**{verdict['headline']}**",
        "",
        "## Hypothesis verdicts",
        "",
        "```json",
        json.dumps(verdict, indent=2),
        "```",
        "",
        "## Summary table (mean Res_pair by r × window)",
        "",
        f"| r | station | {w_header} | sparsity_w{ws[0]} | unique_w{ws[0]} | IPF_dev_w{ws[0]} | full_Res |",
        "|" + "---|" * (3 + len(ws) + 4),
    ]
    rs = sorted({a["r"] for a in agg})
    for r in rs:
        st = next(a for a in agg if a["r"] == r)["station"]
        vals = {
            w: next(a for a in agg if a["r"] == r and a["window"] == w) for w in ws
        }
        m0 = vals[ws[0]]
        res_cells = " | ".join(f"{vals[w]['mean_res_pair_mean']:.4f}" for w in ws)
        lines.append(
            f"| {r:.2f} | {st} | {res_cells} | "
            f"{m0['mean_sparsity_mean']:.3f} | "
            f"{m0['mean_n_unique_joint_mean']:.1f} | "
            f"{m0['mean_ipf_dev_mean']:.2e} | "
            f"{m0['full_res_pair_mean']:.4f} |"
        )

    lines += [
        "",
        "## Reading guide",
        "",
        "- **H1 (window):** if Res rises with w near $r_\\infty$ but remains ≪ period-2, "
        "finite-window bias is *partial*, not full explanation.",
        "- **H2 (sparsity):** high unique/w ⇒ each joint pattern appears ~once ⇒ "
        "pairwise maxent can fit sparse tables almost perfectly ⇒ Res→0.",
        "- **H3 (IPF):** if final max_dev ≪ 1e-6, IPF converged; collapse is not numerical failure.",
        "- **H5 (period-2 peak):** if Res stays high at w=104 in period-2, the peak is "
        "few-state joint structure (or true higher-order residual), not short-window noise.",
        "- **Full-block:** long contiguous estimate; still limited by observed alphabet size.",
        "",
        "## Figures",
        "",
    ]
    for p in fig_paths:
        lines.append(f"- `{p.relative_to(ROOT)}`")
    lines += [
        "",
        "## Canon implication",
        "",
        "Report excess3 and Res_pair separately (E1). Collapse near $r_\\infty$ must be "
        "qualified by window length and support sparsity before claiming absence of strong L3.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    # stable copy
    (OUT_DIR / "REPORT_res_pair_diag.md").write_text("\n".join(lines), encoding="utf-8")
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n_realizations", type=int, default=4)
    ap.add_argument("--n_steps", type=int, default=1800)
    ap.add_argument("--n_comp", type=int, default=4)
    ap.add_argument("--coupling", type=float, default=0.05)
    ap.add_argument("--noise", type=float, default=0.003)
    ap.add_argument("--stride", type=int, default=8)
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()

    if args.quick:
        n_real = 2
        n_steps = 900
        windows = [13, 52]
    else:
        n_real = args.n_realizations
        n_steps = args.n_steps
        windows = WINDOWS

    stations = STATIONS
    stamp = time.strftime("%Y%m%d_%H%M%S")
    cfg = {
        "n_realizations": n_real,
        "n_steps": n_steps,
        "n_comp": args.n_comp,
        "coupling": args.coupling,
        "noise": args.noise,
        "stride": args.stride,
        "windows": windows,
        "stations": stations,
        "quick": args.quick,
    }
    print("=== Res_pair diagnostics ===")
    print(json.dumps(cfg, indent=2))

    flat: List[Dict] = []
    t0 = time.time()
    for r, st in stations:
        for seed in range(n_real):
            print(f"  r={r:.2f} seed={seed} ...", flush=True)
            rows = run_one(
                r=r,
                station=st,
                seed=seed,
                n_steps=n_steps,
                n_comp=args.n_comp,
                coupling=args.coupling,
                noise=args.noise,
                windows=windows,
                stride=args.stride,
            )
            for row in rows:
                print(
                    f"    w={row['window']:3d} Res={row['mean_res_pair']:.4f} "
                    f"sp={row['mean_sparsity']:.3f} uniq={row['mean_n_unique_joint']:.1f} "
                    f"ipf_dev={row['mean_ipf_dev']:.2e} full={row['full_res_pair']:.4f}",
                    flush=True,
                )
            flat.extend(rows)

    elapsed = time.time() - t0
    print(f"Done in {elapsed:.1f}s; {len(flat)} rows")

    # save flat
    flat_csv = OUT_DIR / f"res_pair_diag_flat_{stamp}.csv"
    keys = list(flat[0].keys())
    with flat_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(flat)

    agg = aggregate(flat)
    # if quick, only some windows — pad verdict carefully
    if args.quick:
        # duplicate w=13 as w=26 etc missing — skip full H1 w104
        # re-run verdict only on available windows
        available_w = sorted({a["window"] for a in agg})
        print("quick mode windows:", available_w)

    agg_csv = OUT_DIR / f"res_pair_diag_agg_{stamp}.csv"
    akeys = list(agg[0].keys())
    with agg_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=akeys)
        w.writeheader()
        w.writerows(agg)

    available_w = sorted({a["window"] for a in agg})
    if 13 in available_w and available_w[-1] >= 52:
        # Adapt H1 to use max window instead of hard-coded 104
        try:
            verdict = hypothesis_verdict(agg)
        except Exception as e:
            print("verdict fallback:", e)
            verdict = {"headline": f"verdict error: {e}", "mode": "error"}
    else:
        verdict = {
            "mode": "quick_reduced",
            "note": "Full H1–H5 needs broader window set; see table.",
            "headline": "quick run — see table",
            "H1_window_bias": {"verdict": "quick_skip"},
            "H2_sparsity": {"verdict": "quick_skip"},
            "H3_ipf": {"verdict": "quick_skip"},
            "H5_period2_peak": {"verdict": "quick_skip"},
            "full_block": {},
        }

    try:
        fig_paths = plot_results(agg, stamp)
    except Exception as e:
        print("plot warning:", e)
        fig_paths = []

    report = write_report(agg, verdict, cfg, fig_paths, stamp)

    json_path = OUT_DIR / f"res_pair_diag_{stamp}.json"
    json_path.write_text(
        json.dumps({"cfg": cfg, "verdict": verdict, "agg": agg, "elapsed_s": elapsed}, indent=2),
        encoding="utf-8",
    )
    print("Report:", report)
    print("JSON:", json_path)
    for p in fig_paths:
        print("Fig:", p)


if __name__ == "__main__":
    main()
