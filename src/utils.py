from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, Optional, Sequence
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DEBUG = str(os.getenv("SWAT_DEBUG", "")).strip().lower() in {"1", "true", "yes", "y", "on"}

FILE_KIND = {
    "sdmorph": "channel_sdmorph_mon.txt",
    "sd": "channel_sd_mon.txt",
    "ru": "ru_mon.txt",
    "reservoir": "reservoir_mon.txt",
    "hwb": "hru_wb_mon.txt",
    "lwb": "lsunit_wb_mon.txt",
    "sdmorph-yr": "channel_sdmorph_yr.txt",
    "sd-yr": "channel_sd_yr.txt",
    "ru-yr": "ru_yr.txt",
    "reservoir-yr": "reservoir_yr.txt",
    "hwb-yr": "hru_wb_yr.txt",
    "lwb-yr": "lsunit_wb_yr.txt",
}


@dataclass(slots=True)
class Station:
    gis_id: int
    obs_col: str
    title: str
    p_species: Optional[str] = None


@dataclass(slots=True)
class PlotStyle:
    font_family: str = "Times New Roman"
    font_size: int = 20
    font_size_secondary: int = 20
    figsize_hydro: tuple[int, int] = (24, 12)
    figsize_seasonal: tuple[int, int] = (24, 12)
    figsize_fdc: tuple[int, int] = (24, 12)
    obs_color: str = "#ff7f0e"
    sim_color: str = "#1f77b4"
    line_width: float = 2.8
    spine_width: float = 2.2
    tick_width: float = 2.2
    marker_size: float = 7.0
    show_metrics: bool = False
    title_in_frame: bool = False
    show_bias_bars: bool = False
    show_range: bool = True
    range_mode: str = "minmax"
    show_minmax_whiskers: bool = True


@dataclass(slots=True)
class RunJob:
    name: str
    variable: str
    source_file: str
    time_step: str
    obs_csv: Path
    obs_mode: str
    metric: str = "NSE"
    obs_p_species: Optional[str] = None
    y_label_hydro: Optional[str] = None
    y_label_seasonal: Optional[str] = None
    y_label_fdc: Optional[str] = None


@dataclass(slots=True)
class CourseConfig:
    txtinout_dir: Path
    out_dir: Path
    sim_start: str
    sim_end: str
    warmup_years: int = 3
    obs_scale: float = 1.0
    obs_monthly_to_yearly: str = "mean"
    flow_var: str = "flo_out"
    day_var: str = "day"
    save_aligned_csv: bool = True
    save_plotdata_csv: bool = True
    save_stf_files: bool = True
    show_plots: bool = False
    export_plots: bool = True
    all_metrics: bool = False
    style: PlotStyle = field(default_factory=PlotStyle)

    @property
    def cal_start(self) -> str:
        return (pd.to_datetime(self.sim_start) + pd.DateOffset(years=self.warmup_years)).strftime("%Y-%m-%d")

    @property
    def cal_end(self) -> str:
        return self.sim_end


def dbg(message: str) -> None:
    if DEBUG:
        print(f"[SWAT_DEBUG] {message}")


def dbg_series(name: str, series: Optional[pd.Series]) -> None:
    if not DEBUG:
        return
    if series is None:
        print(f"[SWAT_DEBUG] {name}: None")
        return
    clean = series.replace([np.inf, -np.inf], np.nan).dropna()
    if clean.empty:
        print(f"[SWAT_DEBUG] {name}: empty")
        return
    print(
        f"[SWAT_DEBUG] {name}: n={len(clean)} min={clean.min()} max={clean.max()} "
        f"mean={clean.mean()} head5={clean.head(5).to_dict()}"
    )


def normalize_source_file(source_file: str, time_step: str) -> str:
    source = source_file.strip().lower()
    step = time_step.strip().lower()
    if step in {"yearly", "annual", "yr", "y"}:
        return source if source.endswith("-yr") else f"{source}-yr"
    return source[:-3] if source.endswith("-yr") else source


def resolve_txt_file(source_file: str, time_step: str) -> str:
    key = normalize_source_file(source_file, time_step)
    if key not in FILE_KIND:
        raise ValueError(f"Unsupported source_file={source_file!r}. Allowed values: {sorted(FILE_KIND)}")
    return FILE_KIND[key]


def month_end_index(values, dayfirst: bool = False) -> pd.DatetimeIndex:
    dt = pd.to_datetime(values, errors="coerce", dayfirst=dayfirst)
    return dt.dt.to_period("M").dt.to_timestamp("M")


