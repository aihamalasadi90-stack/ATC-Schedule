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
            model.Add(sum(x[t, p, c["initials"]] for c in CONTROLLERS) == 1)

    for t in range(len(TIME_SLOTS)):
        for c in CONTROLLERS:
            model.Add(sum(x[t, p, c["initials"]] for p in POSITIONS) <= 1)

    for t in range(len(TIME_SLOTS)):
        for c in CONTROLLERS:
            if c["initials"] not in [fdo_1, fdo_2]:
                model.Add(x[t, "FDO", c["initials"]] == 0)

    for t in range(len(TIME_SLOTS)):
        for p in POSITIONS:
            for c in CONTROLLERS:
                if "RADAR" in p and not c["radar"]:
                    model.Add(x[t, p, c["initials"]] == 0)

    radar_positions = [p for p in POSITIONS if "RADAR" in p]
    if radar_positions:
        for c in CONTROLLERS:
            for t in range(len(TIME_SLOTS) - 3):
                model.Add(sum(x[t + i, p, c["initials"]] for p in radar_positions for i in range(4)) <= 3)

    total_shifts_worked = {}
    for c in CONTROLLERS:
        total_shifts_worked[c["initials"]] = model.NewIntVar(0, len(TIME_SLOTS), f'worked_{c["initials"]}')
        model.Add(total_shifts_worked[c["initials"]] == sum(x[t, p, c["initials"]] for t in range(len(TIME_SLOTS)) for p in POSITIONS))
    
    max_work = model.NewIntVar(0, len(TIME_SLOTS), 'max_work')
    min_work = model.NewIntVar(0, len(TIME_SLOTS), 'min_work')
    active_controllers = [c["initials"] for c in CONTROLLERS if c["initials"] not in [fdo_1, fdo_2]]
    
    if active_controllers:
        model.AddMaxEquality(max_work, [total_shifts_worked[initials] for initials in active_controllers])
        model.AddMinEquality(min_work, [total_shifts_worked[initials] for initials in active_controllers])
        model.Minimize(max_work - min_work)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5.0
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        st.success(f"Schedule optimized successfully for {shift_date} ({shift_type})!")
        
        schedule_data = []
        for t in range(len(TIME_SLOTS)):
            row = {"TIME": TIME_SLOTS[t]}
            for idx, p in enumerate(POSITIONS):
                assigned_controller = "—"
                for c in CONTROLLERS:
                    if solver.Value(x[t, p, c["initials"]]) == 1:
                        assigned_controller = c["initials"]
                        break
                row[DISPLAY_COLS[idx]] = assigned_controller
            schedule_data.append(row)
        
        df = pd.DataFrame(schedule_data)
        
        def apply_cell_styles(val):
            color = COLOR_MAP.get(val, "#FFFFFF")
            text_color = "#000000" if color in ["#FFFF00", "#FFFFFF", "#00FF00", "#A6A6A6", "#E2EFDA", "#F4B183"] else "#FFFFFF"
            return f'background-color: {color}; color: {text_color}; font-weight: bold; text-align: center;'

                styled_df = df.style.map(apply_cell_styles, subset=DISPLAY_COLS)
        st.dataframe(styled_df, height=850, use_container_width=True)
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Roster Data as CSV",
            data=csv,
            file_name=f"ATC_Roster_{shift_date}_{shift_type}.csv",
            mime='text/csv'
        )
    else:
        st.error("Could not generate schedule. Please check constraints.")
