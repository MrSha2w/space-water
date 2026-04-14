from __future__ import annotations

from pathlib import Path

from swat_core import CourseConfig, PlotStyle, RunJob, Station, run_course

# -----------------------------------------------------------------------------
# Space-Water 2026 | Session 2
# Edit only this file for course-specific runs.
# Keep swat_core.py unchanged unless you are improving shared logic.
# -----------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

CONFIG = CourseConfig(
    txtinout_dir=DATA_DIR / "txtinout",
    out_dir=OUTPUT_DIR,
    sim_start="1990-01-01",
    sim_end="2024-12-31",
    warmup_years=3,
    obs_scale=1.0,
    obs_monthly_to_yearly="mean",
    flow_var="flo_out",
    day_var="day",
    save_aligned_csv=True,
    save_plotdata_csv=True,
    save_stf_files=True,
    show_plots=False,
    export_plots=True,
    all_metrics=False,
    style=PlotStyle(
        font_family="Times New Roman",
        font_size=24,
        font_size_secondary=24,
        figsize_hydro=(24, 12),
        figsize_seasonal=(24, 12),
        figsize_fdc=(24, 12),
        obs_color="#ff7f0e",
        sim_color="#1f77b4",
        line_width=3.0,
        spine_width=2.5,
        tick_width=2.5,
        marker_size=8.0,
        show_metrics=False,
        title_in_frame=False,
        show_bias_bars=False,
        show_range=True,
        range_mode="minmax",
        show_minmax_whiskers=True,
    ),
)

STATIONS = [
    Station(1084, "genevebout", "Geneve Bout"),
    Station(1079, "genevehalle", "Geneve Halle"),
    Station(1250, "chancy", "Chancy"),
    Station(149, "Tolochenaz", "Tolochenaz"),
    Station(738, "Versoix", "Versoix"),
    Station(281, "Vevey", "Vevey"),
    Station(404, "porteduscex", "Porte du Scex"),
    Station(75, "ecublensboi", "Ecublens les Bois"),
    Station(446, "blatten", "Blatten"),
    Station(141, "reckingen", "Reckingen"),
    Station(730, "brig", "Brig"),
    Station(420, "blattenbeinaters", "Blatten bei Naters"),
    Station(563, "aigle", "Aigle"),
    Station(723, "visp", "Visp"),
    Station(1095, "sion", "Sion"),
    Station(1127, "dardagnylesgranges", "Dardagny les Granges"),
    Station(1451, "branson", "Branson"),
    Station(1460, "martignypontderossettan", "Martigny Pont de Rossettan"),
    Station(148, "Allaman_Le_Coulet", "Allaman Le Coulet"),
    Station(427, "gland_route_suisse", "Gland Route Suisse"),
    Station(81, "gletsch", "Gletsch"),
    Station(78, "oberwald", "Oberwald"),
    Station(547, "Dranse", "Dranse"),
    Station(1928, "Chable-Villette", "Chable-Villette"),
    Station(84, "Chamberonne-Chavannes-près-Renens", "Chamberonne-Chavannes-près-Renens"),
]

JOBS = [
    RunJob(
        name="FLOW",
        variable="flo_out",
        source_file="sdmorph",
        time_step="monthly",
        obs_csv=DATA_DIR / "obs" / "all-obs-q.csv",
        obs_mode="monthly_native",
        metric="NSE",
        y_label_hydro="River discharge (m³ s⁻¹)",
        y_label_seasonal="Monthly mean streamflow (m³ s⁻¹)",
        y_label_fdc="Streamflow (m³ s⁻¹)",
    ),
    # Example for future weeks:
    # RunJob(
    #     name="PHOS",
    #     variable="solp_out",
    #     source_file="sd",
    #     time_step="monthly",
    #     obs_csv=DATA_DIR / "obs" / "all-obs-p-ton.csv",
    #     obs_mode="monthly_ton",
    #     obs_p_species="ptot",
    #     metric="NSE",
    #     y_label_hydro="Total phosphorus load (ton month⁻¹)",
    #     y_label_seasonal="Monthly mean phosphorus load (ton month⁻¹)",
    #     y_label_fdc="Phosphorus load (ton month⁻¹)",
    # ),
]


def main() -> None:
    run_course(CONFIG, STATIONS, JOBS)


if __name__ == "__main__":
    main()