def year_end_index(values, dayfirst: bool = False) -> pd.DatetimeIndex:
    dt = pd.to_datetime(values, errors="coerce", dayfirst=dayfirst)
    return dt.dt.to_period("Y").dt.to_timestamp("Y")


def days_in_year(idx: pd.DatetimeIndex) -> np.ndarray:
    return np.array([366 if pd.Timestamp(year, 12, 31).is_leap_year else 365 for year in idx.year], dtype=float)


def clean_series(series: pd.Series) -> pd.Series:
    out = series.replace([np.inf, -np.inf], np.nan).dropna().sort_index()
    if out.index.has_duplicates:
        out = out.groupby(level=0).mean()
    return out


def as_named_series(value, name: str) -> pd.Series:
    if isinstance(value, pd.Series):
        out = value.copy()
        out.name = name
        return out
    if isinstance(value, pd.DataFrame):
        if value.shape[1] == 1:
            return value.iloc[:, 0].rename(name)
        if "value" in value.columns:
            return value["value"].rename(name)
        return value.iloc[:, 0].rename(name)
    return pd.Series(np.asarray(value), name=name)


def extract_stf_from_txtinout(
    txtinout_dir: Path,
    gis_ids: Sequence[int],
    cali_start_day: str,
    cali_end_day: str,
    output_dir: Path,
    variable: str,
    source_file: str,
    time_step: str,
) -> list[Path]:
    """Extract one STF file per gis_id from a SWAT+ periodic output table."""
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = txtinout_dir / resolve_txt_file(source_file, time_step)
    if not file_path.exists():
        raise FileNotFoundError(f"Missing TxtInOut file: {file_path}")

    df = pd.read_csv(file_path, sep=r"\s+", engine="python", skiprows=[0, 2])
    if "gis_id" not in df.columns:
        raise ValueError(f"'gis_id' column not found in {file_path.name}")
    if variable not in df.columns:
        raise ValueError(f"'{variable}' column not found in {file_path.name}")

    df["gis_id"] = pd.to_numeric(df["gis_id"], errors="coerce").astype("Int64")
    df[variable] = pd.to_numeric(df[variable], errors="coerce")

    cal_start = pd.to_datetime(cali_start_day)
    cal_end = pd.to_datetime(cali_end_day)
    step = time_step.strip().lower()
    created: list[Path] = []

    for gid in gis_ids:
        values = df.loc[df["gis_id"] == int(gid), variable].reset_index(drop=True)
        out_path = output_dir / f"stf_{int(gid):03d}_{variable}.txt"
        if values.empty:
            if out_path.exists():
                out_path.unlink()
            continue

        if step in {"yearly", "annual", "yr", "y"}:
            index = pd.date_range(pd.Timestamp(cal_start.year, 12, 31), periods=len(values), freq="YE")
            series = pd.Series(pd.to_numeric(values, errors="coerce").values, index=index, name="sim")
            series = series.loc[pd.Timestamp(cal_start.year, 12, 31): pd.Timestamp(cal_end.year, 12, 31)]
        else:
            index = pd.date_range(cal_start, periods=len(values), freq="ME")
            series = pd.Series(pd.to_numeric(values, errors="coerce").values, index=index, name="sim")
            series = series.loc[cal_start:cal_end]

        series = clean_series(series)
        if series.empty:
            if out_path.exists():
                out_path.unlink()
            continue

        series.to_csv(out_path, sep="\t", index=True, header=False, float_format="%.7e")
        created.append(out_path)

    dbg(f"Extracted {len(created)} STF files for variable={variable}, time_step={time_step}")
    return created


def read_stf(path: Path, start_date: str, end_date: str, time_step: str, dayfirst: bool = False) -> pd.Series:
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    if (not path.exists()) or path.stat().st_size == 0:
        return pd.Series(dtype=float, name="sim")

    try:
        df = pd.read_csv(path, sep=r"\s+|\t", engine="python", header=None)
    except pd.errors.EmptyDataError:
        return pd.Series(dtype=float, name="sim")

    step = time_step.strip().lower()
    if df.shape[1] == 1:
        n = len(df)
        if n == 0:
            return pd.Series(dtype=float, name="sim")
        if step in {"yearly", "annual", "yr", "y"}:
            idx = pd.date_range(pd.Timestamp(start.year, 12, 31), periods=n, freq="YE")
        else:
            idx = pd.date_range(start, periods=n, freq="ME")
        series = pd.Series(pd.to_numeric(df.iloc[:, 0], errors="coerce").values, index=idx, name="sim")
    else:
        if step in {"yearly", "annual", "yr", "y"}:
            dates = year_end_index(df.iloc[:, 0], dayfirst=dayfirst)
        else:
            dates = month_end_index(df.iloc[:, 0], dayfirst=dayfirst)
        values = pd.to_numeric(df.iloc[:, 1], errors="coerce")
        series = pd.Series(values.values, index=dates, name="sim")

    series = clean_series(series)
    if step in {"yearly", "annual", "yr", "y"}:
        series.index = series.index.to_period("Y").to_timestamp("Y")
        return series.loc[pd.Timestamp(start.year, 12, 31): pd.Timestamp(end.year, 12, 31)]

    series.index = series.index.to_period("M").to_timestamp("M")
    return series.loc[start.to_period("M").to_timestamp("M"): end.to_period("M").to_timestamp("M")]


