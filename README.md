📦 Sports Study ZIP Processor

A deployed web app that batch-processes raw activity-monitor CSV exports from a sports study, classifies movement into physical-activity categories, and returns the results as ready-to-use Excel files — all in the browser, with no data stored on the server.

🔗 Live app: sportscsv-bhagya.streamlit.app

Built and deployed end-to-end with Streamlit on Streamlit Community Cloud.


What it does

Researchers upload a single ZIP containing many participants' raw .csv activity logs. The app:


Parses each semicolon-separated CSV (timestamps, event durations, event types, cumulative step counts).
Cleans & groups consecutive events of the same type into activity bouts.
Engineers features per bout — total duration, steps, doubled steps, minutes, and steps-per-minute (cadence).
Classifies each bout into activity categories using configurable cadence thresholds.
Exports a tidy Excel file per input CSV and bundles everything back into a single downloadable ZIP, preserving the original folder structure.


Files are processed in a temporary directory and are never stored on the server.

Classification logic

Movement bouts (Event Type = 2) are labelled by steps per minute (SPM) against two user-set thresholds:

CategoryRuleBehaviour labelLPA (Light)SPM < LPA limitLIPAMIVA (Moderate–Vigorous)LPA limit ≤ SPM ≤ MIVA limitMPAHPA (High)SPM > MIVA limitVPA

Non-movement events are labelled SED (sedentary, type 0) or STAND (type 1). Thresholds default to 100 and 130 steps/min and are adjustable in the sidebar.

Features


Drag-and-drop ZIP upload (up to 200 MB)
Adjustable LPA / MIVA thresholds with a live classification preview
Batch processing of an entire study in one click
Per-file Excel output, re-zipped with original folder hierarchy
Per-file error reporting (failed files listed, run continues)
Clean, responsive UI; privacy-first (no server-side storage)


Expected input structure

study.zip
├── T1/
│   ├── ControlGroup/        # .csv files
│   └── ExperimentalGroup/   # .csv files
├── T2/
│   ├── ControlGroup/
│   └── ExperimentalGroup/
└── ...


Time-point folders start with T (T1, T2, …)
Each contains ControlGroup and ExperimentalGroup
Only .csv files inside those subfolders are processed


Tech stack

Python · Streamlit · pandas · numpy · openpyxl

Run locally

bashgit clone https://github.com/bhagyamoharana/<repo-name>.git
cd <repo-name>
pip install -r requirements.txt
streamlit run app.py

The app opens at http://localhost:8501.

Deployment

Hosted on Streamlit Community Cloud, deployed directly from this GitHub repo. Pushes to the main branch auto-redeploy the live app.


Built by Shoma (Bhagyabati) Moharana — applied data tooling for sports & physical-activity research.
