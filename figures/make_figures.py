#!/usr/bin/env python3
"""Reproducible generator of the three figures of the manuscript.

Reads only published artifacts and recomputes no analysis; the scale-pair panel
comes from the output of ``src/exploratory.py``, so run that first. Writes SVG
and PDF (vector) plus PNG (preview) beside this file.

Okabe-Ito palette, colourblind-safe. No titles inside the figures, since the
captions live in the manuscript. Legible in black and white: shape and position
encode as well as colour.

    python3 src/exploratory.py
    python3 figures/make_figures.py
"""
import json
import sys
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import paths

plt.rcParams.update({
    "svg.fonttype": "none", "pdf.fonttype": 42, "ps.fonttype": 42,
    "font.family": "sans-serif", "font.size": 9,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": "#444444", "axes.linewidth": 0.8,
    "xtick.color": "#444444", "ytick.color": "#444444",
    "grid.color": "#dddddd", "grid.linewidth": 0.6,
})
OK = {"orange": "#E69F00", "skyblue": "#56B4E9", "green": "#009E73", "blue": "#0072B2",
      "vermillion": "#D55E00", "purple": "#CC79A7", "grey": "#999999", "ink": "#222222"}

FIGURES = Path(__file__).resolve().parent
#: Single-model self-consistency baseline, from the Supplementary Material.
BASELINE_N_EFF = 1.427
LINE_COLOUR = {"claude": OK["blue"], "mistral": OK["orange"], "gemma": OK["green"],
               "deepseek": OK["vermillion"], "gemini": OK["purple"]}


def save(figure, name: str) -> None:
    for extension in ("svg", "pdf"):
        figure.savefig(FIGURES / f"{name}.{extension}", bbox_inches="tight")
    figure.savefig(FIGURES / f"{name}.png", dpi=200, bbox_inches="tight")
    plt.close(figure)


indices = pd.read_csv(paths.ENSEMBLE_INDICES)
dissent = pd.read_csv(paths.PER_MODEL_DISSENT)
panel = pd.read_csv(paths.INDICES / "panel.csv").fillna("")
line_of = dict(zip(panel["model"], panel["line"]))
role_of = {row.model: row.scale_role for row in panel.itertuples() if row.scale_role}

scale_results = json.loads((paths.RESULTS / "exploratory.json").read_text())["rq3_scale"]


def short(model: str) -> str:
    return model.split("/")[-1]


# Figure 1 - the dissent regime
figure, (left, right) = plt.subplots(1, 2, figsize=(8.2, 3.2),
                                     gridspec_kw={"width_ratios": [1.5, 1]})
n_eff = indices["n_eff"].to_numpy()
left.hist(n_eff, bins=24, range=(1.0, 2.6), color=OK["blue"], alpha=0.75,
          edgecolor="white", linewidth=0.5)
left.axvline(1.0, color=OK["ink"], lw=1.4)
left.axvline(n_eff.mean(), color=OK["vermillion"], lw=1.6, ls="--")
left.annotate(f"panel mean {n_eff.mean():.2f}", xy=(n_eff.mean(), 0),
              xytext=(n_eff.mean() + 0.06, left.get_ylim()[1] * 0.86),
              color=OK["vermillion"], fontsize=9, fontweight="bold")
left.axvline(BASELINE_N_EFF, color=OK["green"], lw=1.6, ls=":")
left.annotate(f"single-model\nbaseline {BASELINE_N_EFF:.2f}", xy=(BASELINE_N_EFF, 0),
              xytext=(BASELINE_N_EFF, left.get_ylim()[1] * 0.62), ha="center",
              color=OK["green"], fontsize=8, fontweight="bold")
left.annotate("N_eff = 1\n(total consensus)", xy=(1.0, 0),
              xytext=(1.02, left.get_ylim()[1] * 0.30), color=OK["ink"], fontsize=8)
left.text(0.98, 1.02, "maximum possible N_eff = 16 (all voices independent)",
          transform=left.transAxes, ha="right", va="bottom", fontsize=7.5, color="#666666")
left.set_xlim(1.0, 2.6)
left.set_xlabel("Effective number of independent voices  N_eff  (16 models)")
left.set_ylabel("Runs")
left.grid(axis="y", alpha=0.5)

s_norm = indices["s_norm"].to_numpy()
right.hist(s_norm, bins=24, range=(0, 1), color=OK["skyblue"], alpha=0.8,
           edgecolor="white", linewidth=0.5)
right.axvline(s_norm.mean(), color=OK["vermillion"], lw=1.6, ls="--")
right.annotate(f"mean {s_norm.mean():.2f}", xy=(s_norm.mean(), 0),
               xytext=(s_norm.mean() + 0.03, right.get_ylim()[1] * 0.86),
               color=OK["vermillion"], fontsize=9, fontweight="bold")
right.set_xlim(0, 1)
right.set_xlabel("Spectral dissent index  S_norm  ∈ [0,1]")
right.set_ylabel("Runs")
right.grid(axis="y", alpha=0.5)
save(figure, "fig1_dissent_regime")

