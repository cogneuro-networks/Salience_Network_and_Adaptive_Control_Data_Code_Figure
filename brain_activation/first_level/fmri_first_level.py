"""
First-level fMRI GLM analysis for the flexibility-stability task.

License: MIT

Fits run-wise first-level models with one regressor per experimental condition,
includes motion and physiological confounds, and saves design matrices and
condition-specific beta maps.

Can be run from the command line or imported by fmri_first_level.ipynb.

Design summary
--------------
- 2 x 2 x 2 full factorial: long_short x probability x trial_type
- Additional boxcar regressors: rest_onset (20 s), error trials via acc (1 s)
- fMRIPrep confounds: 24-parameter motion, CSF/WM, FD, motion/non-steady outliers
- HRF: Glover; drift: cosine high-pass (0.01 Hz); noise model: AR(1)
"""
from __future__ import annotations

import argparse
import itertools
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

import matplotlib
import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from nilearn import image
from nilearn.glm.first_level import FirstLevelModel, make_first_level_design_matrix
from nilearn.plotting import plot_design_matrix

matplotlib.use("Agg")

logger = logging.getLogger(__name__)

DEFAULT_TARGET_FACTORS = ["trial_type", "probability", "long_short"]
DEFAULT_CONFOUND_NAMES = ["rest_onset", "acc"]
DEFAULT_CONFOUND_DURATIONS = [20, 1]
PROBABILITY_BLOCK_MAP = {
    "SF8020": "prob_diff",
    "SF2080": "prob_diff",
    "SF5050": "prob_same",
}
REST_BLOCK_LABEL = "SF2080ProceLong"
REST_ONSET_OFFSET_S = 20


@dataclass
class FirstLevelConfig:
    """Configuration for first-level GLM estimation."""

    bids_root: Path
    derivatives_dir: Path
    output_dir: Path
    task: str = "flexibilitystability"
    space: str = "MNI152NLin2009cAsym"
    runs: Sequence[int] = field(default_factory=lambda: [1])
    target_factors: Sequence[str] = field(default_factory=lambda: list(DEFAULT_TARGET_FACTORS))
    split_column: str | None = "blocks"
    confound_names: Sequence[str] = field(default_factory=lambda: list(DEFAULT_CONFOUND_NAMES))
    confound_durations: Sequence[int] = field(default_factory=lambda: list(DEFAULT_CONFOUND_DURATIONS))
    events_duration: float = 1.0
    slice_time_ref: float = 0.5
    hrf_model: str = "glover"
    drift_model: str = "cosine"
    high_pass: float = 0.01
    smoothing_fwhm: float = 6.0
    noise_model: str = "ar1"
    n_jobs: int = 1
    subjects: Sequence[str] | None = None

    def __post_init__(self) -> None:
        self.bids_root = Path(self.bids_root).resolve()
        self.derivatives_dir = Path(self.derivatives_dir).resolve()
        self.output_dir = Path(self.output_dir).resolve()
        self.runs = list(self.runs)
        self.target_factors = list(self.target_factors)
        self.confound_names = list(self.confound_names)
        self.confound_durations = list(self.confound_durations)

        if len(self.confound_names) != len(self.confound_durations):
            raise ValueError("confound_names and confound_durations must have the same length.")


