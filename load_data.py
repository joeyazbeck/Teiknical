import sqlite3
from pathlib import Path
import pandas as pd



CSV_PATH = Path("cell-count.csv")
DB_PATH = Path("cell_counts.db")

CELL_POPULATIONS = [
    "b_cell",
    "cd8_t_cell",
    "cd4_t_cell",
    "nk_cell",
    "monocyte",
]


def create_schema(conn):
    cursor = conn.cursor()
    
    cursor.execute("""
                   DROP TABLE IF EXISTS cell_counts;
                   """)
                   
    cursor.execute("""
                   DROP TABLE IF EXISTS samples;
                   """)
                                  
    cursor.execute("""
                   DROP TABLE IF EXISTS subjects;
                   """)

    cursor.execute("""
                   DROP TABLE IF EXISTS treatments;
                   """)
    
    cursor.execute("""
                   DROP TABLE IF EXISTS projects;
                   """)
    
    cursor.execute("""
                   DROP TABLE IF EXISTS cell_populations;
                   """)
                   

    cursor.execute("""
                   CREATE TABLE projects (
                       project_id INTEGER PRIMARY KEY AUTOINCREMENT,
                       project_name TEXT UNIQUE NOT NULL
                       );
                   """)  


    cursor.execute("""
                   CREATE TABLE treatments (
                       treatment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                       treatment_name TEXT UNIQUE NOT NULL
                       );
                   """)


    cursor.execute("""
                   CREATE TABLE cell_populations (
                       population_id INTEGER PRIMARY KEY AUTOINCREMENT,
                       population_name TEXT UNIQUE NOT NULL,
                       display_order INTEGER NOT NULL
                       );
                   """)

    
    cursor.execute("""
                   CREATE TABLE subjects (
                       subject_id TEXT PRIMARY KEY,
                       project_id INTEGER NOT NULL,
                       condition TEXT NOT NULL,
                       age INTEGER NOT NULL,
                       sex TEXT NOT NULL,
                       FOREIGN KEY (project_id) REFERENCES projects(project_id)
                       );
                   """)


    cursor.execute("""
                   CREATE TABLE samples (
                       sample_id TEXT PRIMARY KEY,
                       subject_id TEXT NOT NULL,
                       treatment_id INTEGER NOT NULL,
                       response TEXT,
                       sample_type TEXT NOT NULL,
                       time_from_treatment_start INTEGER NOT NULL,
                       FOREIGN KEY (subject_id) REFERENCES subjects(subject_id),
                       FOREIGN KEY (treatment_id) REFERENCES treatments(treatment_id)
                       );
                   """)    


    cursor.execute("""
                   CREATE TABLE cell_counts (
                       sample_id TEXT NOT NULL,
                       population_id INTEGER NOT NULL,
                       count INTEGER NOT NULL,
                       PRIMARY KEY (sample_id, population_id),
                       FOREIGN KEY (sample_id) REFERENCES samples(sample_id),
                       FOREIGN KEY (population_id) REFERENCES cell_populations(population_id)
                       );
                   """)
    
    conn.commit()


def load_data(conn):
    df = pd.read_csv(CSV_PATH)

    cursor = conn.cursor()

    # Load projects
    for project in sorted(df["project"].unique()):
        cursor.execute(
            "INSERT OR IGNORE INTO projects (project_name) VALUES (?)",
            (project,)
        )

    # Load treatments
    for treatment in sorted(df["treatment"].unique()):
        cursor.execute(
            "INSERT OR IGNORE INTO treatments (treatment_name) VALUES (?)",
            (treatment,)
        )

    # Load cell population names
    for order, population in enumerate(CELL_POPULATIONS, start=1):
        cursor.execute(
            """
            INSERT OR IGNORE INTO cell_populations
            (population_name, display_order)
            VALUES (?, ?)
            """,
            (population, order)
        )

    # Load subjects
    subject_rows = df[
        ["subject", "project", "condition", "age", "sex"]
    ].drop_duplicates()

    for _, row in subject_rows.iterrows():
        cursor.execute(
            "SELECT project_id FROM projects WHERE project_name = ?",
            (row["project"],)
        )
        project_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT OR IGNORE INTO subjects
            (subject_id, project_id, condition, age, sex)
            VALUES (?, ?, ?, ?, ?)
        """, (
            row["subject"],
            project_id,
            row["condition"],
            int(row["age"]),
            row["sex"],
        ))

    # Load samples
    for _, row in df.iterrows():
        cursor.execute(
            "SELECT treatment_id FROM treatments WHERE treatment_name = ?",
            (row["treatment"],)
        )
        treatment_id = cursor.fetchone()[0]

        response = row["response"]
        if pd.isna(response):
            response = None

        cursor.execute("""
            INSERT OR IGNORE INTO samples
            (sample_id, subject_id, treatment_id, response, sample_type, time_from_treatment_start)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            row["sample"],
            row["subject"],
            treatment_id,
            response,
            row["sample_type"],
            int(row["time_from_treatment_start"]),
        ))

    # Load cell counts
    for _, row in df.iterrows():
        sample_id = row["sample"]

        for population in CELL_POPULATIONS:
            cursor.execute(
                "SELECT population_id FROM cell_populations WHERE population_name = ?",
                (population,)
            )
            population_id = cursor.fetchone()[0]

            cursor.execute("""
                INSERT OR REPLACE INTO cell_counts
                (sample_id, population_id, count)
                VALUES (?, ?, ?)
            """, (
                sample_id,
                population_id,
                int(row[population]),
            ))

    conn.commit()

def main():
    
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Could not find {CSV_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    
    create_schema(conn)
    load_data(conn)

    conn.close()

    print(f"Database created successfully: {DB_PATH}")

if __name__ == "__main__":
    main()
    
    