def read_obs_csv(
    obs_csv: Path,
    wanted_cols: Sequence[str],
    start: str,
    end: str,
    time_step: str,
    dayfirst: bool = True,
) -> pd.DataFrame:
    df = pd.read_csv(obs_csv, na_values=[-99, "-99", -99.0], keep_default_na=True)
    date_candidates = [c for c in df.columns if c.lower() in {"date", "datetime", "time", "year"}]
    date_col = date_candidates[0] if date_candidates else df.columns[0]

    step = time_step.strip().lower()
    if step in {"yearly", "annual", "yr", "y"}:
        raw = df[date_col]
        dt = pd.to_datetime(raw, errors="coerce", dayfirst=dayfirst)
        if dt.isna().all():
            years = pd.to_numeric(raw, errors="coerce")
            df = df.loc[years.notna()].copy()
            idx = pd.to_datetime(years.dropna().astype(int).astype(str) + "-12-31", errors="coerce")
        else:
            idx = dt.dt.to_period("Y").dt.to_timestamp("Y")
    else:
        idx = month_end_index(df[date_col], dayfirst=dayfirst)

    df = df.drop(columns=[date_col], errors="ignore")
    for column in df.columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df.index = idx
    df = df.dropna(how="all").sort_index()
    if df.index.has_duplicates:
        df = df.groupby(level=0).mean()

    start_dt = pd.to_datetime(start)
    end_dt = pd.to_datetime(end)
    if step in {"yearly", "annual", "yr", "y"}:
        df = df.loc[pd.Timestamp(start_dt.year, 12, 31): pd.Timestamp(end_dt.year, 12, 31)]
    else:
        df = df.loc[start_dt.to_period("M").to_timestamp("M"): end_dt.to_period("M").to_timestamp("M")]

    keep = [col for col in wanted_cols if col in df.columns]
    return df[keep].copy() if keep else df.copy()


def build_sim_series(
    *,
    txtinout_dir: Path,
    out_dir: Path,
    gis_id: int,
    cal_start: str,
    cal_end: str,
    time_step: str,
    source_file: str,
    variable: str,
) -> pd.Series:
    extract_stf_from_txtinout(
        txtinout_dir=txtinout_dir,
        gis_ids=[gis_id],
        cali_start_day=cal_start,
        cali_end_day=cal_end,
        output_dir=out_dir,
        variable=variable,
        source_file=source_file,
        time_step=time_step,
    )
    stf_path = out_dir / f"stf_{int(gis_id):03d}_{variable}.txt"
    series = read_stf(stf_path, start_date=cal_start, end_date=cal_end, time_step=time_step)
    dbg_series(f"sim::{variable}::{gis_id}", series)
    return series


def build_phosphorus_series(
    *,
    txtinout_dir: Path,
    out_dir: Path,
    gis_id: int,
    cal_start: str,
    cal_end: str,
    time_step: str,
    source_file: str,
    obs_p_species: str,
) -> pd.Series:
    species = (obs_p_species or "").strip().lower()
    if species not in {"po4", "ptot"}:
        raise ValueError("obs_p_species must be 'po4' or 'ptot'")

    solp = build_sim_series(
        txtinout_dir=txtinout_dir,
        out_dir=out_dir,
        gis_id=gis_id,
        cal_start=cal_start,
        cal_end=cal_end,
        time_step=time_step,
        source_file=source_file,
        variable="solp_out",
    )
    if species == "po4":
        return clean_series(solp)

    sedp = build_sim_series(
        txtinout_dir=txtinout_dir,
        out_dir=out_dir,
        gis_id=gis_id,
        cal_start=cal_start,
        cal_end=cal_end,
        time_step=time_step,
        source_file=source_file,
        variable="sedp_out",
    )
    merged = pd.concat([solp.rename("solp"), sedp.rename("sedp")], axis=1).fillna(0.0)
    return clean_series((merged["solp"] + merged["sedp"]).rename("ptot_sim"))


