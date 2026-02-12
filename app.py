"""
🧠 SMART TIMETABLE BUILDER — Smooth, stable, alive
==================================================
- Notifications count down smoothly (fragment run_every)
- st.form() prevents screen jump while typing
- History log like Chrome
- All data persisted to disk
- Priority section optional (timetable works without it)
"""

import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import List

from models import Teacher, Class, ClassSubject, SchoolConfig, ClassPriorityConfig, get_break_name
from solver import solve_timetable, invert_to_teacher_timetable, improve_timetable, generate_rotations
from pdf_export import export_class_timetables_pdf, export_teacher_timetables_pdf, flat_to_class_timetables
from storage import (
    load_teachers, save_teachers, load_classes, save_classes,
    load_priority_configs, save_priority_configs,
    load_config, save_config,
    load_history, append_history,
    is_demo_loaded, set_demo_loaded, clear_demo_loaded,
    load_base_timetable, save_base_timetable,
    load_scenario_state, save_scenario_state,
    clear_base_timetable, clear_scenario_state,
)
from ui_forms import render_teacher_form, render_class_form, get_edit_buffer_teacher, get_edit_buffer_class
from scenarios import (
    apply_scenarios, serialize_timetable, deserialize_timetable,
    teacher_load_heatmap, class_fatigue_heatmap, day_congestion_heatmap, clash_risk_heatmap,
)
from heatmaps import render_teacher_load_heatmap, render_day_congestion_heatmap, render_class_fatigue_heatmap


# ---------------------------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Smart Timetable Builder", page_icon="📅", layout="wide")

# ---------------------------------------------------------------------------
# CSS — Animations (smooth, no layout shift)
# ---------------------------------------------------------------------------

ANIMATION_CSS = """
<style>
    /* Dark theme — gray / neutral */
    .main { background-color: #0f0f0f; }
    .main .block-container { padding-top: 2rem; }
    h1 { color: #fafafa !important; }
    h2, h3 { color: #e4e4e7 !important; }
    p, span, label { color: #a1a1aa !important; }
    .stMarkdown { color: #a1a1aa; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #18181b 0%, #0f0f0f 100%);
    }
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] label { color: #e4e4e7 !important; }

    /* Tab bar */
    .stTabs {
        background-color: #0f0f0f;
        padding: 6px 8px;
        border-radius: 10px;
    }
    .stTabs > div > div {
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab-list"] {
        background-color: #111113;
        border-radius: 10px;
        padding: 4px;
        border: 1px solid #27272a;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.02), 0 12px 28px rgba(0,0,0,0.45);
        transition: all 0.25s ease;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: #a1a1aa;
        border-radius: 6px;
        transition: all 0.2s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #e4e4e7;
        background-color: rgba(63,63,70,0.35);
    }
    .stTabs [aria-selected="true"] {
        background-color: #27272a !important;
        color: #fafafa !important;
    }

    /* Notification slot */
    #notification-slot {
        min-height: 52px;
        margin-bottom: 8px;
    }

    /* Toast */
    .toast-item {
        padding: 10px 14px;
        background: #18181b;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        font-size: 13px;
        color: #e4e4e7;
        max-width: 300px;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        animation: toastFadeIn 0.3s ease;
    }
    @keyframes toastFadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .toast-msg { flex: 1; }
    .toast-countdown { font-size: 11px; color: #71717a; min-width: 24px; }

    /* Buttons */
    button {
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
    }
    button:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0,0,0,0.4);
    }
    button:active { transform: translateY(0); }
    .stButton button[kind="primary"] {
        background: #e4e4e7;
        color: #111827;
        border: 1px solid #52525b;
        box-shadow: 0 6px 14px rgba(0,0,0,0.35);
    }
    .stButton button[kind="primary"]:hover {
        background: #f4f4f5;
        color: #020617;
        box-shadow: 0 10px 20px rgba(0,0,0,0.45);
    }
    .stButton button[kind="primary"]:active {
        background: #d4d4d8;
        color: #111827;
    }

    /* Expanders / cards */
    .stExpander {
        animation: cardFadeIn 0.35s ease;
        background-color: #18181b;
        border: 1px solid #27272a;
        border-radius: 8px;
    }
    @keyframes cardFadeIn {
        from { opacity: 0; transform: translateY(4px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Tables — full text visible, no truncation */
    [data-testid="stDataFrame"] {
        animation: tableFadeIn 0.4s ease;
    }
    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th {
        min-width: 90px !important;
        max-width: 180px !important;
        white-space: normal !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
        padding: 10px 12px !important;
        line-height: 1.4 !important;
    }
    [data-testid="stDataFrame"] .stDataFrame {
        width: 100% !important;
    }
    @keyframes tableFadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    /* History entry */
    .history-entry {
        padding: 12px 16px;
        background: #18181b;
        border: 1px solid #27272a;
        border-radius: 8px;
        margin-bottom: 8px;
        transition: box-shadow 0.2s ease;
    }
    .history-entry:hover { box-shadow: 0 2px 12px rgba(0,0,0,0.3); }

    /* Inputs — darker outline for better visibility */
    [data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] {
        border: 1.5px solid #52525b !important;
        border-radius: 6px !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }
    [data-baseweb="input"]:focus, [data-baseweb="textarea"]:focus {
        border-color: #71717a !important;
        box-shadow: 0 0 0 2px rgba(113, 113, 122, 0.3) !important;
    }
</style>
"""

