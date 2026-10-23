# =============================================================================
# 01_data_processing.py
# PSID Blog 6
# Step 1: Clean individual data and parse parent identification data
# =============================================================================

import pandas as pd
from pathlib import Path


# =============================================================================
# 1. Project paths
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
RAW_DATA_PATH = DATA_DIR / "raw_data"
CLEANED_DATA_PATH = DATA_DIR / "cleaned_data"

individual_file = RAW_DATA_PATH / "individual_data.csv"
parent_id_file = RAW_DATA_PATH / "parent_identification.txt"

individual_output = CLEANED_DATA_PATH / "individual_long.csv"
parent_id_output = CLEANED_DATA_PATH / "parent_identification.csv"

# Create output folder if it does not exist
CLEANED_DATA_PATH.mkdir(parents=True, exist_ok=True)

# Check input files
if not individual_file.exists():
    raise FileNotFoundError(
        f"Individual data file not found: {individual_file}"
    )

if not parent_id_file.exists():
    raise FileNotFoundError(
        f"Parent identification file not found: {parent_id_file}"
    )


# =============================================================================
# 2. Read raw individual data
# =============================================================================

print("=" * 70)
print("STEP 1: PROCESS INDIVIDUAL DATA")
print("=" * 70)

print("\nReading individual data...")

individual_data = pd.read_csv(individual_file)

print("Individual data shape:", individual_data.shape)

print("\nVariables:")
print(individual_data.columns.tolist())


# =============================================================================
# 3. Check required variables
# =============================================================================

required_variables = [
    # Permanent individual identifiers
    "ER30001",
    "ER30002",

    # 2021 PSID wave -> 2020 family income
    "ER78002",
    "ER81775",
    "ER34901",
    "ER34902",
    "ER34903",
    "ER34904",

    # 2023 PSID wave -> 2022 family income
    "ER82002",
    "ER85629",
    "ER35101",
    "ER35102",
    "ER35103",
    "ER35104"
]

missing_variables = [
    var for var in required_variables
    if var not in individual_data.columns
]

if missing_variables:
    raise ValueError(
        "The following required variables are missing:\n"
        + "\n".join(missing_variables)
    )

print("\nAll required individual variables are available.")


# =============================================================================
# 4. Construct permanent person ID
#
# ER30001 = 1968 family interview number
# ER30002 = person number
#
# Convert identifiers to numeric values first to avoid IDs such as "4.0_3.0".
# =============================================================================

individual_data["ER30001"] = pd.to_numeric(
    individual_data["ER30001"],
    errors="coerce"
)

individual_data["ER30002"] = pd.to_numeric(
    individual_data["ER30002"],
    errors="coerce"
)


def make_person_id(interview_number, person_number):
    """
    Construct a permanent PSID person ID.

    Example:
        Interview number = 4
        Person number = 3
        Result = "4_3"
    """

    if pd.isna(interview_number) or pd.isna(person_number):
        return None

    interview_number = int(interview_number)
    person_number = int(person_number)

    if interview_number <= 0 or person_number <= 0:
        return None

    return f"{interview_number}_{person_number}"


individual_data["family_id_1968"] = individual_data["ER30001"]
individual_data["person_number"] = individual_data["ER30002"]

individual_data["person_id"] = individual_data.apply(
    lambda row: make_person_id(
        row["ER30001"],
        row["ER30002"]
    ),
    axis=1
)

print(
    "\nUnique permanent person IDs:",
    individual_data["person_id"].nunique()
)


# =============================================================================
# 5. Construct 2020 income-year data
#
# ER78002 = 2021 Family Interview ID
# ER81775 = Total Family Income - 2020
#
# ER34901 = 2021 Interview Number
# ER34902 = Sequence Number 21
# ER34903 = Relation to Reference Person 21
# ER34904 = Age of Individual 21
# =============================================================================

data_2020 = individual_data[
    [
        "person_id",
        "ER30001",
        "ER30002",
        "ER78002",
        "ER81775",
        "ER34901",
        "ER34902",
        "ER34903",
        "ER34904"
    ]
].copy()

data_2020 = data_2020.rename(
    columns={
        "ER30001": "family_id_1968",
        "ER30002": "person_number",
        "ER78002": "family_id",
        "ER81775": "family_income",
        "ER34901": "interview_number",
        "ER34902": "sequence_number",
        "ER34903": "relation_to_reference",
        "ER34904": "age"
    }
)

