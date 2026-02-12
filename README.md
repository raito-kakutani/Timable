# Smart Timetable Builder

A school timetable generator built with **Python + Streamlit** and **OR-Tools CP-SAT**. Creates clash-free timetables, supports priority-based scheduling, weekly rotation, and exports printable PDFs.

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501 and click **"Load Demo Data"** to try it out.

## Features

| Phase | Feature |
|-------|---------|
| **1** | Core engine: no teacher clashes, no class clashes, all subject periods satisfied |
| **2** | Priority scheduling: place important subjects earlier, avoid back-to-back heavy subjects |
| **3** | Weekly rotation: shift timetable across weeks so the same subject doesn't always land at the same time |
| **4** | PDF export: light-themed, printable A4 timetables for classes and teachers |

## Tech Stack

- **Language:** Python
- **UI:** Streamlit
- **Solver:** OR-Tools CP-SAT
- **Data:** Python objects → pandas
- **PDF:** ReportLab

## Project Structure

```
Timable_V/
├── app.py          # Streamlit UI (tabs, forms, previews)
├── models.py       # Data models (Teacher, Class, SchoolConfig, etc.)
├── solver.py       # OR-Tools constraint solver + scoring + rotation
├── storage.py      # File-based persistence (teachers.json, classes.json)
├── ui_forms.py     # Safe add/edit forms (no widget key mutation)
├── pdf_export.py   # ReportLab PDF export
├── data/           # Persisted data (created automatically)
│   ├── teachers.json
│   ├── classes.json
│   └── priority_configs.json
├── requirements.txt
└── README.md
```

## Usage

1. **Teachers & Classes:** Add teachers (ID, subjects, sections, max periods/day) and classes (subjects with weekly periods and assigned teacher).
2. **Priority (optional):** Mark priority subjects (scheduled earlier), weak subjects, and heavy subjects (avoid back-to-back).
3. **Generate:** Click "Generate Timetable" to solve. The solver finds a valid assignment and optionally improves it with priority scoring.
4. **View:** See class timetables and teacher timetables in separate tabs.
5. **Rotation:** View Week 1/2/3 rotation preview.
6. **Export:** Download class and teacher PDFs.