def convert_monthly_load_kg_to_mgl(load_kg: pd.Series, flow_m3s: pd.Series, days: pd.Series) -> pd.Series:
    load = clean_series(as_named_series(load_kg, "load_kg"))
    flow = clean_series(as_named_series(flow_m3s, "flow_m3s"))
    day = clean_series(as_named_series(days, "days"))
    aligned = pd.concat([load, flow, day], axis=1).dropna()
    if aligned.empty:
        return pd.Series(dtype=float, name="mgL")
    out = (aligned["load_kg"] * 1000000.0) / (aligned["flow_m3s"] * aligned["days"] * 86400.0)
    return clean_series(out.rename("mgL"))


def convert_monthly_load_kg_to_ton(load_kg: pd.Series) -> pd.Series:
    return clean_series((clean_series(as_named_series(load_kg, "load_kg")) / 1000.0).rename("ton"))


def convert_yearly_kg_to_kgday(sim_kgyr: pd.Series) -> pd.Series:
    series = clean_series(as_named_series(sim_kgyr, "kgyr"))
    if series.empty:
        return series.rename("kgday")
    out = series.values / days_in_year(pd.DatetimeIndex(series.index))
    return clean_series(pd.Series(out, index=series.index, name="kgday"))


def aggregate_monthly_to_yearly(obs_monthly: pd.Series, how: str = "mean", flow_monthly: Optional[pd.Series] = None) -> pd.Series:
    series = clean_series(as_named_series(obs_monthly, "obs"))
    series.index = series.index.to_period("M").to_timestamp("M")
    method = how.strip().lower()
    if method == "sum":
        out = series.resample("YE").sum()
    elif method == "mean":
        out = series.resample("YE").mean()
    elif method in {"flow_weighted_mean", "fwmean", "fw_mean"}:
        if flow_monthly is None:
            raise ValueError("flow_monthly is required for flow_weighted_mean")
        flow = clean_series(as_named_series(flow_monthly, "Q"))
        flow.index = flow.index.to_period("M").to_timestamp("M")
        aligned = pd.concat([series.rename("c"), flow.rename("q")], axis=1).dropna()
        out = (aligned["c"] * aligned["q"]).resample("YE").sum() / aligned["q"].resample("YE").sum()
    else:
        raise ValueError("how must be one of: mean, sum, flow_weighted_mean")
    out.index = out.index.to_period("Y").to_timestamp("Y")
    return clean_series(out)


def prepare_sim_for_obs(
    *,
    time_step: str,
    obs_mode: str,
    sim_series: pd.Series,
    flow_series: Optional[pd.Series] = None,
    day_series: Optional[pd.Series] = None,
) -> pd.Series:
    mode = obs_mode.strip().lower()
    step = time_step.strip().lower()

    if mode == "monthly_native":
        return clean_series(sim_series)
    if mode == "monthly_ton":
        if step not in {"monthly", "mon", "m"}:
            raise ValueError("obs_mode='monthly_ton' requires monthly simulation")
        return convert_monthly_load_kg_to_ton(sim_series)
    if mode == "monthly_mgl":
        if step not in {"monthly", "mon", "m"}:
            raise ValueError("obs_mode='monthly_mgL' requires monthly simulation")
        if flow_series is None or day_series is None:
            raise ValueError("monthly_mgL conversion requires flow_series and day_series")
        return convert_monthly_load_kg_to_mgl(sim_series, flow_series, day_series)
    if mode == "annual_kgyr":
        if step not in {"yearly", "annual", "yr", "y"}:
            raise ValueError("obs_mode='annual_kgyr' requires yearly simulation")
        return clean_series(sim_series)
    if mode == "annual_kgday":
        if step not in {"yearly", "annual", "yr", "y"}:
            raise ValueError("obs_mode='annual_kgday' requires yearly simulation")
        return convert_yearly_kg_to_kgday(sim_series)
    raise ValueError("Unsupported obs_mode. Use one of: monthly_native, monthly_ton, monthly_mgl, annual_kgyr, annual_kgday")


