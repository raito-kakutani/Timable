"""
🔥 HEATMAP RENDERING
====================
Visual heatmaps for teacher load, class fatigue, day congestion, clash risk.
Uses pandas Styler for cell coloring.
"""

import pandas as pd
from typing import Dict, List


def _color_scale(val: float, low_rgb: str = "#22c55e", mid_rgb: str = "#eab308", high_rgb: str = "#ef4444") -> str:
    """Value 0-1 -> green (light) to red (overloaded)."""
    if val <= 0:
        return f"background-color: {low_rgb}; color: white;"
    if val >= 1:
        return f"background-color: {high_rgb}; color: white;"
    if val < 0.5:
        return f"background-color: {mid_rgb}; color: black;"
    return f"background-color: {high_rgb}; color: white;"


def render_teacher_load_heatmap(
    teacher_days: Dict[str, Dict[int, int]],
    days: List[str],
    teacher_max: Dict[str, int],
) -> pd.DataFrame:
    """Rows=teachers, Cols=days. Color by load vs max."""
    teachers = sorted(teacher_days.keys())
    data = []
    for tid in teachers:
        row = []
        for d in range(len(days)):
            count = teacher_days.get(tid, {}).get(d, 0)
            row.append(count)
        data.append(row)
    df = pd.DataFrame(data, index=teachers, columns=days)
    max_vals = df.max().max() or 1

    def _style(val):
        if pd.isna(val):
            return ""
        intensity = val / max_vals if max_vals else 0
        return _color_scale(intensity)

    return df.style.applymap(_style).set_caption("Teacher Load (darker = more periods)")


def render_day_congestion_heatmap(
    day_totals: Dict[int, int],
    days: List[str],
) -> pd.DataFrame:
    """Rows=days, Col=total periods."""
    row = [day_totals.get(d, 0) for d in range(len(days))]
    df = pd.DataFrame([row], index=["Periods"], columns=days)
    max_val = max(row) if row else 1

    def _style(val):
        intensity = val / max_val if max_val else 0
        return _color_scale(intensity)

    return df.style.applymap(_style).set_caption("Day Congestion")


def render_class_fatigue_heatmap(
    class_periods: Dict[str, Dict[int, float]],
    num_periods: int,
) -> pd.DataFrame:
    """Rows=classes, Cols=periods. Color by difficulty density."""
    classes = sorted(class_periods.keys())
    data = []
    for cid in classes:
        row = [class_periods.get(cid, {}).get(p, 0) for p in range(num_periods)]
        data.append(row)
    df = pd.DataFrame(data, index=classes, columns=[f"P{p+1}" for p in range(num_periods)])
    return df.style.applymap(lambda v: _color_scale(v) if pd.notna(v) else "").set_caption("Class Fatigue (heavier subjects = hotter)")
