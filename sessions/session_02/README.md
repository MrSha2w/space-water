# Space-Water 2026 | Session 2

Teaching repository for running and presenting SWAT+ observation-vs-simulation comparisons in the Space-Water 2026 course.

## Structure

- `src/swat_core.py`: reusable logic
- `src/run_session2.py`: session-specific configuration and entry point
- `data/`: input files
- `outputs/`: generated figures and aligned CSV files


============
Installation
============

To execute Jupyter Notebook/Lab, we need the Miniconda environment.

1. Miniconda Python:
--------------------

- If you don't already have conda installed, please download Miniconda for your operating system from https://conda.io/en/latest/miniconda.html (choose the latest version for your operating system, 64-bit). You should not need elevated rights to install this.
- Run the installer and select "only my user" when prompted. This will allow you to work with your python installation directly.


2. Set Environment and install libraries:
-----------------------------------------
- After installation, go to the START menu and select "Miniconda Prompt" to open a DOS box.
- Let's update conda base first.

.. code-block:: bash

   conda update -n base -c defaults conda

and hit ENTER.

- Using the `cd <https://www.computerhope.com/issues/chusedos.htm>`_ command in the Miniconda DOS box, navigate to the location where you have `environment.yml` the file and type: 

.. code-block:: bash

   conda env create -f environment.yml

and hit ENTER.

After your virtual environment setup is complete, change the environment to `swatp_pst_wf`:  

.. code-block:: bash

   conda activate swatp_session2

- Launch jupyter lab 

.. code-block:: bash

   jupyter notebook


A browser window with a Jupyter notebook instance should open. Yay!
