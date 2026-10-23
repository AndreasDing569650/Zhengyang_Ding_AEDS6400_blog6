# =============================================================================
# 02_SQL_match.py
# PSID Blog 6
# Step 2: Match parents and children using SQL
# =============================================================================

import pandas as pd
import sqlite3
from pathlib import Path


# =============================================================================
# 1. Project paths
# =============================================================================

project_path = Path(
    r"C:\Users\lenovo\PycharmProjects\6400_blog_6"
)

cleaned_data_path = (
    project_path
    / "data"
    / "cleaned_data"
)

individual_file = (
    cleaned_data_path
    / "individual_long.csv"
)

parent_file = (
    cleaned_data_path
    / "parent_identification.csv"
)

database_path = (
    cleaned_data_path
    / "psid_matching.db"
)

matched_output = (
    cleaned_data_path
    / "matched_parent_child.csv"
)


# =============================================================================
# 2. Read cleaned data
# =============================================================================

print("Reading cleaned individual data...")

individual_data = pd.read_csv(
    individual_file
)

print(
    "Individual data shape:",
    individual_data.shape
)


print("\nReading parent identification data...")

parent_data = pd.read_csv(
    parent_file
)

print(
    "Parent identification shape:",
    parent_data.shape
)


# =============================================================================
# 3. Check required PID variables
# =============================================================================

required_pid_variables = [
    "PID2",
    "PID3",
    "PID4",
    "PID5",
    "PID23",
    "PID24"
]

missing_pid = [
    var
    for var in required_pid_variables
    if var not in parent_data.columns
]

if missing_pid:

    raise ValueError(
        "The following PID variables are missing:\n"
        + "\n".join(missing_pid)
    )


# =============================================================================
# 4. Construct permanent person IDs in Parent Identification File
#
# Child:
#     PID2 + PID3
#
# Mother:
#     PID4 + PID5
#
# Father:
#     PID23 + PID24
# =============================================================================

def make_person_id(
    family_id,
    person_number
):

    if pd.isna(family_id) or pd.isna(person_number):

        return None

    if family_id == 0 or person_number == 0:

        return None

    return (
        str(int(family_id))
        + "_"
        + str(int(person_number))
    )


parent_data["child_id"] = parent_data.apply(
    lambda row: make_person_id(
        row["PID2"],
        row["PID3"]
    ),
    axis=1
)


parent_data["mother_id"] = parent_data.apply(
    lambda row: make_person_id(
        row["PID4"],
        row["PID5"]
    ),
    axis=1
)


parent_data["father_id"] = parent_data.apply(
    lambda row: make_person_id(
        row["PID23"],
        row["PID24"]
    ),
    axis=1
)


# =============================================================================
# 5. Keep only the parent-child identification variables
# =============================================================================

parent_data = parent_data[
    [
        "child_id",
        "mother_id",
        "father_id"
    ]
].copy()


# =============================================================================
# 6. Create SQLite database
# =============================================================================

if database_path.exists():

    database_path.unlink()

connection = sqlite3.connect(
    database_path
)


# =============================================================================
# 7. Load data into SQLite
# =============================================================================
#
# IMPORTANT:
# age is included here because it will be used AFTER the SQL matching
# and AFTER the merge.
# =============================================================================

individual_sql = individual_data[
    [
        "person_id",
        "family_id",
        "family_income",
        "year",
        "age"
    ]
].copy()


individual_sql.to_sql(
    "individual",
    connection,
    if_exists="replace",
    index=False
)


parent_data.to_sql(
    "parent_identification",
    connection,
    if_exists="replace",
    index=False
)


# =============================================================================
# 8. Create indexes
# =============================================================================

connection.execute("""
    CREATE INDEX idx_individual_person_year
    ON individual(person_id, year);
""")


connection.execute("""
    CREATE INDEX idx_parent_child
    ON parent_identification(child_id);
""")


connection.commit()


# =============================================================================
# 9. Create parent-child table
#
# Each child can be matched to:
# - mother
# - father
#
# UNION ALL keeps both parent observations.
# =============================================================================

connection.execute("""
    CREATE TABLE parent_child AS

    SELECT
        child_id,
        mother_id AS parent_id,
        'mother' AS parent_type
    FROM parent_identification
    WHERE mother_id IS NOT NULL

    UNION ALL

    SELECT
        child_id,
        father_id AS parent_id,
        'father' AS parent_type
    FROM parent_identification
    WHERE father_id IS NOT NULL;
""")

connection.commit()


# =============================================================================
# 10. Single-year analysis: 2022
#
# Child income:
#     family income of child's family in 2022
#
# Parent income:
#     family income of matched parent's family in 2022
#
# Exclude parent-child pairs living in the same family.
#
# IMPORTANT:
# NO AGE FILTER HERE.
# =============================================================================

single_year_query = """

SELECT
    pc.child_id,

    AVG(parent.family_income)
        AS parent_income_2022,

    child.family_income
        AS child_income_2022,

    child.age
        AS child_age_2022,

    AVG(parent.age)
        AS parent_age_2022

FROM parent_child AS pc

JOIN individual AS parent
    ON pc.parent_id = parent.person_id
    AND parent.year = 2022

JOIN individual AS child
    ON pc.child_id = child.person_id
    AND child.year = 2022

WHERE
    parent.family_id != child.family_id

GROUP BY
    pc.child_id,
    child.family_income,
    child.age

"""