def kge(obs: np.ndarray, sim: np.ndarray) -> float:
    mask = np.isfinite(obs) & np.isfinite(sim)
    if mask.sum() < 2:
        return np.nan
    o = np.asarray(obs[mask], dtype=float)
    s = np.asarray(sim[mask], dtype=float)
    r = np.corrcoef(o, s)[0, 1]
    if not np.isfinite(r):
        return np.nan
    alpha = np.std(s, ddof=1) / (np.std(o, ddof=1) + 1e-12)
    beta = (np.mean(s) + 1e-12) / (np.mean(o) + 1e-12)
    return 1.0 - np.sqrt((r - 1.0) ** 2 + (alpha - 1.0) ** 2 + (beta - 1.0) ** 2)


def pbias(obs: np.ndarray, sim: np.ndarray) -> float:
    mask = np.isfinite(obs) & np.isfinite(sim)
    if mask.sum() < 1:
        return np.nan
    o = np.asarray(obs[mask], dtype=float)
    s = np.asarray(sim[mask], dtype=float)
    denom = np.sum(o)
    if abs(denom) < 1e-12:
        return np.nan
    return 100.0 * np.sum(o - s) / denom


def nse(obs: pd.Series, sim: pd.Series) -> float:
    aligned = pd.concat([obs.rename("obs"), sim.rename("sim")], axis=1).dropna()
    if aligned.empty:
        return np.nan
    denom = np.sum((aligned["obs"] - aligned["obs"].mean()) ** 2)
    if denom <= 0 or not np.isfinite(denom):
        return np.nan
    return 1.0 - np.sum((aligned["sim"] - aligned["obs"]) ** 2) / denom


def r2(obs: pd.Series, sim: pd.Series) -> float:
    aligned = pd.concat([obs.rename("obs"), sim.rename("sim")], axis=1).dropna()
    if len(aligned) < 2:
        return np.nan
    corr = np.corrcoef(aligned["obs"].values, aligned["sim"].values)[0, 1]
    return corr * corr


def rmse(obs: pd.Series, sim: pd.Series) -> float:
    aligned = pd.concat([obs.rename("obs"), sim.rename("sim")], axis=1).dropna()
    if aligned.empty:
        return np.nan
    return float(np.sqrt(np.mean((aligned["sim"] - aligned["obs"]) ** 2)))


def mse(obs: pd.Series, sim: pd.Series) -> float:
    aligned = pd.concat([obs.rename("obs"), sim.rename("sim")], axis=1).dropna()
    if aligned.empty:
        return np.nan
    return float(np.mean((aligned["sim"] - aligned["obs"]) ** 2))


def eval_metric(metric: str, obs: pd.Series, sim: pd.Series) -> float:
    key = metric.strip().upper()
    if key == "NSE":
        return nse(obs, sim)
    if key == "KGE":
        return kge(obs.values, sim.values)
    if key == "PBIAS":
        return pbias(obs.values, sim.values)
    if key == "R2":
        return r2(obs, sim)
    if key == "RMSE":
        return rmse(obs, sim)
    if key == "MSE":
        return mse(obs, sim)
    raise ValueError("metric must be one of NSE, KGE, PBIAS, R2, RMSE, MSE")


def eval_all_metrics(obs: pd.Series, sim: pd.Series) -> Dict[str, float]:
    return {name: eval_metric(name, obs, sim) for name in ["NSE", "KGE", "PBIAS", "R2", "RMSE", "MSE"]}


def _final_title(base: str, metric_name: Optional[str], metric_value: Optional[float]) -> str:
    if metric_name and metric_value is not None and np.isfinite(metric_value):
        return f"{base} | {metric_name}={metric_value:.3f}"
    return base


def _style_axes(ax: plt.Axes, style: PlotStyle) -> None:
    for spine in ax.spines.values():
        spine.set_linewidth(style.spine_width)
    ax.tick_params(width=style.tick_width, labelsize=style.font_size)


def _draw_title(ax: plt.Axes, title: str, style: PlotStyle) -> None:
    if style.title_in_frame:
        ax.text(
            0.01,
            0.98,
            title,
            transform=ax.transAxes,
            va="top",
            ha="left",
            fontsize=style.font_size,
            fontname=style.font_family,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.75),
        )
    else:
        ax.set_title(title, fontsize=style.font_size, fontname=style.font_family)


