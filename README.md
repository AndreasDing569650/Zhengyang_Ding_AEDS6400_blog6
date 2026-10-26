# Matching Parents and Children with SQL in Python

## Project Overview

This project reproduces a PSID-based intergenerational income analysis in Python. The goal is to match children to their biological parents in a longitudinal panel, construct parent-child family-income measures, and estimate the intergenerational income elasticity (IGE) using log-log regressions.

The analysis is implemented in three stages:

1. Clean and reshape the raw individual-level PSID data into a person-year format.
2. Match children to biological mothers and fathers using SQL in SQLite.
3. Estimate the relationship between parent and child family income and save the regression results.

The project uses family-level income from the PSID and excludes parent-child pairs who live in the same household in the relevant year. This helps isolate parent-child income linkage rather than co-residence effects.

## Data

The raw data are stored in `data/raw_data/`:

- `individual_data.csv`: individual-level PSID data with person identifiers, family identifiers, age, and income measures.
- `parent_identification.txt`: fixed-width parent-identification file linking each child to biological mother and father records.

The project creates cleaned and matched versions in:

- `data/cleaned_data/`
- `data/matched_data/`

The final regression output is written to:

- `result/regression_results.csv`

## Repository Structure

```text
Zhengyang_Ding_AEDS6400_blog6/
├── README.md
├── requirements.txt
├── .gitignore
├── code/
│   ├── data_process.py
│   ├── data_SQLmatch.py
│   └── data_analysis.py
├── data/
│   ├── raw_data/
│   │   ├── individual_data.csv
│   │   └── parent_identification.txt
│   ├── cleaned_data/
│   │   ├── individual_long.csv
│   │   └── parent_identification.csv
│   └── matched_data/
│       ├── matched_parent_child.csv
│       └── psid_matching.db
└── result/
    └── regression_results.csv
```

## Workflow Summary

### 1) Data cleaning and reshaping — `code/data_process.py`

This script reads the raw PSID files and performs the initial data preparation. It:

- loads the individual-level data and checks required variables,
- constructs a permanent person ID using interview number and person number,
- reshapes the 2020 and 2022 records into a long-format person-year dataset,
- removes unusable or zero-filled records,
- reads the parent-identification text file using fixed-width parsing,
- saves cleaned outputs to `data/cleaned_data/`.

Outputs:

- `data/cleaned_data/individual_long.csv`
- `data/cleaned_data/parent_identification.csv`

This step is essential because the later SQL matching expects a consistent person-year structure and a properly formatted parent-to-child identifier table.

### 2) SQL-based parent-child matching — `code/data_SQLmatch.py`

This script loads the cleaned files into a SQLite database and performs the matching logic in SQL. It:

- creates person IDs for child, mother, and father records,
- builds a parent-child bridge table,
- joins the parent and child observations by person ID,
- keeps parent-child pairs only when the parent and child are in different families,
- computes 2022 single-year and 2020-2022 average income measures,
- applies a working-age filter to children and parents (ages 25 to 64 in 2022),
- writes the final matched data and the SQLite database.

Outputs:

- `data/matched_data/psid_matching.db`
- `data/matched_data/matched_parent_child.csv`

This stage is the core of the replication: it translates the matching logic into SQL and produces a clean analysis dataset ready for regression.

### 3) Regression and summary output — `code/data_analysis.py`

This script reads the matched parent-child dataset and estimates two models:

- Single-year model using 2022 family income
- Two-year average model using the average of 2020 and 2022 family income

The regression is:

```text
log(child_income) = alpha + beta * log(parent_income) + error
```

where `beta` is the intergenerational income elasticity (IGE). The script:

- logs parent and child income,
- removes non-positive or missing values,
- fits OLS models using `statsmodels`,
- prints the full regression summaries,
- stores the key estimates in `result/regression_results.csv`.

Output:

- `result/regression_results.csv`

## Reproduction Instructions

To reproduce the results, run the scripts in order from the project root directory.

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the workflow

From the repository root:

```bash
python code/data_process.py
python code/data_SQLmatch.py
python code/data_analysis.py
```

### 3. Check the generated outputs

After successful execution, the project should contain:

- cleaned data under `data/cleaned_data/`
- matched data under `data/matched_data/`
- final regression summary under `result/regression_results.csv`

### Notes on Reproducibility

The scripts are written to detect the project root automatically using `Path(__file__).resolve().parents[1]`, so you generally do not need to manually edit the working directory or file paths before running them. If you execute the commands from the repository root, the analysis should work as expected.

The workflow is deliberately staged:

- `data_process.py` creates the cleaned building blocks,
- `data_SQLmatch.py` creates the matched parent-child dataset,
- `data_analysis.py` estimates the intergenerational elasticity from that dataset.

This order matters because each script depends on the files generated by the previous one.

## Expected Interpretation

The final result measures how strongly child income is related to parent income. A positive coefficient on the log of parent income indicates that higher-income parents are associated with higher-income children, and the magnitude reflects the degree of intergenerational persistence in income.

The project compares a single-year specification and a two-year averaged specification to check whether the result is sensitive to how income is measured over time.