def configure_logging(verbose: bool = False) -> None:
    """Configure module-level logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )


def discover_subjects(bids_root: Path, subjects: Sequence[str] | None = None) -> list[str]:
    """Return subject IDs available under the BIDS root."""
    if subjects:
        return [sub if sub.startswith("sub-") else f"sub-{sub}" for sub in subjects]

    return sorted(path.name for path in bids_root.glob("sub-*") if path.is_dir())


def process_error_trial(event_df: pd.DataFrame, acc_name: str = "acc", order: int = 0) -> pd.DataFrame:
    """Convert accuracy values into onset timestamps for error-trial regressors."""
    event_df = event_df.copy()
    if order == 0:
        event_df[acc_name] = (1 - event_df[acc_name]) * event_df["onset"]
    elif order == 1:
        previous_acc = 1 - event_df.shift(1)[acc_name]
        event_df[acc_name] = (1 - event_df[acc_name]) * event_df["onset"] + previous_acc * event_df["onset"]
    else:
        raise ValueError(f"Unsupported error-trial order: {order}")
    return event_df


def confound_events_to_bold(
    event_df: pd.DataFrame,
    event_names: Sequence[str],
    tr: float,
    n_scans: int,
    durations: Sequence[int],
) -> pd.DataFrame:
    """Convert event columns (e.g. rest_onset, acc) into BOLD time-series regressors."""
    confounds_regressors = pd.DataFrame()
    working_df = event_df.copy()

    for event_name, duration in zip(event_names, durations):
        if event_name == "acc":
            working_df = process_error_trial(working_df, event_name, order=0)

        onset = working_df[event_name].replace(0, np.nan).dropna()
        if onset.empty:
            continue

        confounds_events = pd.DataFrame(
            {
                "onset": onset,
                "duration": [duration] * len(onset),
                "trial_type": [event_name] * len(onset),
            }
        )
        confound_regressor = make_first_level_design_matrix(
            frame_times=np.arange(0, n_scans) * tr,
            events=confounds_events,
            drift_model=None,
        ).drop(columns=["constant"])
        confounds_regressors = pd.concat([confounds_regressors, confound_regressor], axis=1)

    return confounds_regressors


def find_comb(
    event_df: pd.DataFrame,
    factors: Sequence[str] | None = None,
    split_column: str | None = None,
) -> tuple[list[str], pd.DataFrame]:
    """Build full-factorial condition labels from event metadata."""
    event_df = event_df.fillna(np.nan).copy()
    factors = list(factors or [])

    if "rest_onset" in event_df.columns and "blocks" in event_df.columns:
        block_rows = event_df.index[event_df["blocks"] == REST_BLOCK_LABEL]
        if len(block_rows) > 0:
            idx = block_rows[0]
            event_df.at[idx, "rest_onset"] = event_df.at[idx, "onset"] - REST_ONSET_OFFSET_S

    if split_column is not None:
        event_df[["probability", "long_short"]] = event_df[split_column].str.split("Proce", expand=True)
        event_df["probability"] = event_df["probability"].map(PROBABILITY_BLOCK_MAP)
        event_df = event_df.drop(columns=[split_column])

    if None in factors:
        categories = ["all_conditions"]
    else:
        factor_levels = {factor: set(event_df[factor]) for factor in sorted(factors)}
        combinations = list(itertools.product(*factor_levels.values()))
        categories = ["_".join(str(item) for item in combo) for combo in combinations]

    event_df = event_df.assign(
        trial_type=event_df.loc[:, sorted(factors)].apply(
            lambda row: "_".join(str(item) for item in row),
            axis=1,
        )
    )

    if "transition_type" in event_df.columns:
        event_df = event_df[~event_df["transition_type"].str.contains("View", na=False)]

    return categories, event_df


def select_fmriprep_confounds(confound_data: pd.DataFrame) -> pd.DataFrame:
    """Select motion, outlier, and aCompCor confounds from fMRIPrep output."""
    return confound_data.loc[
        :,
        confound_data.columns.str.startswith(
            ("trans", "rot", "non_steady_state_outlier", "motion_outlier")
        )
        | confound_data.columns.isin(["csf", "white_matter", "framewise_displacement"]),
    ]


def _subject_paths(config: FirstLevelConfig, subject: str, run: int) -> tuple[Path, Path, Path, Path]:
    """Return event, BOLD, mask, and confounds paths for one run."""
    stem = f"{subject}_task-{config.task}_run-{run}"
    event_path = config.bids_root / subject / "func" / f"{stem}_events.tsv"
    func_path = (
        config.derivatives_dir
        / subject
        / "func"
        / f"{stem}_space-{config.space}_desc-preproc_bold.nii.gz"
    )
    mask_path = (
        config.derivatives_dir
        / subject
        / "func"
        / f"{stem}_space-{config.space}_desc-brain_mask.nii.gz"
    )
    confounds_path = config.derivatives_dir / subject / "func" / f"{stem}_desc-confounds_timeseries.tsv"
    return event_path, func_path, mask_path, confounds_path


def fit_first_level_subject(config: FirstLevelConfig, subject: str) -> tuple[list[FirstLevelModel], list[pd.DataFrame]]:
    """Fit first-level GLM models for one subject."""
    event_tables: list[pd.DataFrame] = []
    confounds_tables: list[pd.DataFrame] = []
    func_paths: list[Path] = []
    mask_paths: list[Path] = []

    for run in config.runs:
        event_path, func_path, mask_path, confounds_path = _subject_paths(config, subject, run)
        for path in (event_path, func_path, mask_path, confounds_path):
            if not path.exists():
                raise FileNotFoundError(f"Missing required file: {path}")

        events = pd.read_csv(event_path, sep="\t")
        events = events.dropna(subset=["onset", "duration", "trial_type"]).reset_index(drop=True)
        _, events = find_comb(events, factors=config.target_factors, split_column=config.split_column)
        event_tables.append(events)

        confounds_tables.append(select_fmriprep_confounds(pd.read_csv(confounds_path, sep="\t")))
        func_paths.append(func_path)
        mask_paths.append(mask_path)

    models: list[FirstLevelModel] = []

    for run_idx, run in enumerate(config.runs):
        func_data = nib.load(func_paths[run_idx])
        mask = nib.load(mask_paths[run_idx])
        tr = float(func_data.header["pixdim"][4])
        n_scans = func_data.shape[3]

        confound_regressors = confound_events_to_bold(
            event_df=event_tables[run_idx],
            event_names=config.confound_names,
            tr=tr,
            n_scans=n_scans,
            durations=config.confound_durations,
        )
        confounds_run = pd.concat([confounds_tables[run_idx], confound_regressors], axis=1)
        confound_df = confounds_run.dropna()

        events_run = event_tables[run_idx].loc[:, ["onset", "duration", "trial_type"]].copy()
        events_run["duration"] = config.events_duration

        valid_indices = confound_df.index if not confound_df.empty else None
        if valid_indices is not None:
            frame_times = np.arange(0, n_scans)[valid_indices] * tr
        else:
            frame_times = np.arange(0, n_scans) * tr

        design_matrix = make_first_level_design_matrix(
            frame_times=frame_times,
            events=events_run,
            add_regs=confound_df,
            hrf_model=config.hrf_model,
            drift_model=config.drift_model,
            high_pass=config.high_pass,
        )

        first_level_model = FirstLevelModel(
            t_r=tr,
            mask_img=mask,
            slice_time_ref=config.slice_time_ref,
            hrf_model=config.hrf_model,
            drift_model=config.drift_model,
            high_pass=config.high_pass,
            smoothing_fwhm=config.smoothing_fwhm,
            minimize_memory=True,
            noise_model=config.noise_model,
        )
        func_data_clean = image.index_img(func_data, valid_indices) if valid_indices is not None else func_data
        models.append(first_level_model.fit(func_data_clean, design_matrices=design_matrix))

    return models, event_tables


def save_subject_outputs(
    config: FirstLevelConfig,
    subject: str,
    models: list[FirstLevelModel],
    event_tables: list[pd.DataFrame],
) -> None:
    """Save design matrices, QC figures, and condition beta maps for one subject."""
    subject_dir = config.output_dir / subject
    for subdir in ("betas", "model", "figures"):
        (subject_dir / subdir).mkdir(parents=True, exist_ok=True)

    for run_idx, model in enumerate(models):
        run = config.runs[run_idx]
        _, func_path, _, _ = _subject_paths(config, subject, run)
        file_stem = func_path.name.split("desc-preproc")[0]

        design_matrix = model.design_matrices_[0]
        design_matrix.to_csv(subject_dir / "model" / f"{file_stem}desc-design_matrix.tsv", sep="\t", index=False)

        design_fig = subject_dir / "figures" / f"{file_stem}desc-design_matrix.png"
        plot_design_matrix(design_matrix, output_file=str(design_fig))

        corr_fig = subject_dir / "figures" / f"{file_stem}desc-design_corr.png"
        labels = design_matrix.columns.tolist()[:-1]
        ax = plot_design_matrix(design_matrix.drop("constant", axis=1).corr())
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels)
        plt.savefig(corr_fig, bbox_inches="tight")
        plt.close()

        for condition in np.unique(event_tables[run_idx]["trial_type"]):
            contrast = model.compute_contrast(condition, stat_type="t", output_type="all")
            beta_path = subject_dir / "betas" / f"{subject}_{condition}_run-{run}_beta.nii.gz"
            varbeta_path = subject_dir / "betas" / f"{subject}_{condition}_run-{run}_varbeta.nii.gz"
            contrast["effect_size"].to_filename(str(beta_path))
            contrast["effect_variance"].to_filename(str(varbeta_path))


def run_subject(config: FirstLevelConfig, subject: str) -> str:
    """Run the full first-level workflow for one subject."""
    logger.info("Processing %s", subject)
    models, event_tables = fit_first_level_subject(config, subject)
    save_subject_outputs(config, subject, models, event_tables)
    logger.info("Finished %s", subject)
    return subject


def run_batch(config: FirstLevelConfig) -> list[str]:
    """Run first-level analysis for all configured subjects."""
    subjects = discover_subjects(config.bids_root, config.subjects)
    if not subjects:
        raise RuntimeError(f"No subjects found under {config.bids_root}")

    config.output_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Running first-level GLM for %d subject(s)", len(subjects))

    if config.n_jobs == 1:
        return [run_subject(config, subject) for subject in subjects]

    return Parallel(n_jobs=config.n_jobs)(
        delayed(run_subject)(config, subject) for subject in subjects
    )


def _parse_int_list(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def _parse_str_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def build_arg_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Run first-level GLM analysis for the flexibility-stability fMRI task.",
    )
    parser.add_argument("--bids-root", type=Path, required=True, help="BIDS dataset root containing sub-* folders.")
    parser.add_argument(
        "--derivatives-dir",
        type=Path,
        required=True,
        help="fMRIPrep derivatives root containing sub-*/func preprocessed data.",
    )
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory for first-level outputs.")
    parser.add_argument("--subjects", type=_parse_str_list, default=None, help="Comma-separated subject IDs. Default: all sub-* under bids-root.")
    parser.add_argument("--runs", type=_parse_int_list, default="1", help="Comma-separated run numbers.")
    parser.add_argument("--task", default="flexibilitystability", help="BIDS task label.")
    parser.add_argument("--space", default="MNI152NLin2009cAsym", help="Normalized space identifier.")
    parser.add_argument("--n-jobs", type=int, default=1, help="Number of parallel workers.")
    parser.add_argument("--events-duration", type=float, default=1.0, help="Duration (s) assigned to each condition event.")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging.")
    return parser


def config_from_args(args: argparse.Namespace) -> FirstLevelConfig:
    """Build a FirstLevelConfig from parsed CLI arguments."""
    return FirstLevelConfig(
        bids_root=args.bids_root,
        derivatives_dir=args.derivatives_dir,
        output_dir=args.output_dir,
        task=args.task,
        space=args.space,
        runs=args.runs,
        subjects=args.subjects,
        events_duration=args.events_duration,
        n_jobs=args.n_jobs,
    )


def main(argv: Sequence[str] | None = None) -> None:
    """CLI entry point."""
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    configure_logging(verbose=args.verbose)
    config = config_from_args(args)
    run_batch(config)


if __name__ == "__main__":
    main()
