import sqlite3
from pathlib import Path

import pandas as pd


DB_PATH = Path("cell_counts.db")

OUTPUT_SUBSET_PATH = Path("part4_baseline_melanoma_pbmc_miraclib_samples.csv")
OUTPUT_PROJECT_COUNTS_PATH = Path("part4_samples_by_project.csv")
OUTPUT_RESPONSE_COUNTS_PATH = Path("part4_subjects_by_response.csv")
OUTPUT_SEX_COUNTS_PATH = Path("part4_subjects_by_sex.csv")
OUTPUT_AVERAGE_B_CELL = Path("part4_average_b_cells_melanoma_male_responders_time0.csv")


def load_subset(conn):
    query = """
        SELECT DISTINCT
            s.sample_id AS sample,
            subj.subject_id,
            p.project_name AS project,
            subj.condition,
            subj.sex,
            s.sample_type,
            t.treatment_name AS treatment,
            s.response,
            s.time_from_treatment_start
        FROM samples AS s
        JOIN subjects AS subj
            ON s.subject_id = subj.subject_id
        JOIN projects AS p
            ON subj.project_id = p.project_id
        JOIN treatments AS t
            ON s.treatment_id = t.treatment_id
        WHERE
            LOWER(subj.condition) = 'melanoma'
            AND LOWER(s.sample_type) = 'pbmc'
            AND s.time_from_treatment_start = 0
            AND LOWER(t.treatment_name) = 'miraclib'
        ORDER BY
            p.project_name,
            subj.subject_id,
            s.sample_id;
    """

    return pd.read_sql_query(query, conn)


def summarize_subset(subset_df):
    samples_by_project = (
        subset_df
        .groupby("project", as_index=False)
        .agg(number_of_samples=("sample", "nunique"))
    )

    subject_level_df = subset_df[
        ["subject_id", "response", "sex"]
    ].drop_duplicates()

    subjects_by_response = (
        subject_level_df
        .groupby("response", as_index=False)
        .agg(number_of_subjects=("subject_id", "nunique"))
    )

    subjects_by_sex = (
        subject_level_df
        .groupby("sex", as_index=False)
        .agg(number_of_subjects=("subject_id", "nunique"))
    )

    return samples_by_project, subjects_by_response, subjects_by_sex


def average_b_cells_melanoma_male_responders_time0(conn):
    query = """
        SELECT
            ROUND(AVG(cc.count), 2) AS average_b_cells
        FROM cell_counts AS cc
        JOIN cell_populations AS cp
            ON cc.population_id = cp.population_id
        JOIN samples AS s
            ON cc.sample_id = s.sample_id
        JOIN subjects AS subj
            ON s.subject_id = subj.subject_id
        WHERE
            LOWER(subj.condition) = 'melanoma'
            AND LOWER(subj.sex) = 'm'
            AND LOWER(s.response) = 'yes'
            AND s.time_from_treatment_start = 0
            AND LOWER(cp.population_name) = 'b_cell';
    """

    result_df = pd.read_sql_query(query, conn)
    return result_df



def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Could not find {DB_PATH}. Run load_data.py first.")

    conn = sqlite3.connect(DB_PATH)

    subset_df = load_subset(conn)
    
    average_b_cells_df = average_b_cells_melanoma_male_responders_time0(conn)

    conn.close()

    samples_by_project, subjects_by_response, subjects_by_sex = summarize_subset(subset_df)

    print("\nBaseline melanoma PBMC samples treated with miraclib:")
    print(subset_df)

    print("\nNumber of samples from each project:")
    print(samples_by_project)

    print("\nNumber of subjects by response:")
    print(subjects_by_response)

    print("\nNumber of subjects by sex:")
    print(subjects_by_sex)
    
    
    
    
    
    print("\nAverage number of B cells for melanoma male responders at time=0:")
    print(average_b_cells_df)

    average_value = average_b_cells_df["average_b_cells"].iloc[0]
    print(f"\nAnswer: {average_value:.2f}")




    subset_df.to_csv(OUTPUT_SUBSET_PATH, index=False)
    samples_by_project.to_csv(OUTPUT_PROJECT_COUNTS_PATH, index=False)
    subjects_by_response.to_csv(OUTPUT_RESPONSE_COUNTS_PATH, index=False)
    subjects_by_sex.to_csv(OUTPUT_SEX_COUNTS_PATH, index=False)

    print(f"\nSaved subset data to: {OUTPUT_SUBSET_PATH}")
    print(f"Saved project counts to: {OUTPUT_PROJECT_COUNTS_PATH}")
    print(f"Saved response counts to: {OUTPUT_RESPONSE_COUNTS_PATH}")
    print(f"Saved sex counts to: {OUTPUT_SEX_COUNTS_PATH}")
    
    
    
    average_b_cells_df.to_csv(OUTPUT_AVERAGE_B_CELL, index=False)
    
    print(f"Saved average b cell to: {OUTPUT_AVERAGE_B_CELL}")
    


if __name__ == "__main__":
    main()