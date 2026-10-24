# Matching Parents and Children with SQL in Python

## Project Overview

This project demonstrates how SQL can be used in Python to match parents and children in longitudinal data and construct family-income measures for an intergenerational income elasticity (IGE) analysis. The data come from the Panel Study of Income Dynamics (PSID). The workflow separates data preparation, SQL-based matching, and regression analysis so that each stage can be checked and reproduced independently.

## Data

The analysis uses two PSID source files:
- individual_data.csv: individual identifiers, family identifiers, age, and family-level total income for the selected years.
- parent_identification.txt: fixed-width records identifying children and their biological parents.
The income measure is total income for the family unit in which a person is observed, not the person's individual labor earnings. The single-year specification uses 2022 income. The multi-year specification averages income from 2020 and 2022 for both parents and children. The analysis restricts both generations to ages 25–64 in 2022.

Place the source files in data/raw_data/. The PSID files must be obtained through the appropriate PSID data-access process; users should follow the data provider's terms when storing or redistributing the raw data.

## Repository Structure

6400_blog_6/
├── data/
│   ├── raw_data/
│   │   ├── individual_data.csv
│   │   └── parent_identification.txt
│   └── cleaned_data/
│       ├── individual_long.csv
│       ├── parent_identification.csv
│       ├── psid_matching.db
│       └── matched_parent_child.csv
├── result/
│   ├── regression_results.csv
│   ├── single_year_regression.txt
│   └── multi_year_regression.txt
├── code/
│   ├── data_process.py
│   ├── data_SQLmatch.py
│   └── data_analysis.py
├── blog6.qmd
└── README.md

## Data Processing and Analysis Workflow

1. Prepare the data — data_process.py

The first script reads the raw individual data and reshapes the selected year-specific variables into a person-year dataset. It standardizes the person ID, family ID, age, year, and family-income fields, and removes records that do not represent valid interviews. It also parses the fixed-width parent-identification file and exports the required parent-identification fields in CSV format.

Outputs: individual_long.csv and parent_identification.csv in data/cleaned_data/.

2. Match parents and children with SQL — data_SQLmatch.py

The second script loads the cleaned files into a SQLite database. It constructs permanent person IDs for children, mothers, and fathers, then creates a bridge table linking each child to each identified parent. SQL JOIN operations connect those IDs to person-year records; family IDs identify the family whose total income is assigned to each person. GROUP BY and AVG() summarize matched parental income at the child level.

The script constructs two sets of measures: family income in 2022, and the average of family income in 2020 and 2022. Parent-child pairs observed in the same family in a given year are excluded to avoid assigning mechanically identical family-income values to both generations. The 2022 age restriction is applied after matching, and observations with nonpositive income are excluded from the final regression sample because income is logged.

Outputs: psid_matching.db and matched_parent_child.csv in data/cleaned_data/.

3. Estimate and compare IGE — data_analysis.py

The third script uses the matched data to estimate two log-log regressions:
\[
\log(ChildIncome_i) = \alpha + \beta\log(ParentIncome_i) + \epsilon_i.
\]
The coefficient \(\beta\) is the intergenerational income elasticity (IGE). One model uses 2022 family income; the other uses the average of 2020 and 2022 family income. Both models use the same final sample, allowing the estimates to be compared without a change in sample size.

Outputs: regression_results.csv, single_year_regression.txt, and multi_year_regression.txt in result/.

## Reproducibility

Run the scripts in order from the project root:
1. code/data_process.py
2. code/data_SQLmatch.py
3. code/data_analysis.py
Before running, confirm that the project path configured at the beginning of each script points to the local repository directory. The scripts expect the raw source files under data/raw_data/ and write intermediate and final outputs to the directories shown above. The Quarto file, blog6.qmd, provides the accompanying tutorial and explains the SQL matching logic.
