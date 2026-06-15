import sqlite3
from pathlib import Path
import pandas as pd


DB_PATH = Path("cell_counts.db")
OUTPUT_PATH = Path("cell_count_summary.csv")


def create_summary():
    conn = sqlite3.connect(DB_PATH)

    query = """
        WITH sample_totals AS (
            SELECT
                sample_id,
                SUM(count) AS total_count
            FROM cell_counts
            GROUP BY sample_id
        )

        SELECT
            cc.sample_id AS sample,
            st.total_count,
            cp.population_name AS population,
            cc.count,
            ROUND(100.0 * cc.count / st.total_count, 2) AS percentage
        FROM cell_counts AS cc
        JOIN sample_totals AS st
            ON cc.sample_id = st.sample_id
        JOIN cell_populations AS cp
            ON cc.population_id = cp.population_id
        ORDER BY cc.sample_id, cp.display_order;
    """

    summary_df = pd.read_sql_query(query, conn)

    conn.close()

    #Save as csv
    summary_df.to_csv(OUTPUT_PATH, index=False)
    
    #Display first 10 rows
    print(summary_df.head(10))
    print(f"\nSummary saved to: {OUTPUT_PATH}")


def main():
    
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Could not find {DB_PATH}. Run load_data.py first.")

    create_summary()


if __name__ == "__main__":
    main()
    