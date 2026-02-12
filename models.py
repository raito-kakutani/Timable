"""
🧠 DATA MODELS — Baby-level explanation
========================================
These are like little boxes that hold info about teachers, classes, and subjects.
Think of them as forms you fill out: "Teacher name? What do they teach? How many hours?"
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Teacher:
    """
    One teacher in the school.
    - teacher_id: Unique name or code (e.g. "T1" or "Mr. Smith")
    - subjects: List of subjects they can teach (e.g. ["Math", "Science"])
    - sections: Which class sections they teach (e.g. ["5A", "5B"])
    - max_periods_per_day: How many periods they can work per day (e.g. 6)
    """

    teacher_id: str
    subjects: List[str]
    sections: List[str]
    max_periods_per_day: int = 6


@dataclass
class ClassSubject:
    """
    One subject that a class takes, with its teacher and how many periods per week.
    - subject: Name (e.g. "Math")
    - weekly_periods: How many times per week (e.g. 5)
    - teacher_id: Who teaches it (must match a Teacher)
    """

    subject: str
    weekly_periods: int
    teacher_id: str


@dataclass
class Class:
    """
    One class in the school (e.g. 5A, 6B).
    - class_id: Unique name
    - subjects: List of ClassSubject — what they learn and how often
    """

    class_id: str
    subjects: List[ClassSubject] = field(default_factory=list)


@dataclass
class SchoolConfig:
    """
    School-wide settings: days, periods, and named breaks (Lunch, Fruit break, etc.).
    - days: e.g. ["Mon", "Tue", "Wed", "Thu", "Fri"] or ["11", "12", "13"]
    - periods_per_day: e.g. 8
    - break_periods: period_index (0-based) -> name, e.g. {3: "Lunch", 1: "Fruit break"}
    """

    days: List[str]
    periods_per_day: int
    break_periods: Dict[int, str] = field(default_factory=dict)  # period_idx -> "Lunch", "Fruit break", etc.

    @property
    def break_period_indices(self) -> List[int]:
        """For backward compatibility."""
        return list(self.break_periods.keys())


@dataclass
class ClassPriorityConfig:
    """
    Phase 2: Priority settings for one class.
    - priority_subjects: Should be scheduled earlier in the day
    - weak_subjects: Students struggle — maybe spread out
    - heavy_subjects: Avoid back-to-back with other heavy subjects
    """

    class_id: str
    priority_subjects: List[str] = field(default_factory=list)
    weak_subjects: List[str] = field(default_factory=list)
    heavy_subjects: List[str] = field(default_factory=list)


def get_all_slots(config: SchoolConfig) -> List[tuple]:
    """
    Returns all (day_idx, period_idx) slots that are NOT breaks.
    Like getting all empty boxes on a weekly grid.
    """
    slots = []
    for d in range(len(config.days)):
        for p in range(config.periods_per_day):
            if p not in config.break_period_indices:
                slots.append((d, p))
    return slots


def get_break_name(config: SchoolConfig, period_idx: int) -> str:
    """Return the name for a break period, or 'Break' if unnamed."""
    return config.break_periods.get(period_idx, "Break")