# Figure 2 - per-model dissent contribution, ordered by mean
order = dissent.groupby("model")["d_i"].mean().sort_values().index.tolist()
figure, axis = plt.subplots(figsize=(7.2, 6.2))
boxes = axis.boxplot([dissent.loc[dissent.model == m, "d_i"].to_numpy() for m in order],
                     positions=list(range(len(order))), vert=False, widths=0.6,
                     patch_artist=True, showfliers=False,
                     medianprops=dict(color="#222222", lw=1.4),
                     whiskerprops=dict(color="#777777", lw=1.0),
                     capprops=dict(color="#777777", lw=1.0))
for patch, model in zip(boxes["boxes"], order):
    colour = LINE_COLOUR.get(line_of[model], OK["grey"])
    patch.set_facecolor(colour)
    patch.set_alpha(0.55)
    patch.set_edgecolor(colour)
    patch.set_linewidth(1.0)
for position, model in enumerate(order):
    mean = dissent.loc[dissent.model == model, "d_i"].mean()
    role = role_of.get(model)
    if role == "small":
        axis.plot(mean, position, marker="o", mfc="white", mec="#222222", mew=1.4, ms=6, zorder=4)
    elif role == "large":
        axis.plot(mean, position, marker="o", mfc="#222222", mec="#222222", ms=6, zorder=4)
    else:
        axis.plot(mean, position, marker="D", mfc="#222222", mec="#222222", ms=5, zorder=4)
axis.set_yticks(range(len(order)))
axis.set_yticklabels([short(m) for m in order], fontsize=8.5)
axis.set_xlabel("Per-model dissent contribution  d_i")
axis.set_ylim(-0.6, len(order) - 0.4)
axis.grid(axis="x", alpha=0.5)
family_legend = [Line2D([0], [0], marker="s", color="white", markerfacecolor=LINE_COLOUR[l],
                        markersize=9, label=l)
                 for l in ("claude", "mistral", "gemma", "deepseek", "gemini")]
family_legend.append(Line2D([0], [0], marker="s", color="white", markerfacecolor=OK["grey"],
                            markersize=9, label="single-model family"))
marker_legend = [
    Line2D([0], [0], marker="o", color="#222", mfc="white", mew=1.4, ls="none", ms=6,
           label="mean — scale pair small"),
    Line2D([0], [0], marker="o", color="#222", mfc="#222", ls="none", ms=6,
           label="mean — scale pair large"),
    Line2D([0], [0], marker="D", color="#222", mfc="#222", ls="none", ms=5,
           label="mean — not a scale pair"),
]
axis.add_artist(axis.legend(handles=family_legend, title="family / line", loc="lower right",
                            fontsize=8, title_fontsize=8, frameon=False))
axis.legend(handles=marker_legend, title="marker", loc="lower right",
            bbox_to_anchor=(1.0, 0.30), fontsize=8, title_fontsize=8, frameon=False)
save(figure, "fig2_per_model_dissent")

# Figure 3 - scale pairs, paired difference with confidence interval
pair_order = ["mistral", "claude-4.5", "gemma-4", "deepseek-v4"]
pair_labels = {"claude-4.5": "claude-4.5\n(haiku vs sonnet)",
               "mistral": "mistral\n(ministral-14b vs large)",
               "gemma-4": "gemma-4\n(26b vs 31b)",
               "deepseek-v4": "deepseek-v4\n(flash vs pro)"}
pair_colours = {"claude-4.5": OK["blue"], "mistral": OK["orange"],
                "gemma-4": OK["green"], "deepseek-v4": OK["vermillion"]}
figure, axis = plt.subplots(figsize=(6.6, 3.2))
for position, key in enumerate(pair_order):
    result = scale_results[key]
    low, high = result["ci95"]
    colour = pair_colours[key]
    axis.plot([low, high], [position, position], color=colour, lw=2.2,
              solid_capstyle="round", zorder=2)
    axis.plot(result["paired_diff_large_minus_small"], position, marker="o",
              mfc=colour, mec=colour, ms=9, zorder=3)
axis.axvline(0, color=OK["ink"], lw=1.3, zorder=1)
axis.set_yticks(range(len(pair_order)))
axis.set_yticklabels([pair_labels[k] for k in pair_order], fontsize=8.5)
axis.set_ylim(-0.6, len(pair_order) - 0.4)
axis.set_xlabel("Paired difference in d_i,  large − small   (dot = mean, bar = 95% CI)")
axis.grid(axis="x", alpha=0.5)
axis.text(0.02, 1.02, "← small model more divergent", transform=axis.transAxes,
          ha="left", va="bottom", fontsize=8, color="#666")
axis.text(0.98, 1.02, "large model more divergent →", transform=axis.transAxes,
          ha="right", va="bottom", fontsize=8, color="#666")
save(figure, "fig3_scale_pairs")

print("figures written (svg, pdf, png):")
for name in ("fig1_dissent_regime", "fig2_per_model_dissent", "fig3_scale_pairs"):
    print(f"  {name}")