def plot_hydrograph(
    obs: pd.Series,
    sim: pd.Series,
    title: str,
    ylabel: str,
    save_path: Optional[Path],
    style: PlotStyle,
    show: bool,
    metric_name: str,
) -> None:
    aligned = pd.concat([clean_series(obs).rename("obs"), clean_series(sim).rename("sim")], axis=1).dropna()
    if aligned.empty:
        return

    metric_value = eval_metric(metric_name, aligned["obs"], aligned["sim"]) if style.show_metrics else None
    fig, ax = plt.subplots(figsize=style.figsize_hydro)
    _style_axes(ax, style)
    ax.plot(aligned.index, aligned["obs"].values, label="OBS", linewidth=style.line_width, color=style.obs_color)
    ax.plot(aligned.index, aligned["sim"].values, label="SIM", linewidth=style.line_width, color=style.sim_color)
    ax.set_ylabel(ylabel, fontsize=style.font_size, fontname=style.font_family)
    ax.set_xlabel("", fontsize=style.font_size, fontname=style.font_family)
    ax.margins(x=0)
    ax.grid(True, alpha=0.3)
    ax.legend()
    _draw_title(ax, _final_title(title, metric_name if style.show_metrics else None, metric_value), style)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=200)
    if show:
        plt.show()
    plt.close(fig)


def plot_seasonal(
    obs: pd.Series,
    sim: pd.Series,
    title: str,
    ylabel: str,
    save_path: Optional[Path],
    style: PlotStyle,
    show: bool,
    metric_name: str,
) -> None:
    aligned = pd.concat([clean_series(obs).rename("obs"), clean_series(sim).rename("sim")], axis=1).dropna()
    if aligned.empty:
        return
    aligned["month"] = aligned.index.month
    obs_mean = aligned.groupby("month")["obs"].mean()
    sim_mean = aligned.groupby("month")["sim"].mean()

    metric_value = eval_metric(metric_name, aligned["obs"], aligned["sim"]) if style.show_metrics else None
    fig, ax = plt.subplots(figsize=style.figsize_seasonal)
    _style_axes(ax, style)
    ax.plot(obs_mean.index, obs_mean.values, marker="o", color=style.obs_color, linewidth=style.line_width, markersize=style.marker_size, label="OBS")
    ax.plot(sim_mean.index, sim_mean.values, marker="o", color=style.sim_color, linewidth=style.line_width, markersize=style.marker_size, label="SIM")

    if style.show_range:
        if style.range_mode == "minmax":
            obs_low = aligned.groupby("month")["obs"].min()
            obs_high = aligned.groupby("month")["obs"].max()
            sim_low = aligned.groupby("month")["sim"].min()
            sim_high = aligned.groupby("month")["sim"].max()
        elif style.range_mode == "q10_q90":
            obs_low = aligned.groupby("month")["obs"].quantile(0.10)
            obs_high = aligned.groupby("month")["obs"].quantile(0.90)
            sim_low = aligned.groupby("month")["sim"].quantile(0.10)
            sim_high = aligned.groupby("month")["sim"].quantile(0.90)
        elif style.range_mode == "q25_q75":
            obs_low = aligned.groupby("month")["obs"].quantile(0.25)
            obs_high = aligned.groupby("month")["obs"].quantile(0.75)
            sim_low = aligned.groupby("month")["sim"].quantile(0.25)
            sim_high = aligned.groupby("month")["sim"].quantile(0.75)
        else:
            raise ValueError("range_mode must be minmax, q10_q90, or q25_q75")
        ax.fill_between(obs_mean.index, obs_low.values, obs_high.values, alpha=0.12, color=style.obs_color, label=f"OBS {style.range_mode}")
        ax.fill_between(sim_mean.index, sim_low.values, sim_high.values, alpha=0.12, color=style.sim_color, label=f"SIM {style.range_mode}")
        if style.range_mode == "minmax" and style.show_minmax_whiskers:
            for month in obs_mean.index:
                ax.vlines(month, obs_low.loc[month], obs_high.loc[month], alpha=0.25)
                ax.vlines(month, sim_low.loc[month], sim_high.loc[month], alpha=0.25)

    if style.show_bias_bars:
        ax.bar(obs_mean.index, sim_mean.values - obs_mean.values, alpha=0.25, label="SIM-OBS bias")

    ax.set_xticks(range(1, 13))
    ax.set_xlabel("Month", fontsize=style.font_size, fontname=style.font_family)
    ax.set_ylabel(ylabel, fontsize=style.font_size, fontname=style.font_family)
    ax.grid(True, alpha=0.3)
    ax.legend()
    _draw_title(ax, _final_title(title, metric_name if style.show_metrics else None, metric_value), style)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=200)
    if show:
        plt.show()
    plt.close(fig)


