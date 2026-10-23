# =============================================================================
# 03_data_analysis.py
# PSID Blog 6
# Step 3: Estimate intergenerational elasticity
# =============================================================================

import pandas as pd
import numpy as np
import statsmodels.api as sm
from pathlib import Path


# =============================================================================
# 1. Project paths
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
MATCHED_DATA_PATH = DATA_DIR / "matched_data"
RESULTS_PATH = REPO_ROOT / "result"

matched_file = MATCHED_DATA_PATH / "matched_parent_child.csv"
results_file = RESULTS_PATH / "regression_results.csv"

RESULTS_PATH.mkdir(parents=True, exist_ok=True)


# =============================================================================
# 2. Read matched data
# =============================================================================

data = pd.read_csv(matched_file)

print("Matched data shape:",
      data.shape)

print("\nVariables:")
print(data.columns.tolist())


# =============================================================================
# 3. Prepare regression samples
# =============================================================================

single_year = data[
    [
        "child_id",
        "parent_income_2022",
        "child_income_2022"
    ]
].copy()

multi_year = data[
    [
        "child_id",
        "parent_income_avg",
        "child_income_avg"
    ]
].copy()


# =============================================================================
# 4. Log income
# =============================================================================

single_year["log_parent_income"] = np.log(
    single_year["parent_income_2022"]
)

single_year["log_child_income"] = np.log(
    single_year["child_income_2022"]
)

multi_year["log_parent_income"] = np.log(
    multi_year["parent_income_avg"]
)

multi_year["log_child_income"] = np.log(
    multi_year["child_income_avg"]
)


# =============================================================================
# 5. Remove missing / infinite values
# =============================================================================

single_year = single_year.replace(
    [np.inf, -np.inf],
    np.nan
).dropna(
    subset=[
        "log_parent_income",
        "log_child_income"
    ]
)

multi_year = multi_year.replace(
    [np.inf, -np.inf],
    np.nan
).dropna(
    subset=[
        "log_parent_income",
        "log_child_income"
    ]
)


# =============================================================================
# 6. Single-year IGE
#
# log(child family income in 2022)
#     = alpha + beta * log(parent family income in 2022) + error
# =============================================================================

X_single = sm.add_constant(
    single_year["log_parent_income"]
)

y_single = single_year["log_child_income"]

model_single = sm.OLS(
    y_single,
    X_single
).fit()


# =============================================================================
# 7. Two-year average IGE
#
# log(child average family income)
#     = alpha + beta * log(parent average family income) + error
# =============================================================================

X_multi = sm.add_constant(
    multi_year["log_parent_income"]
)

y_multi = multi_year["log_child_income"]

model_multi = sm.OLS(
    y_multi,
    X_multi
).fit()


# =============================================================================
# 8. Print regression results
# =============================================================================

print("\n========================================")
print("SINGLE-YEAR IGE: 2022")
print("========================================")

print(model_single.summary())


print("\n========================================")
print("TWO-YEAR AVERAGE IGE: 2020-2022")
print("========================================")

print(model_multi.summary())


# =============================================================================
# 9. Extract key results
# =============================================================================

results = pd.DataFrame({
    "model": [
        "Single-year: 2022",
        "Two-year average: 2020-2022"
    ],

    "IGE": [
        model_single.params["log_parent_income"],
        model_multi.params["log_parent_income"]
    ],

    "SE": [
        model_single.bse["log_parent_income"],
        model_multi.bse["log_parent_income"]
    ],

    "p_value": [
        model_single.pvalues["log_parent_income"],
        model_multi.pvalues["log_parent_income"]
    ],

    "N": [
        int(model_single.nobs),
        int(model_multi.nobs)
    ],

    "R_squared": [
        model_single.rsquared,
        model_multi.rsquared
    ]
})


# =============================================================================
# 10. Save results
# =============================================================================

results.to_csv(
    results_file,
    index=False
)

print("\n========================================")
print("COMPARISON")
print("========================================")

print(results)

print("\nSaved regression results to:")
print(results_file)


# =============================================================================
# END
# =============================================================================

if __name__ == "__main__":
    pass
