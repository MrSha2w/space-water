from pathlib import Path
import pandas as pd

# ------------------------------------------------------------
# Session 2 configuration for Space-Water 2026
# ------------------------------------------------------------
# Edit ONLY this file when you want to change:
# - input/output paths
# - stations
# - jobs
# - plotting defaults
#
# This file is designed to be imported by:
# - src/session_runner.py
# - Jupyter notebooks inside this session
# ------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
OUTPUTS_DIR = REPO_ROOT / "outputs" / "session_02"

# ------------------------------------------------------------
# USER PATHS
# ------------------------------------------------------------
# Change these paths on your own computer.
TXTINOUT_DIR = Path(r"D:\Leman Model-Jan2026\auto_calibration\Default26-wetland&drawdawn")
OBS_Q_CSV = Path(r"D:\Leman Model-Jan2026\obs\all-obs-q.csv")
OBS_ET_CSV = Path(r"D:\Leman Model-Jan2026\obs\all-obs-et.csv")
OBS_P_CSV = Path(r"D:\Leman Model-Jan2026\obs\all-obs-p-ton.csv")

# ------------------------------------------------------------
# SIMULATION WINDOW
# ------------------------------------------------------------
SIM_START = "1990-01-01"
SIM_END = "2024-12-31"
WARMUP_YEARS = 3
CAL_START = (pd.to_datetime(SIM_START) + pd.DateOffset(years=WARMUP_YEARS)).strftime("%Y-%m-%d")
CAL_END = SIM_END

# ------------------------------------------------------------
# GLOBAL OPTIONS
# ------------------------------------------------------------
OBS_SCALE = 1.0
OBS_MONTHLY_TO_YEARLY = "mean"   # "mean" | "sum" | "flow_weighted_mean"
FLOW_VAR = "flo_out"
DAY_VAR = "day"
SAVE_PLOTDATA_CSV = True
SHOW_PLOTS = True
SHOW_METRICS_ON_PLOTS = False
TITLE_IN_FRAME = False
ALL_METRICS = False

# ------------------------------------------------------------
# PLOT STYLE
# ------------------------------------------------------------
PLOT = {
    "font_family": "Times New Roman",
    "font_size": 28,
    "font_size_large": 29,
    "figsize_hydro": (24, 12),
    "figsize_seasonal": (24, 12),
    "figsize_fdc": (24, 12),
    "obs_color": "#ff7f0e",
    "sim_color": "#1f77b4",
    "line_width": 3,
    "spine_width": 2.5,
    "tick_width": 3,
    "marker_size": 8,
    "seasonal_show_bias_bars": False,
    "seasonal_show_range": True,
    "seasonal_range_mode": "minmax",
    "seasonal_show_minmax_whiskers": True,
}

# ------------------------------------------------------------
# STATIONS
# ------------------------------------------------------------
# Simple mode:
#   404: "porteduscex"
#
# Rich mode:
#   404: {"obs_col": "porteduscex", "title": "Porte du Scex"}
#
# For phosphorus stations you can also use:
#   "p_species": "po4" or "ptot"
STATIONS = {
    1084: {"obs_col": "genevebout", "title": "genevebout"},
    1079: {"obs_col": "genevehalle", "title": "genevehalle"},
    1250: {"obs_col": "chancy", "title": "chancy"},
    149: {"obs_col": "Tolochenaz", "title": "Tolochenaz"},
    738: {"obs_col": "Versoix", "title": "Versoix"},
    281: {"obs_col": "Vevey", "title": "Vevey"},
    404: {"obs_col": "porteduscex", "title": "Porte du Scex"},
    75: {"obs_col": "ecublensboi", "title": "ecublensboi"},
    446: {"obs_col": "blatten", "title": "blatten"},
    141: {"obs_col": "reckingen", "title": "reckingen"},
    730: {"obs_col": "brig", "title": "brig"},
    420: {"obs_col": "blattenbeinaters", "title": "blattenbeinaters"},
    563: {"obs_col": "aigle", "title": "aigle"},
    723: {"obs_col": "visp", "title": "visp"},
    1095: {"obs_col": "sion", "title": "sion"},
    1127: {"obs_col": "dardagnylesgranges", "title": "dardagnylesgranges"},
    1451: {"obs_col": "branson", "title": "branson"},
    1460: {"obs_col": "martignypontderossettan", "title": "martignypontderossettan"},
    148: {"obs_col": "Allaman_Le_Coulet", "title": "Allaman_Le_Coulet"},
    427: {"obs_col": "gland_route_suisse", "title": "gland_route_suisse"},
    81: {"obs_col": "gletsch", "title": "gletsch"},
    78: {"obs_col": "oberwald", "title": "oberwald"},
    547: {"obs_col": "Dranse", "title": "Dranse"},
    1928: {"obs_col": "Chable-Villette", "title": "Chable-Villette"},
    84: {"obs_col": "Chamberonne-Chavannes-près-Renens", "title": "Chamberonne-Chavannes-près-Renens"},
}