def plot_fdc(
    obs: pd.Series,
    sim: pd.Series,
    title: str,
    ylabel: str,
    save_path: Optional[Path],
    style: PlotStyle,
    show: bool,
    logy: bool = False,
) -> None:
    aligned = pd.concat([clean_series(obs).rename("obs"), clean_series(sim).rename("sim")], axis=1).dropna()
    if aligned.empty:
        return
    obs_sorted = np.sort(aligned["obs"].values)[::-1]
    sim_sorted = np.sort(aligned["sim"].values)[::-1]
    exceedance = 100.0 * (np.arange(1, len(obs_sorted) + 1) / (len(obs_sorted) + 1.0))
    metric_value = eval_metric("KGE", aligned["obs"], aligned["sim"]) if style.show_metrics else None

    fig, ax = plt.subplots(figsize=style.figsize_fdc)
    _style_axes(ax, style)
    ax.plot(exceedance, obs_sorted, label="OBS", color=style.obs_color, linewidth=style.line_width)
    ax.plot(exceedance, sim_sorted, label="SIM", color=style.sim_color, linewidth=style.line_width)
    ax.set_xlabel("Exceedance (%)", fontsize=style.font_size, fontname=style.font_family)
    ax.set_ylabel(ylabel, fontsize=style.font_size, fontname=style.font_family)
    if logy:
        ax.set_yscale("log")
    ax.grid(True, alpha=0.3)
    ax.legend()
    _draw_title(ax, _final_title(title, "KGE" if style.show_metrics else None, metric_value), style)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=200)
    if show:
        plt.show()
    plt.close(fig)


def _normalize_stations(stations: Iterable[Station | dict | tuple | str]) -> list[Station]:
    normalized: list[Station] = []
    for item in stations:
        if isinstance(item, Station):
            normalized.append(item)
            continue
        if isinstance(item, dict):
            normalized.append(
                Station(
                    gis_id=int(item["gis_id"]),
                    obs_col=str(item["obs_col"]).strip(),
                    title=str(item.get("title", item["obs_col"])).strip(),
                    p_species=(str(item["p_species"]).strip().lower() if item.get("p_species") else None),
                )
            )
            continue
        if isinstance(item, tuple) and len(item) >= 3:
            normalized.append(Station(gis_id=int(item[0]), obs_col=str(item[1]).strip(), title=str(item[2]).strip(), p_species=(str(item[3]).strip().lower() if len(item) > 3 and item[3] else None)))
            continue
        raise ValueError(f"Unsupported station definition: {item!r}")
    return normalized


