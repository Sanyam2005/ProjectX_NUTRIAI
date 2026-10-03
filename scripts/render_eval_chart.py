"""Render an accuracy report card from test_images/eval_results.json.

Produces two assets:
  docs/eval_chart.png        — single combined chart for the README / pitch deck
  docs/eval_chart_breakdown.png — per-image stripe + latency bar (more detail)

Run with:
    & "<venv>\\python.exe" scripts\\render_eval_chart.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap

HERE = Path(__file__).resolve().parent.parent
JSON = HERE / "test_images" / "eval_results.json"
OUT_DIR = HERE / "docs"
OUT_DIR.mkdir(exist_ok=True)

# Forest / Moss palette to match the pitch deck.
COLORS = {
    "bg":     "#0c1a14",
    "panel":  "#13261b",
    "ink":    "#e8f3ec",
    "muted":  "#7a8b80",
    "ok":     "#5fbd7d",
    "warn":   "#e0bd6c",
    "miss":   "#e07a6c",
    "accent": "#9be9b3",
}

CHECK_LABELS = [
    ("ok_name",       "Dish name match"),
    ("ok_ingredient", "Ingredient match"),
    ("ok_kcal",       "Calories in plausible range"),
    ("ok_macros",     "Macro consistency (\u00b135%)"),
]


def load_results() -> list[dict]:
    return json.loads(JSON.read_text())


def style_axes(ax) -> None:
    ax.set_facecolor(COLORS["panel"])
    ax.tick_params(colors=COLORS["ink"])
    for s in ax.spines.values():
        s.set_color(COLORS["muted"])
    ax.xaxis.label.set_color(COLORS["ink"])
    ax.yaxis.label.set_color(COLORS["ink"])
    ax.title.set_color(COLORS["ink"])


def render_summary(results: list[dict], out_path: Path) -> None:
    """Single 'report card' chart for the README / deck."""
    n = len(results)
    rates = {k: sum(1 for r in results if r.get(k)) / n for k, _ in CHECK_LABELS}
    labels = [label for _, label in CHECK_LABELS]
    values = [rates[k] * 100 for k, _ in CHECK_LABELS]

    avg_lat = sum(r["elapsed_s"] for r in results) / n
    median_lat = sorted(r["elapsed_s"] for r in results)[n // 2]

    fig, ax = plt.subplots(figsize=(10, 5.5), facecolor=COLORS["bg"])
    style_axes(ax)

    bar_colors = [COLORS["ok"] if v >= 80 else COLORS["warn"] if v >= 50 else COLORS["miss"] for v in values]
    bars = ax.barh(labels[::-1], values[::-1], color=bar_colors[::-1], height=0.55, edgecolor=COLORS["panel"], linewidth=2)

    for bar, value in zip(bars, values[::-1]):
        ax.text(value + 1.5, bar.get_y() + bar.get_height() / 2,
                f"{value:.0f}%  ({int(round(value * n / 100))}/{n})",
                color=COLORS["ink"], va="center", fontsize=11, fontweight="bold")

    ax.set_xlim(0, 110)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.set_xlabel("Pass rate")
    ax.set_title(f"NutriAI vision pipeline \u2014 {n} test images \u00b7 avg {avg_lat:.1f}s, median {median_lat:.1f}s",
                 fontsize=13, pad=14)

    ax.grid(axis="x", linestyle="--", alpha=0.18, color=COLORS["muted"])
    ax.set_axisbelow(True)

    fig.tight_layout()
    fig.savefig(out_path, dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"wrote {out_path}")


def render_breakdown(results: list[dict], out_path: Path) -> None:
    """Per-image stripe chart + latency bar."""
    n = len(results)
    fig, (ax_grid, ax_lat) = plt.subplots(
        2, 1, figsize=(12, 7.5), gridspec_kw={"height_ratios": [3, 2]},
        facecolor=COLORS["bg"]
    )
    for ax in (ax_grid, ax_lat):
        style_axes(ax)

    # --- top: pass/fail grid -------------------------------------------------
    check_keys = [k for k, _ in CHECK_LABELS]
    check_titles = [t for _, t in CHECK_LABELS]
    files = [r["file"].replace(".jpg", "") for r in results]

    for col, r in enumerate(results):
        for row, key in enumerate(check_keys):
            ok = r.get(key)
            color = COLORS["ok"] if ok else COLORS["miss"]
            ax_grid.add_patch(plt.Rectangle((col - 0.4, row - 0.4), 0.8, 0.8,
                                            facecolor=color, edgecolor=COLORS["panel"], linewidth=2))
            ax_grid.text(col, row, "OK" if ok else "MISS",
                         color=COLORS["panel"] if ok else COLORS["ink"],
                         ha="center", va="center", fontsize=8.5, fontweight="bold")

    ax_grid.set_xlim(-0.6, n - 0.4)
    ax_grid.set_ylim(-0.6, len(check_keys) - 0.4)
    ax_grid.set_xticks(range(n))
    ax_grid.set_xticklabels(files, rotation=30, ha="right", fontsize=9)
    ax_grid.set_yticks(range(len(check_keys)))
    ax_grid.set_yticklabels(check_titles, fontsize=10)
    ax_grid.invert_yaxis()
    ax_grid.set_title("Per-image check matrix", fontsize=12, pad=10)
    ax_grid.tick_params(axis="both", length=0)
    for s in ax_grid.spines.values():
        s.set_visible(False)

    # --- bottom: latency per image -----------------------------------------
    lats = [r["elapsed_s"] for r in results]
    bars = ax_lat.bar(files, lats, color=COLORS["accent"], edgecolor=COLORS["panel"], linewidth=2)
    for bar, lat in zip(bars, lats):
        ax_lat.text(bar.get_x() + bar.get_width() / 2, lat + 0.15,
                    f"{lat:.1f}s", ha="center", va="bottom", color=COLORS["ink"], fontsize=9)
    ax_lat.axhline(sum(lats) / len(lats), color=COLORS["warn"], linestyle="--", alpha=0.7,
                   label=f"avg {sum(lats)/len(lats):.1f}s")
    ax_lat.set_ylabel("Latency (s)")
    ax_lat.set_title("End-to-end response time per image (upload \u2192 GPT-4o \u2192 OFF override \u2192 JSON)",
                     fontsize=12, pad=10)
    ax_lat.tick_params(axis="x", labelrotation=30)
    for tick in ax_lat.get_xticklabels():
        tick.set_horizontalalignment("right")
        tick.set_fontsize(9)
    ax_lat.legend(facecolor=COLORS["panel"], edgecolor=COLORS["muted"],
                  labelcolor=COLORS["ink"], loc="upper right")
    ax_lat.grid(axis="y", linestyle="--", alpha=0.18, color=COLORS["muted"])
    ax_lat.set_axisbelow(True)

    fig.suptitle("NutriAI accuracy + latency breakdown", color=COLORS["ink"], fontsize=14, y=0.995)
    fig.tight_layout()
    fig.savefig(out_path, dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"wrote {out_path}")


def main() -> int:
    if not JSON.exists():
        print(f"ERROR: {JSON} not found. Run scripts/eval_accuracy.py first.")
        return 1
    results = load_results()
    if not results:
        print("ERROR: empty eval results.")
        return 1
    render_summary(results, OUT_DIR / "eval_chart.png")
    render_breakdown(results, OUT_DIR / "eval_chart_breakdown.png")

    # Also print a tiny console summary so you have raw numbers handy.
    n = len(results)
    print()
    for k, label in CHECK_LABELS:
        ok = sum(1 for r in results if r.get(k))
        print(f"  {label:35s} {ok}/{n}  ({ok/n*100:.0f}%)")
    lats = [r["elapsed_s"] for r in results]
    print(f"  Latency avg / median / max          {sum(lats)/len(lats):.1f}s / {sorted(lats)[len(lats)//2]:.1f}s / {max(lats):.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