data_2020["year"] = 2020


# =============================================================================
# 6. Construct 2022 income-year data
#
# ER82002 = 2023 Family Interview ID
# ER85629 = Total Family Income - 2022
#
# ER35101 = 2023 Interview Number
# ER35102 = Sequence Number 23
# ER35103 = Relation to Reference Person 23
# ER35104 = Age of Individual 23
# =============================================================================

data_2022 = individual_data[
    [
        "person_id",
        "ER30001",
        "ER30002",
        "ER82002",
        "ER85629",
        "ER35101",
        "ER35102",
        "ER35103",
        "ER35104"
    ]
].copy()

data_2022 = data_2022.rename(
    columns={
        "ER30001": "family_id_1968",
        "ER30002": "person_number",
        "ER82002": "family_id",
        "ER85629": "family_income",
        "ER35101": "interview_number",
        "ER35102": "sequence_number",
        "ER35103": "relation_to_reference",
        "ER35104": "age"
    }
)

data_2022["year"] = 2022


# =============================================================================
# 7. Combine 2020 and 2022
# =============================================================================

individual_long = pd.concat(
    [data_2020, data_2022],
    ignore_index=True
)

print(
    "\nLong-format data shape before cleaning:",
    individual_long.shape
)


# =============================================================================
# 8. Convert numeric variables
# =============================================================================

numeric_variables = [
    "family_id_1968",
    "person_number",
    "family_id",
    "family_income",
    "interview_number",
    "sequence_number",
    "relation_to_reference",
    "age",
    "year"
]

for variable in numeric_variables:
    individual_long[variable] = pd.to_numeric(
        individual_long[variable],
        errors="coerce"
    )


# =============================================================================
# 9. Remove zero-filled records
#
# In the PSID cross-year individual file, year-specific variables can be
# zero-filled when an individual is not observed in a particular wave.
#
# Keep observations with a positive interview number.
# Do not treat zero family income as missing at this stage.
# =============================================================================

print(
    "\nObservations by year before interview-number filtering:"
)

print(
    individual_long.groupby("year")["person_id"].count()
)

individual_long = individual_long[
    individual_long["interview_number"] > 0
].copy()

# Rows without a usable permanent person ID cannot be matched later.
individual_long = individual_long[
    individual_long["person_id"].notna()
].copy()

print(
    "\nObservations by year after cleaning:"
)

print(
    individual_long.groupby("year")["person_id"].count()
)


# =============================================================================
# 10. Check duplicate person-year observations
# =============================================================================

duplicate_count = (
    individual_long
    .duplicated(subset=["person_id", "year"])
    .sum()
)

print("\nDuplicate person-year observations:", duplicate_count)

if duplicate_count > 0:
    raise ValueError(
        "Duplicate person-year observations were found."
    )


# =============================================================================
# 11. Check family income
# =============================================================================

print("\nFamily income summary:")

print(
    individual_long["family_income"].describe()
)

print(
    "\nNumber of zero family-income observations:",
    (individual_long["family_income"] == 0).sum()
)

print(
    "\nNumber of missing family-income observations:",
    individual_long["family_income"].isna().sum()
)


# =============================================================================
# 12. Save cleaned long-format individual data
# =============================================================================

output_columns = [
    "person_id",
    "family_id_1968",
    "person_number",
    "family_id",
    "sequence_number",
    "relation_to_reference",
    "age",
    "family_income",
    "year"
]

individual_long = individual_long[output_columns].copy()

individual_long.to_csv(
    individual_output,
    index=False
)

print("\nSaved cleaned individual data to:")
print(individual_output)

print("\nFinal individual data shape:", individual_long.shape)

print("\nFirst observations:")
print(individual_long.head())


# =============================================================================
# 13. Read Parent Identification TXT using fixed-width fields
#
# The original PSID file contains 40 variables and has 75 characters per row.
#
# PID1       : Release number
# PID2-PID3  : Child identifier components
# PID4-PID5  : Biological mother identifier components
# PID23-PID24: Biological father identifier components
#
# Do NOT use sep=r'\s+' or split() to read this file.
# The original TXT must be read using its fixed-width field layout.
# =============================================================================

print("\n" + "=" * 70)
print("STEP 2: PROCESS PARENT IDENTIFICATION DATA")
print("=" * 70)

print("\nReading parent identification data...")