def run_job_for_station(config: CourseConfig, station: Station, job: RunJob) -> dict:
    config.out_dir.mkdir(parents=True, exist_ok=True)

    tag = f"{station.obs_col}_gid{station.gis_id}_{job.name}_{job.variable}_{job.time_step}_{job.obs_mode}_{job.metric}"
    hydro_png = config.out_dir / f"{tag}_hydrograph.png"
    seasonal_png = config.out_dir / f"{tag}_seasonal.png"
    fdc_png = config.out_dir / f"{tag}_fdc.png"
    aligned_csv = config.out_dir / f"{tag}_aligned.csv"
    plotdata_csv = config.out_dir / f"{tag}_plotdata.csv"

    if job.variable.strip().lower() == "solp_out":
        p_species = (job.obs_p_species or station.p_species or "").strip().lower()
        if not p_species:
            raise ValueError(f"Station {station.title} needs p_species or job.obs_p_species for phosphorus runs")
        sim_raw = build_phosphorus_series(
            txtinout_dir=config.txtinout_dir,
            out_dir=config.out_dir,
            gis_id=station.gis_id,
            cal_start=config.cal_start,
            cal_end=config.cal_end,
            time_step=job.time_step,
            source_file=job.source_file,
            obs_p_species=p_species,
        )
    else:
        sim_raw = build_sim_series(
            txtinout_dir=config.txtinout_dir,
            out_dir=config.out_dir,
            gis_id=station.gis_id,
            cal_start=config.cal_start,
            cal_end=config.cal_end,
            time_step=job.time_step,
            source_file=job.source_file,
            variable=job.variable,
        )

    obs_step = "monthly" if job.obs_mode.startswith("monthly") else "yearly"
    obs_df = read_obs_csv(job.obs_csv, [station.obs_col], config.cal_start, config.cal_end, obs_step)
    if station.obs_col not in obs_df.columns:
        raise ValueError(f"Observation column {station.obs_col!r} not found in {job.obs_csv}")
    obs = obs_df[station.obs_col].astype(float) * float(config.obs_scale)

    if obs_step == "monthly" and job.time_step.strip().lower() != "monthly":
        flow_monthly = None
        if config.obs_monthly_to_yearly in {"flow_weighted_mean", "fwmean", "fw_mean"}:
            flow_monthly = build_sim_series(
                txtinout_dir=config.txtinout_dir,
                out_dir=config.out_dir,
                gis_id=station.gis_id,
                cal_start=config.cal_start,
                cal_end=config.cal_end,
                time_step="monthly",
                source_file="sd",
                variable="flo_out",
            )
        obs = aggregate_monthly_to_yearly(obs, how=config.obs_monthly_to_yearly, flow_monthly=flow_monthly)

    flow_series = None
    day_series = None
    if job.obs_mode.strip().lower() == "monthly_mgl":
        flow_series = build_sim_series(
            txtinout_dir=config.txtinout_dir,
            out_dir=config.out_dir,
            gis_id=station.gis_id,
            cal_start=config.cal_start,
            cal_end=config.cal_end,
            time_step="monthly",
            source_file="sd",
            variable=config.flow_var,
        )
        day_series = build_sim_series(
            txtinout_dir=config.txtinout_dir,
            out_dir=config.out_dir,
            gis_id=station.gis_id,
            cal_start=config.cal_start,
            cal_end=config.cal_end,
            time_step="monthly",
            source_file="sd",
            variable=config.day_var,
        )

    sim = prepare_sim_for_obs(
        time_step=job.time_step,
        obs_mode=job.obs_mode,
        sim_series=sim_raw,
        flow_series=flow_series,
        day_series=day_series,
    )

    aligned = pd.concat([obs.rename("obs"), sim.rename("sim")], axis=1).dropna()
    metrics = eval_all_metrics(aligned["obs"], aligned["sim"]) if config.all_metrics else {job.metric.upper(): eval_metric(job.metric, aligned["obs"], aligned["sim"])}

    if config.save_aligned_csv:
        aligned.to_csv(aligned_csv, index=True)
    if config.save_plotdata_csv:
        aligned.to_csv(plotdata_csv, index=True)

    if config.export_plots or config.show_plots:
        plot_hydrograph(
            obs=aligned["obs"],
            sim=aligned["sim"],
            title=station.title,
            ylabel=job.y_label_hydro or job.variable,
            save_path=hydro_png if config.export_plots else None,
            style=config.style,
            show=config.show_plots,
            metric_name=job.metric,
        )
        if job.time_step.strip().lower() == "monthly":
            plot_seasonal(
                obs=aligned["obs"],
                sim=aligned["sim"],
                title=station.title,
                ylabel=job.y_label_seasonal or job.variable,
                save_path=seasonal_png if config.export_plots else None,
                style=config.style,
                show=config.show_plots,
                metric_name=job.metric,
            )
        plot_fdc(
            obs=aligned["obs"],
            sim=aligned["sim"],
            title=station.title,
            ylabel=job.y_label_fdc or job.variable,
            save_path=fdc_png if config.export_plots else None,
            style=config.style,
            show=config.show_plots,
        )

    return {
        "station": station,
        "job": job,
        "aligned": aligned,
        "metrics": metrics,
        "hydro_png": hydro_png,
        "seasonal_png": seasonal_png if job.time_step.strip().lower() == "monthly" else None,
        "fdc_png": fdc_png,
        "aligned_csv": aligned_csv,
        "plotdata_csv": plotdata_csv,
    }


def run_course(config: CourseConfig, stations: Sequence[Station | dict | tuple], jobs: Sequence[RunJob]) -> list[dict]:
    station_list = _normalize_stations(stations)
    if not station_list:
        raise ValueError("No stations provided")
    if not jobs:
        raise ValueError("No jobs provided")

    results: list[dict] = []
    print(f"Running {len(jobs)} jobs for {len(station_list)} stations...")
    for station in station_list:
        print(f"\n===== STATION: {station.title} (gis_id={station.gis_id}, obs_col={station.obs_col}) =====")
        for job in jobs:
            result = run_job_for_station(config, station, job)
            score_text = ", ".join(f"{k}={v:.4f}" if pd.notna(v) else f"{k}=nan" for k, v in result["metrics"].items())
            print(f"[{job.name}] {score_text}")
            print(f"  aligned: {result['aligned_csv']}")
            print(f"  hydro  : {result['hydro_png']}")
            if result["seasonal_png"] is not None:
                print(f"  seasonal: {result['seasonal_png']}")
            print(f"  fdc    : {result['fdc_png']}")
            results.append(result)
    print("\nDone.")
    return results
