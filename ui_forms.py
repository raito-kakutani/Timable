"""
🧠 UI FORMS — st.form() to prevent screen jump while typing
==========================================================
Forms batch inputs: no rerun until Submit. Layout stays fixed.
Uses edit_buffer (form_teacher/form_class) for prefilled data — never mutates widget keys.
"""

import streamlit as st
from typing import Optional, Callable

from models import Teacher, Class, ClassSubject


def _teacher_form_key(editing_index: Optional[int], field: str, prefix: str = "main") -> str:
    """Unique key per mode + tab. Never shared with widget-backed keys."""
    if editing_index is None:
        return f"t_{prefix}_{field}_add"
    return f"t_{prefix}_{field}_edit_{editing_index}"


def _class_form_key(editing_index: Optional[int], field: str, prefix: str = "main") -> str:
    if editing_index is None:
        return f"c_{prefix}_{field}_add"
    return f"c_{prefix}_{field}_edit_{editing_index}"


def render_teacher_form(
    editing_index: Optional[int],
    form_data: dict,
    on_save: Callable[[str, list, list, int], None],
    on_cancel: Callable[[], None],
    prefix: str = "main",
) -> None:
    """
    Renders teacher form inside st.form(). No reruns while typing.
    form_data comes from edit_buffer — never from widget keys.
    """
    k = lambda f: _teacher_form_key(editing_index, f, prefix)
    form_key = f"teacher_form_{prefix}_{editing_index if editing_index is not None else 'add'}"

    with st.form(form_key, clear_on_submit=True):
        t_id = st.text_input(
            "Teacher ID",
            value=form_data["id"],
            key=k("id"),
            placeholder="e.g. T1 or Mr. Smith",
        )
        t_subjects = st.text_input(
            "Subjects (comma-separated)",
            value=form_data["subjects"],
            key=k("subjects"),
            placeholder="Math, Science",
        )
        t_sections = st.text_input(
            "Sections/Classes (comma-separated)",
            value=form_data["sections"],
            key=k("sections"),
            placeholder="5A, 5B",
        )
        t_max = st.number_input(
            "Max periods per day",
            min_value=1,
            max_value=10,
            value=form_data.get("max", 6),
            key=k("max"),
        )

        col_add, col_cancel = st.columns(2)
        with col_add:
            submitted = st.form_submit_button(
                "Update Teacher" if editing_index is not None else "Add Teacher"
            )
        with col_cancel:
            cancel_clicked = (
                st.form_submit_button("Cancel") if editing_index is not None else False
            )

    if cancel_clicked:
        on_cancel()
        return
    if submitted and t_id and t_subjects:
        subj_list = [s.strip() for s in t_subjects.split(",") if s.strip()]
        sec_list = [s.strip() for s in t_sections.split(",") if s.strip()]
        on_save(t_id, subj_list, sec_list, int(t_max))


def render_class_form(
    editing_index: Optional[int],
    form_data: dict,
    on_save: Callable[[str, list], None],
    on_cancel: Callable[[], None],
    prefix: str = "main",
) -> None:
    """Class form inside st.form(). No reruns while typing."""
    k = lambda f: _class_form_key(editing_index, f, prefix)
    form_key = f"class_form_{prefix}_{editing_index if editing_index is not None else 'add'}"

    with st.form(form_key, clear_on_submit=True):
        c_id = st.text_input(
            "Class ID",
            value=form_data["id"],
            key=k("id"),
            placeholder="e.g. 5A",
        )
        st.markdown("**Subjects** (one per line: subject, weekly_periods, teacher_id)")
        subjects_text = st.text_area(
            "Subjects",
            value=form_data["subjects"],
            key=k("subjects"),
            placeholder="Math, 5, T1\nEnglish, 4, T2\nScience, 3, T1",
            height=120,
        )

        col_add, col_cancel = st.columns(2)
        with col_add:
            submitted = st.form_submit_button(
                "Update Class" if editing_index is not None else "Add Class"
            )
        with col_cancel:
            cancel_clicked = (
                st.form_submit_button("Cancel") if editing_index is not None else False
            )

    if cancel_clicked:
        on_cancel()
        return
    if submitted and c_id and subjects_text:
        subs = []
        for line in subjects_text.strip().split("\n"):
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 3:
                subs.append(
                    ClassSubject(
                        subject=parts[0],
                        weekly_periods=int(parts[1]),
                        teacher_id=parts[2],
                    )
                )
        if subs:
            on_save(c_id, subs)


def get_edit_buffer_teacher(t: Teacher) -> dict:
    """Build edit_buffer for teacher. Used as form_data value=, never as widget key."""
    return {
        "id": t.teacher_id,
        "subjects": ", ".join(t.subjects),
        "sections": ", ".join(t.sections),
        "max": t.max_periods_per_day,
    }


def get_edit_buffer_class(c: Class) -> dict:
    """Build edit_buffer for class."""
    return {
        "id": c.class_id,
        "subjects": "\n".join(
            f"{cs.subject}, {cs.weekly_periods}, {cs.teacher_id}" for cs in c.subjects
        ),
    }