# ------------------------------------------------------------
# JOBS
# ------------------------------------------------------------
# Keep only the jobs you want to teach in Session 2.
# You can add new jobs later without touching src/swat_core.py.
JOBS = [
    {
        "name": "FLOW",
        "variable": "flo_out",
        "source_file": "sdmorph",
        "time_step": "monthly",
        "obs_csv": str(OBS_Q_CSV),
        "obs_mode": "monthly_native",
        "obs_p_species": None,
        "metric": "NSE",
        "y_label_hydro": "Streamflow (m³ s⁻¹)",
        "y_label_seasonal": "Monthly Mean Streamflow",
        "y_label_fdc": "Streamflow (m³ s⁻¹)",
    },

    # Example ET job:
    # {
    #     "name": "ET",
    #     "variable": "et",
    #     "source_file": "lwb",
    #     "time_step": "monthly",
    #     "obs_csv": str(OBS_ET_CSV),
    #     "obs_mode": "monthly_native",
    #     "obs_p_species": None,
    #     "metric": "NSE",
    #     "y_label_hydro": "Evapotranspiration",
    #     "y_label_seasonal": "Monthly Mean ET",
    #     "y_label_fdc": "Evapotranspiration",
    # },

    # Example phosphorus concentration / load jobs:
    # {
    #     "name": "PHOS",
    #     "variable": "solp_out",
    #     "source_file": "sd",
    #     "time_step": "monthly",
    #     "obs_csv": str(OBS_P_CSV),
    #     "obs_mode": "monthly_mgl",
    #     "obs_p_species": "ptot",
    #     "metric": "NSE",
    #     "y_label_hydro": "Total phosphorus concentration (mg L⁻¹)",
    #     "y_label_seasonal": "Monthly Mean Total Phosphorus",
    #     "y_label_fdc": "Total phosphorus concentration (mg L⁻¹)",
    # },
]

SESSION = {
    "name": "session_02",
    "title": "Space-Water 2026 | Session 2",
    "txtinout_dir": TXTINOUT_DIR,
    "outputs_dir": OUTPUTS_DIR,
    "sim_start": SIM_START,
    "sim_end": SIM_END,
    "cal_start": CAL_START,
    "cal_end": CAL_END,
    "warmup_years": WARMUP_YEARS,
    "obs_scale": OBS_SCALE,
    "obs_monthly_to_yearly": OBS_MONTHLY_TO_YEARLY,
    "flow_var": FLOW_VAR,
    "day_var": DAY_VAR,
    "save_plotdata_csv": SAVE_PLOTDATA_CSV,
    "show_plots": SHOW_PLOTS,
    "show_metrics_on_plots": SHOW_METRICS_ON_PLOTS,
    "title_in_frame": TITLE_IN_FRAME,
    "all_metrics": ALL_METRICS,
    "plot": PLOT,
}
