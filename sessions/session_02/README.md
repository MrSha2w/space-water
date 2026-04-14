# Space-Water 2026 | Session 2

Teaching repository for running and presenting SWAT+ observation-vs-simulation comparisons in the Space-Water 2026 course.

## Structure

- `src/swat_core.py`: reusable logic
- `src/run_session2.py`: session-specific configuration and entry point
- `data/`: input files
- `outputs/`: generated figures and aligned CSV files

## Run

From the repository root:

```bash
python src/run_session2.py
```

## JupyterLab

In a notebook started from the repository root:

```python
import sys
sys.path.append("src")

from run_session2 import CONFIG, STATIONS, JOBS
from swat_core import run_course

results = run_course(CONFIG, STATIONS[:2], JOBS)
```
