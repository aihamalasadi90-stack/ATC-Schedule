import streamlit as st
import pandas as pd
from ortools.sat.python import cp_model

st.set_page_config(page_title="ATC Group B Scheduler", layout="wide")

# ==========================================
# 1. DATABASE CONFIGURATION
# ==========================================
TIME_SLOTS = [
    "08:00-08:30", "08:30-09:00", "09:00-09:30", "09:30-10:00",
    "10:00-10:30", "10:30-11:00", "11:00-11:30", "11:30-12:00",
    "12:00-12:30", "12:30-01:00", "01:00-01:30", "01:30-02:00",
    "02:00-02:30", "02:30-03:00", "03:00-03:30", "03:30-04:00",
    "04:00-04:30", "04:30-05:00", "05:00-05:30", "05:30-06:00",
    "06:00-06:30", "06:30-07:00", "07:00-07:30", "07:30-08:00"
]

CONTROLLERS = [
    {"initials": "TH", "radar": True,  "assist": True},
    {"initials": "RA", "radar": True,  "assist": True},
    {"initials": "ET", "radar": True,  "assist": True},
    {"initials": "SS", "radar": True,  "assist": True},
    {"initials": "CU", "radar": True,  "assist": True},
    {"initials": "HU", "radar": True,  "assist": True},
    {"initials": "ZR", "radar": True,  "assist": True},
    {"initials": "AT", "radar": True,  "assist": True},
    {"initials": "NG", "radar": False, "assist": True},
    {"initials": "BJ", "radar": True,  "assist": True},
    {"initials": "RX", "radar": True,  "assist": True},
    {"initials": "DF", "radar": True,  "assist": True},
    {"initials": "SL", "radar": True,  "assist": True},
]

COLOR_MAP = {
    "TH": "#A6A6A6", "RA": "#7030A0", "ET": "#D60093", "SS": "#00B050",
    "CU": "#F4B183", "HU": "#1F4E78", "ZR": "#FFFFFF", "AT": "#FFFF00",
    "NG": "#00FF00", "BJ": "#FF0000", "RX": "#C00000", "DF": "#FFFFFF",
    "SL": "#FFFFFF", "BREAK": "#E2EFDA"
}

# ==========================================
# 2. USER INTERFACE
# ==========================================
st.title("✈️ Air Traffic Control Automated Scheduler")
st.subheader("Group (B) Shift Configuration")

col1, col2, col3 = st.columns(3)
with col1:
    shift_date = st.date_input("Shift Date", value=pd.to_datetime("2026-04-11"))
with col2:
    shift_type = st.selectbox("Shift Type", ["DAY", "NIGHT"])
with col3:
    airspace_config = st.selectbox("Airspace Configuration", ["Split Sectors (N/H/S/G)", "Combined Radar (R)"])

st.sidebar.header("Select Dedicated FDOs")
fdo_1 = st.sidebar.selectbox("FDO Controller 1", [c["initials"] for c in CONTROLLERS], index=11)
fdo_2 = st.sidebar.selectbox("FDO Controller 2", [c["initials"] for c in CONTROLLERS], index=12)

if airspace_config == "Split Sectors (N/H/S/G)":
    POSITIONS = ["NORTH_RADAR_N", "NORTH_RADAR_H", "NORTH_ASSIST", "FDO", "SOUTH_RADAR_S", "SOUTH_RADAR_G", "SOUTH_ASSIST"]
    DISPLAY_COLS = ["NORTH RADAR (N)", "NORTH RADAR (H)", "NORTH ASSIST", "FDO", "SOUTH RADAR (S)", "SOUTH RADAR (G)", "SOUTH ASSIST"]
else:
    POSITIONS = ["RADAR_R", "BACK_UP", "FDO", "SOUTH_RADAR_S", "SOUTH_RADAR_G", "SOUTH_ASSIST"]
    DISPLAY_COLS = ["RADAR (R)", "BACK UP", "FDO", "SOUTH RADAR (S)", "SOUTH RADAR (G)", "SOUTH ASSIST"]

# ==========================================
# 3. CP-SAT MATHEMATICAL SOLVER ENGINE
# ==========================================
if st.button("⚡ Generate Perfect Fatigue-Compliant Schedule"):
    model = cp_model.CpModel()
    
    x = {}
    for t in range(len(TIME_SLOTS)):
        for p in POSITIONS:
            for c in CONTROLLERS:
                x[t, p, c["initials"]] = model.NewBoolVar(f'x_{t}_{p}_{c["initials"]}')

    for t in range(len(TIME_SLOTS)):
        for p in POSITIONS:
            model.Add(sum(x[t, p, c["initials"]] for c in CONT
")
