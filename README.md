# Matching Parents and Children with SQL in Python

## Project Overview

This project demonstrates how SQL can be used in Python to match children to their biological parents in longitudinal PSID data and construct family-income measures for an intergenerational income elasticity (IGE) analysis. The workflow is implemented in three stages: data cleaning, parent-child matching, and regression estimation.

The project uses a long-format panel built from two PSID waves (2020 and 2022), converts individual-level records into person-year observations, matches children to mothers and fathers using the PSID parent-identification file, and estimates how a child's family income varies with the income of the matched parent(s).

## Data

The analysis uses two PSID source files stored under `data/raw_data/`:
- `individual_data.csv`: individual-level data containing identifiers, family identifiers, age, and family-level total income for the selected years.
- `parent_identification.txt`: fixed-width parent-identification records linking children to their biological mother and father.

The income measure is total family income for the family in which a person is observed, not the person's individual labor earnings. The single-year specification uses 2022 family income, while the multi-year specification uses the average of 2020 and 2022 family income. In addition, we do not count parent-child pairs that live in the same family when constructing income measures for the analysis.

## Repository Structure

```text
Zhengyang_Ding_AEDS6400_blog6/
│
├── code/
│   ├── data_process.py
│   ├── data_SQLmatch.py
│   └── data_analysis.py
│
├── data/
│   ├── raw_data/
│   │   ├── individual_data.csv
│   │   └── parent_identification.txt
│   │
│   ├── cleaned_data/
│   │   ├── individual_long.csv
│   │   └── parent_identification.csv
│   │
│   └── matched_data/
│       ├── matched_parent_child.csv
│       └── psid_matching.db
│
├── result/
│   └── regression_results.csv
│
└── README.md
```

## Data Processing and Analysis Workflow

1. Prepare the data — `code/data_process.py`

The first script reads the raw individual data and reshapes the selected year-specific variables into a person-year dataset. It standardizes the permanent person ID, family ID, age, year, and family-income fields, removes incomplete or zero-filled rows, and writes the cleaned files used by the matching stage.

Outputs:
- `data/cleaned_data/individual_long.csv`
- `data/cleaned_data/parent_identification.csv`

2. Match parents and children with SQL — `code/data_SQLmatch.py`

The second script loads the cleaned files into a SQLite database. It constructs permanent person IDs for children, mothers, and fathers, creates a bridge table linking each child to each identified parent, and joins the parent and child records by person ID and year.

The matching procedure excludes parent-child pairs living in the same family in the relevant year and then constructs two income measures:
- family income in 2022 for the single-year regressions
- the average of family income in 2020 and 2022 for the multi-year regressions

The script outputs the matched dataset and the SQLite database used for the analysis.

Outputs:
- `data/matched_data/psid_matching.db`
- `data/matched_data/matched_parent_child.csv`

3. Estimate and compare IGE — `code/data_analysis.py`

The third script reads the matched data, logs both parent and child family income, applies positivity checks, and estimates two log-log regressions:

$$
\log(\text{ChildIncome}_i) = \alpha + \beta \log(\text{ParentIncome}_i) + \epsilon_i
$$

One model uses 2022 family income, and the other uses the average of 2020 and 2022 family income. The coefficient $\beta$ is the intergenerational income elasticity (IGE), which is reported in the final results table.

Outputs:
- `result/regression_results.csv`

## Reproducibility

Run the scripts in order from the project root:
1. `python code/data_process.py`
2. `python code/data_SQLmatch.py`
3. `python code/data_analysis.py`

Before running the scripts, confirm that the project path configured at the beginning of each script points to the local repository directory. The scripts expect the raw source files under `data/raw_data/`, then generate cleaned intermediate data under `data/cleaned_data/`, matched outputs under `data/matched_data/`, and regression results in `result/`.

The repository is designed to be reproducible using the two PSID files already stored in `data/raw_data/`.
