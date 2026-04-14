# Space-Water 2026 | Session 2

Session 2 teaching repository for running, evaluating, and presenting SWAT+ observation-versus-simulation comparisons in the Space-Water 2026 course.

## Repository structure

- `src/swat_core.py` contains the reusable workflow logic for reading SWAT+ outputs, loading observations, aligning time series, computing evaluation metrics, and generating diagnostic plots.
- `sessions/session_02/config.py` contains the Session 2 configuration, including paths, stations, jobs, and plotting settings.
- `sessions/session_02/session_02_demo.ipynb` provides the classroom notebook for testing and demonstrating the Session 2 workflow.
- `data/` stores input files such as observations and any required local data.
- `outputs/` stores generated figures and aligned CSV files.

## Environment setup

This workflow is intended to run in a dedicated Conda environment.

### 1. Install Miniconda

If Conda is not already installed on your computer, download and install Miniconda for your operating system from the official Miniconda website. Use the latest 64-bit version available for your system.

During installation, choose the option for your user only unless you specifically need a system-wide installation.

### 2. Open the Conda terminal

After installation, open **Miniconda Prompt** from the Start menu on Windows.

### 3. Update Conda

Run the following command:

```bash
conda update -n base -c defaults conda
```

### 4. Create the Session 2 environment

Move to the repository folder, then run:

```bash
conda env create -f environment.yml
```

This creates the environment defined for the course workflow.

### 5. Activate the environment

After the environment is created, activate it with:

```bash
conda activate swatp_session2
```

## Running the notebook

To start Jupyter Notebook, run:

```bash
jupyter notebook
```

A browser window should open automatically. Then open:

```text
sessions/session_02/session_02_demo.ipynb
```

## Before running Session 2

Before executing the notebook or any workflow script, make sure you update the paths in:

```text
sessions/session_02/config.py
```

At minimum, verify that the following paths match your computer:

- SWAT+ `TxtInOut` directory
- observation CSV files
- output directory

If these paths are wrong, the workflow will fail immediately, which is a very efficient way to waste class time.

## Outputs

Session 2 generates:

- aligned observation-simulation CSV files
- hydrograph plots
- seasonal climatology plots for monthly runs
- flow duration curve plots

All generated outputs are written to the configured output folder.