# Widths for PID1-PID9
# PID1 = 1 character
# PID2 = 4 characters
# PID3 = 3 characters
# PID4 = 4 characters
# PID5 = 3 characters
# PID6 = 4 characters
# PID7 = 3 characters
# PID8 = 4 characters
# PID9 = 3 characters
#
# PID10-PID22: 13 one-character source indicators
# PID23-PID28: three interview/person identifier pairs
# PID29-PID40: 12 one-character source indicators

pid_widths = (
    [1, 4, 3, 4, 3, 4, 3, 4, 3]
    + [1] * 13
    + [4, 3, 4, 3, 4, 3]
    + [1] * 12
)

pid_columns = [
    f"PID{i}" for i in range(1, 41)
]

# Validate the field-width specification before reading the file.
if len(pid_widths) != 40:
    raise ValueError(
        f"Expected 40 field widths, got {len(pid_widths)}."
    )

if sum(pid_widths) != 75:
    raise ValueError(
        f"Expected a total record width of 75, "
        f"got {sum(pid_widths)}."
    )

# Check the first record's width.
with open(parent_id_file, "r", encoding="utf-8") as file:
    first_line = file.readline().rstrip("\r\n")

if len(first_line) != 75:
    raise ValueError(
        "The first record in parent_identification.txt "
        f"has {len(first_line)} characters instead of 75. "
        "Please verify that the correct raw file was downloaded."
    )

# Read the fixed-width TXT file.
parent_identification = pd.read_fwf(
    parent_id_file,
    widths=pid_widths,
    names=pid_columns,
    header=None,
    dtype=str
)

print(
    "Parent identification data shape:",
    parent_identification.shape
)

if parent_identification.shape[1] != 40:
    raise ValueError(
        "The parent identification file should contain 40 variables."
    )

# Convert PID variables to numeric values.
for variable in pid_columns:
    parent_identification[variable] = pd.to_numeric(
        parent_identification[variable],
        errors="coerce"
    )

# Check the key identifiers needed for parent-child matching.
required_pid_variables = [
    "PID2",
    "PID3",
    "PID4",
    "PID5",
    "PID23",
    "PID24"
]

missing_pid_variables = [
    var for var in required_pid_variables
    if var not in parent_identification.columns
]

if missing_pid_variables:
    raise ValueError(
        "Required parent identification variables are missing:\n"
        + "\n".join(missing_pid_variables)
    )

print("\nKey identifier variables are available.")

print("\nExample parent identification records:")

print(
    parent_identification[
        [
            "PID2",
            "PID3",
            "PID4",
            "PID5",
            "PID23",
            "PID24"
        ]
    ].head(10)
)


# =============================================================================
# 14. Save cleaned parent identification data
# =============================================================================

parent_identification.to_csv(
    parent_id_output,
    index=False
)

print("\nSaved parent identification data to:")
print(parent_id_output)


# =============================================================================
# 15. Check whether individual IDs can be found in the identification file
#
# This is a diagnostic only. The SQL matching is performed in Stage 2.
# =============================================================================

print("\n" + "=" * 70)
print("STEP 3: CHECK PERSON-ID MATCHING")
print("=" * 70)

individual_person_ids = set(
    individual_long["person_id"].dropna().unique()
)

id_definitions = [
    ("Child", "PID2", "PID3"),
    ("Mother", "PID4", "PID5"),
    ("Father", "PID23", "PID24")
]

for relationship, interview_var, person_var in id_definitions:

    candidate_ids = parent_identification.apply(
        lambda row: make_person_id(
            row[interview_var],
            row[person_var]
        ),
        axis=1
    )

    candidate_ids = set(
        candidate_ids.dropna().unique()
    )

    matched_ids = candidate_ids.intersection(
        individual_person_ids
    )

    print(f"\n{relationship} IDs:")
    print("  Unique valid IDs in identification file:",
          len(candidate_ids))
    print("  IDs found in individual_long.csv:",
          len(matched_ids))


# =============================================================================
# 16. Final summary
# =============================================================================

print("\n" + "=" * 70)
print("STEP 1 COMPLETED")
print("=" * 70)

print("\nGenerated files:")

print("1.", individual_output)
print("2.", parent_id_output)

print("\nIndividual data shape:")
print(individual_long.shape)

print("\nParent identification data shape:")
print(parent_identification.shape)

print("\nStage 1 completed successfully.")


if __name__ == "__main__":
    pass