single_year_data = pd.read_sql_query(
    single_year_query,
    connection
)


# =============================================================================
# 11. Multi-year analysis: 2020 and 2022
#
# Parent income:
#     average parent family income over 2020 and 2022
#
# Child income:
#     average child family income over 2020 and 2022
#
# We require the parent and child to be in different families
# in BOTH years.
#
# IMPORTANT:
# NO AGE FILTER HERE.
# =============================================================================

multi_year_query = """

SELECT
    pc.child_id,

    AVG(parent_2020.family_income)
        AS parent_income_2020,

    AVG(parent_2022.family_income)
        AS parent_income_2022,

    child_2020.family_income
        AS child_income_2020,

    child_2022.family_income
        AS child_income_2022,

    child_2022.age
        AS child_age_2022,

    AVG(parent_2022.age)
        AS parent_age_2022

FROM parent_child AS pc

JOIN individual AS parent_2020
    ON pc.parent_id = parent_2020.person_id
    AND parent_2020.year = 2020

JOIN individual AS parent_2022
    ON pc.parent_id = parent_2022.person_id
    AND parent_2022.year = 2022

JOIN individual AS child_2020
    ON pc.child_id = child_2020.person_id
    AND child_2020.year = 2020

JOIN individual AS child_2022
    ON pc.child_id = child_2022.person_id
    AND child_2022.year = 2022

WHERE
    parent_2020.family_id != child_2020.family_id

    AND

    parent_2022.family_id != child_2022.family_id

GROUP BY
    pc.child_id,
    child_2020.family_income,
    child_2022.family_income,
    child_2022.age

"""


multi_year_data = pd.read_sql_query(
    multi_year_query,
    connection
)


# =============================================================================
# 12. Construct two-year averages
# =============================================================================

multi_year_data["parent_income_avg"] = (
    multi_year_data["parent_income_2020"]
    +
    multi_year_data["parent_income_2022"]
) / 2


multi_year_data["child_income_avg"] = (
    multi_year_data["child_income_2020"]
    +
    multi_year_data["child_income_2022"]
) / 2


# =============================================================================
# 13. Merge single-year and multi-year results
# =============================================================================
#
# We keep the age variables from single_year_data.
#
# The age variables are already calculated from individual_long.csv
# and stored in SQLite.
#
# =============================================================================

matched_data = pd.merge(
    single_year_data,
    multi_year_data[
        [
            "child_id",
            "parent_income_avg",
            "child_income_avg"
        ]
    ],
    on="child_id",
    how="inner"
)


# =============================================================================
# 14. Remove invalid income observations
#
# Income must be positive because the regression will use logarithms.
# =============================================================================

matched_data = matched_data[
    (matched_data["parent_income_2022"] > 0)
    &
    (matched_data["child_income_2022"] > 0)
    &
    (matched_data["parent_income_avg"] > 0)
    &
    (matched_data["child_income_avg"] > 0)
].copy()


# =============================================================================
# 15. APPLY 2022 AGE FILTER AFTER MERGE
# =============================================================================
#
# Working-age definition:
#
#     Child: 25-64 in 2022
#     Parent: 25-64 in 2022
#
# This is deliberately done AFTER SQL matching and AFTER merging.
#
# =============================================================================

print("\n==============================")
print("AGE FILTER")
print("==============================")


print(
    "\nObservations before age filter:",
    len(matched_data)
)


print(
    "\nAge summary before age filter:"
)

print(
    matched_data[
        [
            "child_age_2022",
            "parent_age_2022"
        ]
    ].describe()
)


matched_data = matched_data[
    (matched_data["child_age_2022"] >= 25)
    &
    (matched_data["child_age_2022"] <= 64)
    &
    (matched_data["parent_age_2022"] >= 25)
    &
    (matched_data["parent_age_2022"] <= 64)
].copy()


print(
    "\nObservations after age filter:",
    len(matched_data)
)


print(
    "\nAge summary after age filter:"
)

print(
    matched_data[
        [
            "child_age_2022",
            "parent_age_2022"
        ]
    ].describe()
)


# =============================================================================
# 16. Save final matched data
# =============================================================================

matched_data.to_csv(
    matched_output,
    index=False
)


# =============================================================================
# 17. Print diagnostics
# =============================================================================

print("\n==============================")
print("SQL MATCHING RESULTS")
print("==============================")


print(
    "\nSingle-year observations:",
    len(single_year_data)
)


print(
    "Multi-year observations:",
    len(multi_year_data)
)


print(
    "Final matched observations:",
    len(matched_data)
)


print(
    "\nNumber of unique children:",
    matched_data["child_id"].nunique()
)


print(
    "\nFinal data:"
)

print(
    matched_data.head()
)


print(
    "\nSummary:"
)

print(
    matched_data.describe()
)


# =============================================================================
# 18. Close database
# =============================================================================

connection.close()


print(
    "\nSaved matched data to:"
)

print(
    matched_output
)


print(
    "\nSQLite database saved to:"
)

print(
    database_path
)


# =============================================================================
# END
# =============================================================================