st.markdown(ANIMATION_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# SESSION STATE — Load from disk
# ---------------------------------------------------------------------------

def _init_session():
    if "initialized" not in st.session_state:
        st.session_state.teachers = load_teachers()
        st.session_state.classes = load_classes()
        st.session_state.priority_configs = load_priority_configs()
        st.session_state.config = load_config()
        st.session_state.initialized = True

    if "class_timetable" not in st.session_state:
        st.session_state.class_timetable = None
    if "teacher_timetable" not in st.session_state:
        st.session_state.teacher_timetable = None
    if "notifications" not in st.session_state:
        st.session_state.notifications = []  # List of {msg, until, id}
    if "editing_teacher" not in st.session_state:
        st.session_state.editing_teacher = None
    if "editing_class" not in st.session_state:
        st.session_state.editing_class = None
    if "form_teacher" not in st.session_state:
        st.session_state.form_teacher = {"id": "", "subjects": "", "sections": "", "max": 6}
    if "form_class" not in st.session_state:
        st.session_state.form_class = {"id": "", "subjects": ""}
    if "scenario_state" not in st.session_state:
        st.session_state.scenario_state = load_scenario_state()
    # Restore base timetable from disk if we have none
    if st.session_state.class_timetable is None:
        base_data = load_base_timetable()
        if base_data:
            st.session_state.class_timetable = deserialize_timetable(base_data)
            st.session_state.teacher_timetable = invert_to_teacher_timetable(
                st.session_state.class_timetable, st.session_state.config
            )


_init_session()


# ---------------------------------------------------------------------------
# DEMO DATA — Predefined for quick testing
# ---------------------------------------------------------------------------

def _get_demo_teachers():
    """Demo teachers: Science, Commerce, Humanities streams. Realistic names."""
    return [
        Teacher("Eric Simon", ["Physics"], ["11SCI", "12SCI"], 5),
        Teacher("Aisha Khan", ["Chemistry"], ["11SCI", "12SCI"], 5),
        Teacher("Rahul Mehta", ["Mathematics"], ["11SCI", "12SCI", "11COM", "12COM"], 5),
        Teacher("Neha Verma", ["Biology"], ["11SCI", "12SCI"], 5),
        Teacher("Daniel Brooks", ["English"], ["11SCI", "12SCI", "11COM", "12COM", "11HUM", "12HUM"], 4),
        Teacher("Priya Nair", ["Economics"], ["11COM", "12COM"], 5),
        Teacher("Arjun Patel", ["Accountancy"], ["11COM", "12COM"], 5),
        Teacher("Kavita Rao", ["Business Studies"], ["11COM", "12COM"], 4),
        Teacher("Sofia Mendes", ["History"], ["11HUM", "12HUM"], 5),
        Teacher("Aman Gupta", ["Political Science"], ["11HUM", "12HUM"], 5),
        Teacher("Ritu Chawla", ["Geography"], ["11HUM", "12HUM"], 4),
        Teacher("Marcus Lee", ["Physical Education"], ["11SCI", "12SCI", "11COM", "12COM", "11HUM", "12HUM"], 3),
    ]


def _get_demo_classes():
    """Demo classes: 11SCI, 12SCI, 11COM, 12COM, 11HUM, 12HUM."""
    return [
        Class("11SCI", [
            ClassSubject("Physics", 6, "Eric Simon"),
            ClassSubject("Chemistry", 6, "Aisha Khan"),
            ClassSubject("Mathematics", 6, "Rahul Mehta"),
            ClassSubject("Biology", 6, "Neha Verma"),
            ClassSubject("English", 4, "Daniel Brooks"),
            ClassSubject("Physical Education", 2, "Marcus Lee"),
        ]),
        Class("12SCI", [
            ClassSubject("Physics", 6, "Eric Simon"),
            ClassSubject("Chemistry", 6, "Aisha Khan"),
            ClassSubject("Mathematics", 6, "Rahul Mehta"),
            ClassSubject("Biology", 6, "Neha Verma"),
            ClassSubject("English", 4, "Daniel Brooks"),
            ClassSubject("Physical Education", 2, "Marcus Lee"),
        ]),
        Class("11COM", [
            ClassSubject("Accountancy", 6, "Arjun Patel"),
            ClassSubject("Business Studies", 6, "Kavita Rao"),
            ClassSubject("Economics", 6, "Priya Nair"),
            ClassSubject("Mathematics", 4, "Rahul Mehta"),
            ClassSubject("English", 4, "Daniel Brooks"),
            ClassSubject("Physical Education", 2, "Marcus Lee"),
        ]),
        Class("12COM", [
            ClassSubject("Accountancy", 6, "Arjun Patel"),
            ClassSubject("Business Studies", 6, "Kavita Rao"),
            ClassSubject("Economics", 6, "Priya Nair"),
            ClassSubject("Mathematics", 4, "Rahul Mehta"),
            ClassSubject("English", 4, "Daniel Brooks"),
            ClassSubject("Physical Education", 2, "Marcus Lee"),
        ]),
        Class("11HUM", [
            ClassSubject("History", 6, "Sofia Mendes"),
            ClassSubject("Political Science", 6, "Aman Gupta"),
            ClassSubject("Geography", 6, "Ritu Chawla"),
            ClassSubject("English", 4, "Daniel Brooks"),
            ClassSubject("Physical Education", 2, "Marcus Lee"),
        ]),
        Class("12HUM", [
            ClassSubject("History", 6, "Sofia Mendes"),
            ClassSubject("Political Science", 6, "Aman Gupta"),
            ClassSubject("Geography", 6, "Ritu Chawla"),
            ClassSubject("English", 4, "Daniel Brooks"),
            ClassSubject("Physical Education", 2, "Marcus Lee"),
        ]),
    ]


def _load_demo_data() -> bool:
    """
    Inject demo teachers and classes. Skip duplicates by ID.
    Saves to disk. Sets demo_loaded flag so button disables.
    Returns True if any data was added.
    """
    existing_t_ids = {t.teacher_id for t in st.session_state.teachers}
    existing_c_ids = {c.class_id for c in st.session_state.classes}
    added = False
    for t in _get_demo_teachers():
        if t.teacher_id not in existing_t_ids:
            st.session_state.teachers.append(t)
            existing_t_ids.add(t.teacher_id)
            added = True
    for c in _get_demo_classes():
        if c.class_id not in existing_c_ids:
            st.session_state.classes.append(c)
            existing_c_ids.add(c.class_id)
            added = True
    if added:
        save_teachers(st.session_state.teachers)
        save_classes(st.session_state.classes)
    set_demo_loaded()  # Always disable button after first use
    append_history("demo", "Demo Data", "Loaded demo teachers and classes", "")
    st.session_state.class_timetable = None
    st.session_state.teacher_timetable = None
    return added


# ---------------------------------------------------------------------------
# NOTIFICATIONS — Stackable, smooth countdown via fragment
# ---------------------------------------------------------------------------

def show_toast(msg: str, duration_sec: int = 3) -> None:
    """Add a notification. Stackable — new ones don't replace old."""
    uid = f"n_{time.time()}_{id(msg)}"
    st.session_state.notifications.append({
        "msg": msg,
        "until": time.time() + duration_sec,
        "id": uid,
    })


@st.fragment(run_every=timedelta(seconds=1))
def _notification_ticker():
    """
    Runs every second. Removes expired toasts, countdown ticks smoothly.
    Fragment reruns only this block — no full-page refresh.
    """
    now = time.time()
    notifications = st.session_state.get("notifications", [])
    active = [n for n in notifications if n["until"] > now]
    if len(active) != len(notifications):
        st.session_state.notifications = active

    if not active:
        return

    for n in active:
        remaining = max(0, int(n["until"] - now))
        st.markdown(
            f'<div class="toast-item">'
            f'<span class="toast-msg">{n["msg"]}</span>'
            f'<span class="toast-countdown">{remaining}s</span>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# SIDEBAR — Config (persisted)
# ---------------------------------------------------------------------------

st.sidebar.title("⚙️ School Setup")
cfg = st.session_state.config

with st.sidebar.form("sidebar_config", clear_on_submit=False):
    st.markdown("**📆 Days & Periods**")
    days_input = st.text_input(
        "Days (comma-separated)",
        value=",".join(cfg.days) if cfg.days else "Mon,Tue,Wed,Thu,Fri",
        key="sb_days",
    )
    periods = st.number_input(
        "Periods per day",
        min_value=4,
        max_value=12,
        value=cfg.periods_per_day or 8,
        key="sb_periods",
    )
    st.markdown("**🥤 Break Periods**")
    st.caption("Add in the fields below (period number, name)")
    break_p_str = st.text_area(
        "Break periods (one per line: period,name)",
        value="\n".join(f"{p+1},{n}" for p, n in sorted(cfg.break_periods.items())),
        height=80,
        key="sb_breaks",
    )
    if st.form_submit_button("Apply Config"):
        days = [d.strip() for d in days_input.split(",") if d.strip()]
        break_periods = {}
        for line in break_p_str.strip().split("\n"):
            parts = line.strip().split(",")
            if len(parts) >= 2:
                try:
                    p = int(parts[0].strip()) - 1
                    name = parts[1].strip()
                    if name:
                        break_periods[p] = name
                except ValueError:
                    pass
        if days:
            st.session_state.config = SchoolConfig(
                days=days,
                periods_per_day=int(periods),
                break_periods=break_periods or cfg.break_periods,
            )
            save_config(st.session_state.config)
            show_toast("Config saved")
            st.rerun()

st.sidebar.markdown("---")
with st.sidebar.expander("🧪 Demo / Testing"):
    demo_loaded = is_demo_loaded()
    if demo_loaded:
        st.caption("Demo data already loaded.")
        st.button("Load Demo Data", key="demo_btn", disabled=True)
    else:
        if st.button("Load Demo Data", key="demo_btn"):
            if _load_demo_data():
                show_toast("Demo data loaded successfully")
            else:
                show_toast("Demo data already present (no duplicates added)")
            st.rerun()

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Clear all data"):
    st.session_state.teachers = []
    st.session_state.classes = []
    st.session_state.priority_configs = []
    st.session_state.class_timetable = None
    st.session_state.teacher_timetable = None
    st.session_state.scenario_state = {"selected_day": 0, "scenarios": {}}
    st.session_state.editing_teacher = None
    st.session_state.editing_class = None
    save_teachers([])
    save_classes([])
    save_priority_configs([])
    clear_base_timetable()
    clear_scenario_state()
    clear_demo_loaded()
    append_history("clear", "All", "All teachers and classes cleared", "")
    show_toast("All data cleared")
    st.rerun()


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

st.title("📅 Smart Timetable Builder")
st.markdown("*Smooth, stable, alive. Data persists across refresh.*")

# Notification slot — fixed height to prevent layout shift
st.markdown('<div id="notification-slot"></div>', unsafe_allow_html=True)
_notification_ticker()

tabs = st.tabs([
    "👥 Teachers & Classes",
    "📚 Saved Data",
    "🕓 History",
    "📋 Class Timetables",
    "👨‍🏫 Teacher Timetables",
    "🔄 Rotation",
    "🧪 What-If Lab",
    "🔥 Insights",
    "📄 PDF Export",
])
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = tabs


# ----- TAB 1: Teachers & Classes -----
with tab1:
    st.header("1. Add Teachers")
    editing_t = st.session_state.editing_teacher
    ft = st.session_state.form_teacher

    with st.expander("➕ Add a teacher" if editing_t is None else "✏️ Edit teacher", expanded=True):
        def on_teacher_save(t_id: str, subj_list: list, sec_list: list, t_max: int):
            t = Teacher(teacher_id=t_id, subjects=subj_list, sections=sec_list, max_periods_per_day=t_max)
            if editing_t is not None:
                st.session_state.teachers[editing_t] = t
                show_toast(f"Teacher {t_id} updated")
                append_history("edit", f"Teacher {t_id}", f"Updated teacher {t_id}", "")
            else:
                st.session_state.teachers.append(t)
                show_toast(f"Teacher {t_id} added")
                append_history("add", f"Teacher {t_id}", f"Added teacher {t_id}", "")
            save_teachers(st.session_state.teachers)
            st.session_state.form_teacher = {"id": "", "subjects": "", "sections": "", "max": 6}
            st.session_state.editing_teacher = None
            st.session_state.class_timetable = None
            st.session_state.teacher_timetable = None
            st.rerun()

        def on_teacher_cancel():
            st.session_state.editing_teacher = None
            st.session_state.form_teacher = {"id": "", "subjects": "", "sections": "", "max": 6}
            st.rerun()

        render_teacher_form(editing_t, ft, on_teacher_save, on_teacher_cancel)

    if st.session_state.teachers:
        st.subheader("Teachers")
        for i, t in enumerate(st.session_state.teachers):
            with st.container():
                c1, c2, c3 = st.columns([4, 1, 1])
                with c1:
                    st.markdown(f"**{t.teacher_id}** — {', '.join(t.subjects)} · Max {t.max_periods_per_day}/day")
                with c2:
                    if st.button("Edit", key=f"t_edit_{i}"):
                        st.session_state.editing_teacher = i
                        st.session_state.form_teacher = get_edit_buffer_teacher(t)
                        st.rerun()
                with c3:
                    if st.button("Remove", key=f"t_rm_{i}"):
                        name = t.teacher_id
                        st.session_state.teachers.pop(i)
                        save_teachers(st.session_state.teachers)
                        st.session_state.class_timetable = None
                        st.session_state.teacher_timetable = None
                        append_history("delete", f"Teacher {name}", f"Removed teacher {name}", "")
                        show_toast(f"Teacher {name} removed")
                        st.rerun()

    st.markdown("---")
    st.header("2. Add Classes")
    editing_c = st.session_state.editing_class
    fc = st.session_state.form_class

    with st.expander("➕ Add a class" if editing_c is None else "✏️ Edit class", expanded=True):
        def on_class_save(c_id: str, subs: list):
            cls = Class(class_id=c_id, subjects=subs)
            if editing_c is not None:
                st.session_state.classes[editing_c] = cls
                show_toast(f"Class {c_id} updated")
                append_history("edit", f"Class {c_id}", f"Updated class {c_id}", "")
            else:
                st.session_state.classes.append(cls)
                show_toast(f"Class {c_id} added")
                append_history("add", f"Class {c_id}", f"Added class {c_id}", "")
            save_classes(st.session_state.classes)
            st.session_state.form_class = {"id": "", "subjects": ""}
            st.session_state.editing_class = None
            st.session_state.class_timetable = None
            st.session_state.teacher_timetable = None
            st.rerun()

        def on_class_cancel():
            st.session_state.editing_class = None
            st.session_state.form_class = {"id": "", "subjects": ""}
            st.rerun()

        render_class_form(editing_c, fc, on_class_save, on_class_cancel)

    if st.session_state.classes:
        st.subheader("Classes")
        for i, c in enumerate(st.session_state.classes):
            subj_str = ", ".join(f"{cs.subject}({cs.weekly_periods}w)" for cs in c.subjects)
            with st.container():
                c1, c2, c3 = st.columns([4, 1, 1])
                with c1:
                    st.markdown(f"**{c.class_id}** — {subj_str}")
                with c2:
                    if st.button("Edit", key=f"c_edit_{i}"):
                        st.session_state.editing_class = i
                        st.session_state.form_class = get_edit_buffer_class(c)
                        st.rerun()
                with c3:
                    if st.button("Remove", key=f"c_rm_{i}"):
                        name = c.class_id
                        st.session_state.classes.pop(i)
                        st.session_state.priority_configs = [
                            p for p in st.session_state.priority_configs if p.class_id != name
                        ]
                        save_classes(st.session_state.classes)
                        save_priority_configs(st.session_state.priority_configs)
                        st.session_state.class_timetable = None
                        st.session_state.teacher_timetable = None
                        append_history("delete", f"Class {name}", f"Removed class {name}", "")
                        show_toast(f"Class {name} removed")
                        st.rerun()

    st.markdown("---")
    st.header("3. Priority Settings (Optional)")
    st.caption("Leave empty if you don't need priority scheduling. Timetable still generates.")
    for i, c in enumerate(st.session_state.classes):
        with st.expander(f"Priorities for {c.class_id}"):
            pc = next((p for p in st.session_state.priority_configs if p.class_id == c.class_id), None)
            if pc is None:
                pc = ClassPriorityConfig(class_id=c.class_id)
                st.session_state.priority_configs.append(pc)
            with st.form(f"prio_form_{c.class_id}"):
                prio = st.text_input("Priority (early) subjects", value=",".join(pc.priority_subjects), key=f"prio_{c.class_id}")
                weak = st.text_input("Weak subjects", value=",".join(pc.weak_subjects), key=f"weak_{c.class_id}")
                heavy = st.text_input("Heavy subjects", value=",".join(pc.heavy_subjects), key=f"heavy_{c.class_id}")
                if st.form_submit_button("Save"):
                    pc.priority_subjects = [s.strip() for s in prio.split(",") if s.strip()]
                    pc.weak_subjects = [s.strip() for s in weak.split(",") if s.strip()]
                    pc.heavy_subjects = [s.strip() for s in heavy.split(",") if s.strip()]
                    save_priority_configs(st.session_state.priority_configs)
                    show_toast(f"Priorities for {c.class_id} saved")
                    st.rerun()


# ----- TAB 2: Saved Data -----
with tab2:
    st.header("📚 Saved Data")
    editing_t = st.session_state.editing_teacher
    editing_c = st.session_state.editing_class

    if editing_t is not None:
        with st.expander("✏️ Edit teacher", expanded=True):
            t = st.session_state.teachers[editing_t]
            def _on_hist_t_save(t_id, subj_list, sec_list, t_max):
                st.session_state.teachers[editing_t] = Teacher(
                    teacher_id=t_id, subjects=subj_list, sections=sec_list, max_periods_per_day=t_max
                )
                save_teachers(st.session_state.teachers)
                append_history("edit", f"Teacher {t_id}", f"Updated {t_id}", "")
                show_toast(f"Teacher {t_id} updated")
                st.session_state.editing_teacher = None
                st.session_state.form_teacher = {"id": "", "subjects": "", "sections": "", "max": 6}
                st.session_state.class_timetable = None
                st.session_state.teacher_timetable = None
                st.rerun()
            def _on_hist_t_cancel():
                st.session_state.editing_teacher = None
                st.session_state.form_teacher = {"id": "", "subjects": "", "sections": "", "max": 6}
                st.rerun()
            render_teacher_form(editing_t, get_edit_buffer_teacher(t), _on_hist_t_save, _on_hist_t_cancel, prefix="hist")

    if editing_c is not None:
        with st.expander("✏️ Edit class", expanded=True):
            c = st.session_state.classes[editing_c]
            def _on_hist_c_save(c_id, subs):
                st.session_state.classes[editing_c] = Class(class_id=c_id, subjects=subs)
                save_classes(st.session_state.classes)
                append_history("edit", f"Class {c_id}", f"Updated {c_id}", "")
                show_toast(f"Class {c_id} updated")
                st.session_state.editing_class = None
                st.session_state.form_class = {"id": "", "subjects": ""}
                st.session_state.class_timetable = None
                st.session_state.teacher_timetable = None
                st.rerun()
            def _on_hist_c_cancel():
                st.session_state.editing_class = None
                st.session_state.form_class = {"id": "", "subjects": ""}
                st.rerun()
            render_class_form(editing_c, get_edit_buffer_class(c), _on_hist_c_save, _on_hist_c_cancel, prefix="hist")

    st.subheader("Teachers")
    if st.session_state.teachers:
        for i, t in enumerate(st.session_state.teachers):
            with st.container():
                col1, col2, col3 = st.columns([4, 1, 1])
                with col1:
                    st.markdown(f"**{t.teacher_id}** — {', '.join(t.subjects)}")
                with col2:
                    if st.button("✏️ Edit", key=f"hist_t_edit_{i}"):
                        st.session_state.editing_teacher = i
                        st.session_state.form_teacher = get_edit_buffer_teacher(t)
                        st.rerun()
                with col3:
                    if st.button("🗑️ Delete", key=f"hist_t_del_{i}"):
                        name = t.teacher_id
                        st.session_state.teachers.pop(i)
                        save_teachers(st.session_state.teachers)
                        append_history("delete", f"Teacher {name}", f"Deleted {name}", "")
                        show_toast(f"Teacher {name} deleted")
                        st.rerun()
    else:
        st.info("No teachers yet.")

    st.markdown("---")
    st.subheader("Classes")
    if st.session_state.classes:
        for i, c in enumerate(st.session_state.classes):
            subj_str = ", ".join(f"{cs.subject}({cs.weekly_periods}w)" for cs in c.subjects)
            with st.container():
                col1, col2, col3 = st.columns([4, 1, 1])
                with col1:
                    st.markdown(f"**{c.class_id}** — {subj_str}")
                with col2:
                    if st.button("✏️ Edit", key=f"hist_c_edit_{i}"):
                        st.session_state.editing_class = i
                        st.session_state.form_class = get_edit_buffer_class(c)
                        st.rerun()
                with col3:
                    if st.button("🗑️ Delete", key=f"hist_c_del_{i}"):
                        name = c.class_id
                        st.session_state.classes.pop(i)
                        st.session_state.priority_configs = [
                            p for p in st.session_state.priority_configs if p.class_id != name
                        ]
                        save_classes(st.session_state.classes)
                        save_priority_configs(st.session_state.priority_configs)
                        append_history("delete", f"Class {name}", f"Deleted {name}", "")
                        show_toast(f"Class {name} deleted")
                        st.rerun()
    else:
        st.info("No classes yet.")


# ----- TAB 3: History (Chrome-style log) -----
with tab3:
    st.header("🕓 History")
    st.markdown("Activity log — add, edit, delete, generate, export.")
    history = load_history()
    if history:
        for entry in history:
            ts = entry.get("ts", "")
            action = entry.get("action", "")
            target = entry.get("target", "")
            summary = entry.get("summary", "")
            details = entry.get("details", "")
            try:
                dt = datetime.fromisoformat(ts)
                ts_fmt = dt.strftime("%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                ts_fmt = ts
            icon = {"add": "➕", "edit": "✏️", "delete": "🗑️", "generate": "🚀", "export": "📥", "clear": "🗑️"}.get(action, "•")
            with st.expander(f"{icon} {ts_fmt} — {summary}"):
                st.markdown(f"**Action:** {action} | **Target:** {target}")
                if details:
                    st.caption(details)
    else:
        st.info("No history yet. Actions will appear here.")


# ----- TAB 4: Class Timetables -----
with tab4:
    st.header("Class Timetables")
    if st.button("🚀 Generate Timetable", type="primary", key="gen_tt"):
        teachers = st.session_state.teachers
        classes = st.session_state.classes
        cfg = st.session_state.config
        if not cfg.days or cfg.periods_per_day < 1:
            st.error("Configure days and periods in the sidebar first!")
        elif not teachers:
            st.error("Add at least one teacher first!")
        elif not classes:
            st.error("Add at least one class first!")
        else:
            with st.spinner("Solving..."):
                tt = solve_timetable(cfg, teachers, classes)
            if tt is None:
                st.error("No solution found!")
            else:
                st.session_state.class_timetable = tt
                # Priority optional — improve only if configs exist
                prio = st.session_state.priority_configs
                if prio:
                    st.session_state.class_timetable = improve_timetable(
                        tt, cfg, classes, prio,
                    )
                st.session_state.teacher_timetable = invert_to_teacher_timetable(
                    st.session_state.class_timetable, cfg
                )
                save_base_timetable(serialize_timetable(st.session_state.class_timetable))
                append_history("generate", "Timetable", "Generated clash-free timetable", "")
                show_toast("Timetable generated!")

    if st.session_state.class_timetable:
        cfg = st.session_state.config
        class_ids = sorted({k[0] for k in st.session_state.class_timetable})
        period_cols = [f"P{p+1}" + (f" ({get_break_name(cfg, p)})" if p in cfg.break_period_indices else "") for p in range(cfg.periods_per_day)]
        col_config = {"Day": st.column_config.TextColumn("Day", width="medium")}
        for pc in period_cols:
            col_config[pc] = st.column_config.TextColumn(pc, width="medium")
        for cid in class_ids:
            st.subheader(f"Class {cid}")
            rows = []
            for d in range(len(cfg.days)):
                row = [cfg.days[d]]
                for p in range(cfg.periods_per_day):
                    if p in cfg.break_period_indices:
                        row.append(get_break_name(cfg, p))
                    else:
                        val = st.session_state.class_timetable.get((cid, d, p), ("", ""))[0]
                        row.append(val if val else "Free period")
                rows.append(row)
            st.dataframe(pd.DataFrame(rows, columns=["Day"] + period_cols), column_config=col_config, use_container_width=True, hide_index=True)


# ----- TAB 5: Teacher Timetables -----
with tab5:
    st.header("Teacher Timetables")
    if st.session_state.teacher_timetable:
        cfg = st.session_state.config
        period_cols = [f"P{p+1}" + (f" ({get_break_name(cfg, p)})" if p in cfg.break_period_indices else "") for p in range(cfg.periods_per_day)]
        col_config = {"Day": st.column_config.TextColumn("Day", width="medium")}
        for pc in period_cols:
            col_config[pc] = st.column_config.TextColumn(pc, width="medium")
        for tid in sorted(st.session_state.teacher_timetable.keys()):
            st.subheader(f"Teacher {tid}")
            tt = st.session_state.teacher_timetable[tid]
            rows = []
            for d in range(len(cfg.days)):
                row = [cfg.days[d]]
                for p in range(cfg.periods_per_day):
                    if p in cfg.break_period_indices:
                        row.append(get_break_name(cfg, p))
                    else:
                        val = tt.get((d, p), ("", ""))
                        row.append(f"{val[0]}: {val[1]}" if val[0] else "Free period")
                rows.append(row)
            st.dataframe(pd.DataFrame(rows, columns=["Day"] + period_cols), column_config=col_config, use_container_width=True, hide_index=True)
    else:
        st.info("Generate a timetable first.")


# ----- TAB 6: Rotation -----
with tab6:
    st.header("Weekly Rotation")
    if st.session_state.class_timetable:
        rotations = generate_rotations(st.session_state.class_timetable, st.session_state.config, 3)
        cfg = st.session_state.config
        period_cols = [f"P{p+1}" + (f" ({get_break_name(cfg, p)})" if p in cfg.break_period_indices else "") for p in range(cfg.periods_per_day)]
        col_config = {"Day": st.column_config.TextColumn("Day", width="medium")}
        for pc in period_cols:
            col_config[pc] = st.column_config.TextColumn(pc, width="medium")
        for week_idx, rot in enumerate(rotations):
            st.subheader(f"Week {week_idx + 1}")
            class_ids = sorted({k[0] for k in rot})
            for cid in class_ids[:2]:
                rows = []
                for d in range(len(cfg.days)):
                    row = [cfg.days[d]]
                    for p in range(cfg.periods_per_day):
                        if p in cfg.break_period_indices:
                            row.append(get_break_name(cfg, p))
                        else:
                            val = rot.get((cid, d, p), ("", ""))[0]
                            row.append(val if val else "Free period")
                    rows.append(row)
                st.caption(f"Class {cid}")
                st.dataframe(pd.DataFrame(rows, columns=["Day"] + period_cols), column_config=col_config, use_container_width=True, hide_index=True)
            if len(class_ids) > 2:
                st.caption(f"... and {len(class_ids)-2} more")
    else:
        st.info("Generate a timetable first.")


# ----- TAB 7: What-If Lab -----
with tab7:
    st.header("🧪 What-If Lab")
    st.markdown("Simulate disruptions. Base timetable is never modified — you see a live overlay.")
    base_tt = st.session_state.class_timetable
    if not base_tt:
        st.info("Generate a timetable first in the Class Timetables tab.")
    else:
        ss = st.session_state.scenario_state
        cfg = st.session_state.config

        # Day selector
        day_idx = st.selectbox(
            "Day",
            range(len(cfg.days)),
            format_func=lambda i: cfg.days[i],
            key="whatif_day",
            index=ss.get("selected_day", 0),
        )
        ss["selected_day"] = day_idx

        # Scenario checkboxes
        st.subheader("Scenarios")
        scenarios = ss.get("scenarios", {})

        def _get(name, default):
            return scenarios.get(name, default)

        c1, c2 = st.columns(2)
        with c1:
            sc_ta = st.checkbox("Teacher absent today", _get("teacher_absent", {}).get("active", False), key="sc_ta")
            sc_sub = st.checkbox("Substitute teacher assigned", _get("substitute", {}).get("active", False), key="sc_sub")
            sc_lab = st.checkbox("Lab unavailable today", _get("lab_unavailable", {}).get("active", False), key="sc_lab")
        with c2:
            sc_short = st.checkbox("Shortened school day", _get("shortened_day", {}).get("active", False), key="sc_short")
            sc_free = st.checkbox("Emergency free period", _get("emergency_free", {}).get("active", False), key="sc_free")

        # Expanded fields per scenario
        teacher_ids = [t.teacher_id for t in st.session_state.teachers]
        class_ids = sorted({k[0] for k in base_tt})

        if sc_ta and teacher_ids:
            with st.expander("Teacher absent — select teacher"):
                saved = scenarios.get("teacher_absent", {}).get("teacher_id")
                idx = teacher_ids.index(saved) if saved in teacher_ids else 0
                absent_tid = st.selectbox("Absent teacher", teacher_ids, index=idx, key="absent_tid")
                scenarios["teacher_absent"] = {"active": True, "teacher_id": absent_tid}
        else:
            scenarios["teacher_absent"] = {"active": False}

        if sc_sub and teacher_ids:
            with st.expander("Substitute — who replaces whom"):
                saved_orig = scenarios.get("substitute", {}).get("original_teacher")
                saved_sub = scenarios.get("substitute", {}).get("substitute_teacher")
                idx_orig = teacher_ids.index(saved_orig) if saved_orig in teacher_ids else 0
                idx_sub = teacher_ids.index(saved_sub) if saved_sub in teacher_ids else min(1, len(teacher_ids) - 1)
                orig = st.selectbox("Original teacher", teacher_ids, index=idx_orig, key="sub_orig")
                sub = st.selectbox("Substitute teacher", teacher_ids, index=idx_sub, key="sub_sub")
                scenarios["substitute"] = {"active": True, "original_teacher": orig, "substitute_teacher": sub}
        else:
            scenarios["substitute"] = {"active": False}

        if sc_lab:
            with st.expander("Lab unavailable — which subjects"):
                default_lab = scenarios.get("lab_unavailable", {}).get("lab_subjects", "Physics, Chemistry, Biology")
                lab_subs = st.text_input("Lab subjects (comma-separated)", default_lab, key="lab_subs")
                scenarios["lab_unavailable"] = {"active": True, "lab_subjects": lab_subs}
        else:
            scenarios["lab_unavailable"] = {"active": False}

        if sc_short:
            with st.expander("Shortened day"):
                new_max = st.number_input(
                    "Max periods today",
                    min_value=1,
                    max_value=cfg.periods_per_day,
                    value=scenarios.get("shortened_day", {}).get("max_periods", 4),
                    key="short_max",
                )
                scenarios["shortened_day"] = {"active": True, "max_periods": new_max}
        else:
            scenarios["shortened_day"] = {"active": False}

        if sc_free and class_ids:
            with st.expander("Emergency free period"):
                saved_cid = scenarios.get("emergency_free", {}).get("class_id")
                saved_p = scenarios.get("emergency_free", {}).get("period", 2)
                idx_c = class_ids.index(saved_cid) if saved_cid in class_ids else 0
                free_cid = st.selectbox("Class", class_ids, index=idx_c, key="free_cid")
                free_p = st.number_input("Period (0-based)", min_value=0, max_value=cfg.periods_per_day - 1, value=saved_p, key="free_p")
                scenarios["emergency_free"] = {"active": True, "class_id": free_cid, "period": free_p}
        else:
            scenarios["emergency_free"] = {"active": False}

        ss["scenarios"] = scenarios
        save_scenario_state(ss)

        # Resolved view
        resolved = apply_scenarios(base_tt, cfg, st.session_state.teachers, st.session_state.classes, ss)
        st.subheader("Live timetable (with scenarios)")
        period_cols = [f"P{p+1}" + (f" ({get_break_name(cfg, p)})" if p in cfg.break_period_indices else "") for p in range(cfg.periods_per_day)]
        col_config = {"Day": st.column_config.TextColumn("Day", width="medium")}
        for pc in period_cols:
            col_config[pc] = st.column_config.TextColumn(pc, width="medium")
        for cid in sorted({k[0] for k in resolved}):
            st.caption(f"Class {cid}")
            rows = []
            for d in range(len(cfg.days)):
                row = [cfg.days[d]]
                for p in range(cfg.periods_per_day):
                    if p in cfg.break_period_indices:
                        row.append(get_break_name(cfg, p))
                    else:
                        val = resolved.get((cid, d, p), ("", ""))[0]
                        row.append(val if val else "Free period")
                rows.append(row)
            df = pd.DataFrame(rows, columns=["Day"] + period_cols)
            st.dataframe(df, column_config=col_config, use_container_width=True, hide_index=True)


# ----- TAB 8: Insights (Heatmaps) -----
with tab8:
    st.header("🔥 Insights")
    st.markdown("Visual heatmaps: overload, fatigue, congestion. Darker = higher load.")
    base_tt = st.session_state.class_timetable
    if not base_tt:
        st.info("Generate a timetable first.")
    else:
        cfg = st.session_state.config
        ss = st.session_state.scenario_state
        resolved = apply_scenarios(base_tt, cfg, st.session_state.teachers, st.session_state.classes, ss)

        heatmap_type = st.selectbox(
            "Heatmap",
            ["Teacher load", "Day congestion", "Class fatigue", "Clash risk"],
            key="heatmap_sel",
        )

        if heatmap_type == "Teacher load":
            load = teacher_load_heatmap(resolved, cfg)
            teacher_max = {t.teacher_id: t.max_periods_per_day for t in st.session_state.teachers}
            styled = render_teacher_load_heatmap(load, cfg.days, teacher_max)
            st.dataframe(styled, use_container_width=True)
            st.caption("Rows = teachers, Cols = days. Darker = more periods.")
        elif heatmap_type == "Day congestion":
            cong = day_congestion_heatmap(resolved, cfg)
            styled = render_day_congestion_heatmap(cong, cfg.days)
            st.dataframe(styled, use_container_width=True)
            st.caption("Total teaching periods per day.")
        elif heatmap_type == "Class fatigue":
            pcs = getattr(st.session_state, "priority_configs", None) or []
            heavy_map = {pc.class_id: pc.heavy_subjects for pc in pcs}
            fatigue = class_fatigue_heatmap(resolved, cfg, heavy_map)
            styled = render_class_fatigue_heatmap(fatigue, cfg.periods_per_day)
            st.dataframe(styled, use_container_width=True)
            st.caption("Rows = classes, Cols = periods. Heavier subjects = hotter.")
        else:
            risks = clash_risk_heatmap(resolved, cfg, st.session_state.teachers)
            st.subheader("Clash risks")
            if risks["teacher_overload"]:
                st.warning("Teacher overload detected:")
                for r in risks["teacher_overload"]:
                    st.write(f"• {r['teacher']}: {r['count']} periods on {cfg.days[r['day']]} (over max)")
            else:
                st.success("No teacher overload detected.")
            if risks["back_to_back_heavy"]:
                st.warning("Back-to-back heavy subjects — review manually.")


# ----- TAB 9: PDF Export -----
with tab9:
    st.header("Export PDFs")
    if st.session_state.class_timetable and st.session_state.teacher_timetable:
        class_tt = flat_to_class_timetables(st.session_state.class_timetable)
        class_pdf = export_class_timetables_pdf(class_tt, st.session_state.config)
        teacher_pdf = export_teacher_timetables_pdf(st.session_state.teacher_timetable, st.session_state.config)
        col1, col2 = st.columns(2)
        with col1:
            if st.download_button(
                "📥 Download Class Timetables PDF",
                data=class_pdf,
                file_name="class_timetables.pdf",
                mime="application/pdf",
                key="dl_class",
            ):
                append_history("export", "PDF", "Exported class timetables PDF", "")
                show_toast("Class PDF downloaded")
        with col2:
            if st.download_button(
                "📥 Download Teacher Timetables PDF",
                data=teacher_pdf,
                file_name="teacher_timetables.pdf",
                mime="application/pdf",
                key="dl_teacher",
            ):
                append_history("export", "PDF", "Exported teacher timetables PDF", "")
                show_toast("Teacher PDF downloaded")
    else:
        st.info("Generate a timetable first.")
