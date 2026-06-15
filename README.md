# Teiknical


This repository contains my solution for the Teiko technical assessment. The project loads immune-cell count data from a CSV file into a normalized SQLite database, performs analysis on immune-cell population counts and percentages, and provides an interactive Streamlit dashboard for exploring the results.


# Project Structure

Teiknical/

 ├── cell-count.csv

 ├── load\_data.py

 ├── initial\_analysis.py

 ├── statistical\_analysis.py

 ├── data\_subset\_analysis.py

 ├── dashboard.py

 ├── requirements.txt

 ├── Makefile

 ├── README.md

 └── LICENSE

# Code Structure and Design Rationale

The code is organized into separate scripts so that each part of the assessment has a clear responsibility.

* `load_data.py`: creates the SQLite database schema and loads the original CSV data into normalized relational tables.
* `initial_analysis.py`: performs the initial cell-count analysis by calculating total cell counts and immune-cell population percentages for each sample.
* `statistical_analysis.py`: performs the responder vs non-responder analysis for melanoma PBMC samples treated with miraclib, including statistical testing and output summaries.
* `data_subset_analysis.py`: performs Bob's subset analysis for baseline melanoma PBMC samples treated with miraclib.
* `dashboard.py`: provides an interactive Streamlit dashboard for viewing the database status, normalized cell-count analysis, responder analysis, and Bob's subset analysis.
* `requirements.txt`: lists the Python dependencies needed to run the project.
* `Makefile`: provides standardized commands for setup, pipeline execution, and launching the dashboard.

The project is structured this way to separate data loading, analysis, and visualization. `load_data.py` is responsible only for creating and populating the database. The analysis scripts read from the database rather than directly from the CSV, which makes the workflow more reproducible and ensures that all analyses use the same cleaned relational data source.

The dashboard also reads from the SQLite database, so the visual results are connected to the same pipeline as the generated output tables. This avoids duplicating logic across multiple files and makes it easier to update or extend the project later.

The `Makefile` provides three main commands:

```bash
make setup
make pipeline
make dashboard
```

`make setup` installs dependencies, `make pipeline` runs the full data workflow from database creation through analysis output generation, and `make dashboard` starts the local Streamlit server. This makes the project easier to grade and easier to reproduce in GitHub Codespaces.


# Part 1: Data Management

`load_data.py` creates a SQLite database called `cell_counts.db` from the input CSV file.

 The database contains the following tables:

 * projects : stores unique project names.
 * treatments : stores unique treatment names.
 * cell_populations : stores immune-cell population names such as `b_cell`, `cd8_t_cell`, `cd4_t_cell`, `nk_cell`, and `monocyte`.
 * subjects : stores subject-level metadata including subject_ID, project, condition, age, and sex.
 * samples : stores sample-level metadata such as sample ID, subject ID, treatment, response, sample type, and time from treatment start.
 * cell_counts : stores the measured immune-cell counts for each sample and cell population.
 
 
This design separates subject-level information from sample-level information because one subject may have multiple samples taken at different time points or under different treatment conditions. It also separates cell population names into their own lookup table so that the count table does not need to repeatedly store text labels for every sample.

The cell_counts table uses a long-format design where each row represents one sample and one immune-cell population. For example, instead of storing b_cell, cd8_t_cell, cd4_t_cell, nk_cell, and monocyte as separate columns, the database stores the cell population as a row-level attribute linked by population_id.

This structure scales better than a flat CSV-style table. If hundreds of projects, thousands of samples, or additional immune-cell populations were added, the schema would not need to be redesigned. New projects, treatments, subjects, samples, and cell populations could be added as new rows. This also makes downstream analytics more flexible because queries can group, filter, and aggregate by project, subject, treatment, response, time point, sample type, or immune-cell population.

For example, the same schema can support analyses such as:

* comparing responders and non-responders
* calculating immune-cell percentages by sample
* filtering baseline samples only
* comparing treatment groups
* analyzing changes over time
* summarizing counts by project, subject, sex, condition, or response status

This relational structure keeps the data organized, reduces duplication, and allows the analysis scripts and dashboard to query the same database consistently.
 
To create the database manually:

```bash
python load_data.py
```

# Part 2: Initial Cell Count Analysis


 `initial_analysis.py` calculates the total cell count for each sample and the percentage contribution of each immune-cell population.

 The output contains:

* sample ID
* total cell count
* immune-cell population name
* raw count
* percentage of total cell count

 To run the initial analysis:

```bash
 python initial_analysis.py
```

# Part 3: Responder vs Non-Responder Analysis


`statistical_analysis.py` compares immune-cell population percentages between responders and non-responders for melanoma PBMC samples treated with miraclib.


The analysis uses a Mann-Whitney U test to compare responder and non-responder groups for each immune-cell population.



To run the responder analysis:
```bash
python statistical_analysis.py
```


# Part 4: Bob's Data Subset Analysis


`data_subset_analysis.py` identifies baseline melanoma PBMC samples from patients treated with miraclib.


It reports:

* how many samples came from each project
* how many subjects were responders or non-responders
* how many subjects were male or female
* the average number of B cells for melanoma male responders at time zero

 To run Bob's subset analysis:

```bash
 python data_subset_analysis.py
```

# Interactive Dashboard


The project includes an interactive Streamlit dashboard in `dashboard.py`.

The dashboard displays:

* database status and summary counts
* Part 2 normalized immune-cell percentages
* Part 3 responder vs non-responder analysis
* Part 4 Bob's baseline melanoma PBMC subset analysis
* downloadable tables
* interactive plots


# Dashboard Link

 After starting the dashboard locally, open:

 http://localhost:8501

 If port `8501` is already in use, Streamlit may provide a different local URL in the terminal.

# Setup

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Or using the Makefile:
 
```bash
 make setup
```

# Run the Dashboard

 The preferred way to launch the dashboard is:

```bash
 make dashboard
```

This creates the SQLite database if needed and starts the local Streamlit server.

 
On Windows, if `make` is not available, run:

```bash
python load_data.py
python -m streamlit run dashboard.py
```



# Requirements

The main Python packages used are:

* pandas
* streamlit
* plotly
* scipy
* matplotlib
The project also uses Python standard-library modules including `sqlite3` and `pathlib`.


# Notes
Generated files such as the SQLite database, CSV outputs, text summaries, and figures are not tracked in Git. They can be regenerated by running the scripts.



