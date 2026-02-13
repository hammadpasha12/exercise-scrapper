import pandas as pd
import itertools
import os

# -------- CONFIG --------
INPUT_CSV = "analyzed_exercises.csv"
OUTPUT_CSV = "exercises_new_expanded.csv"
# ------------------------

df = pd.read_csv(INPUT_CSV)

def split_values(val):
    """Split comma-separated values safely"""
    if pd.isna(val) or str(val).strip() == "":
        return [None]
    return [v.strip() for v in str(val).split(",") if v.strip()]

expanded_rows = []

for _, row in df.iterrows():

    equipment_list = split_values(row["equipment_name"])
    primary_muscles = split_values(row["primary_muscle_name"])
    secondary_muscles = split_values(row["secondary_muscle_name"])
    primary_joints = split_values(row["primary_joint_name"])

    # Cartesian product
    for equipment, pm, sm, pj in itertools.product(
        equipment_list,
        primary_muscles,
        secondary_muscles,
        primary_joints
    ):
        new_row = row.copy()
        new_row["equipment_name"] = equipment
        new_row["primary_muscle_name"] = pm
        new_row["secondary_muscle_name"] = sm
        new_row["primary_joint_name"] = pj

        expanded_rows.append(new_row)

# Create expanded dataframe
expanded_df = pd.DataFrame(expanded_rows)

# Save updated CSV
expanded_df.to_csv(OUTPUT_CSV, index=False)

print(f"✅ Expanded CSV generated: {OUTPUT_CSV}")
print(f"Original rows: {len(df)}")
print(f"Expanded rows: {len(expanded_df)}")
