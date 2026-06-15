import sqlite3
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import mannwhitneyu


DB_PATH = Path("cell_counts.db")

OUTPUT_DATA_PATH = Path("part3_responder_data.csv")
OUTPUT_STATS_PATH = Path("part3_responder_stats.csv")
OUTPUT_PLOT_PATH = Path("part3_responder_boxplots.png")
OUTPUT_SUMMARY_PATH = Path("part3_summary.txt")


def load_percentage_data(conn):
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
            subj.condition,
            s.sample_type,
            t.treatment_name AS treatment,
            s.response,
            s.time_from_treatment_start,
            cp.population_name AS population,
            cp.display_order,
            cc.count,
            st.total_count,
            ROUND(100.0 * cc.count / st.total_count, 2) AS percentage
        FROM cell_counts AS cc
        JOIN sample_totals AS st
            ON cc.sample_id = st.sample_id
        JOIN cell_populations AS cp
            ON cc.population_id = cp.population_id
        JOIN samples AS s
            ON cc.sample_id = s.sample_id
        JOIN subjects AS subj
            ON s.subject_id = subj.subject_id
        JOIN treatments AS t
            ON s.treatment_id = t.treatment_id
        ORDER BY
            cc.sample_id,
            cp.display_order;
    """

    return pd.read_sql_query(query, conn)


def filter_part3_data(df):
    part3_df = df[
        (df["condition"].str.lower() == "melanoma") &
        (df["sample_type"].str.lower() == "pbmc") &
        (df["treatment"].str.lower() == "miraclib") &
        (df["response"].str.lower().isin(["yes", "no"]))
    ].copy()

    return part3_df


def calculate_statistics(part3_df):
    results = []

    populations = (
        part3_df[["population", "display_order"]]
        .drop_duplicates()
        .sort_values("display_order")
    )


    for _, pop_row in populations.iterrows():
        population = pop_row["population"]

        pop_df = part3_df[part3_df["population"] == population]

        responder_values = pop_df[pop_df["response"].str.lower() == "yes"]["percentage"]
        non_responder_values = pop_df[pop_df["response"].str.lower() == "no"]["percentage"]

        responder_mean = responder_values.mean()
        non_responder_mean = non_responder_values.mean()

        responder_median = responder_values.median()
        non_responder_median = non_responder_values.median()

        if len(responder_values) > 0 and len(non_responder_values) > 0:
            stat, p_value = mannwhitneyu(
                responder_values,
                non_responder_values,
                alternative="two-sided"
            )
        else:
            p_value = None

        results.append({
            "population": population,
            "n_responders": len(responder_values),
            "n_non_responders": len(non_responder_values),
            "responder_mean_percentage": round(responder_mean, 2),
            "non_responder_mean_percentage": round(non_responder_mean, 2),
            "responder_median_percentage": round(responder_median, 2),
            "non_responder_median_percentage": round(non_responder_median, 2),
            "difference_in_means": round(responder_mean - non_responder_mean, 2),
            "p_value": p_value,
        })

    return pd.DataFrame(results)


def make_boxplots(part3_df):
    populations = (
        part3_df[["population", "display_order"]]
        .drop_duplicates()
        .sort_values("display_order")["population"]
        .tolist()
    )

    fig, axes = plt.subplots(
        nrows=1,
        ncols=len(populations),
        figsize=(16, 5),
        sharey=True
    )

    for ax, population in zip(axes, populations):
        pop_df = part3_df[part3_df["population"] == population]

        yes_values = pop_df[pop_df["response"].str.lower() == "yes"]["percentage"]
        no_values = pop_df[pop_df["response"].str.lower() == "no"]["percentage"]

        ax.boxplot(
            [yes_values, no_values],
            tick_labels=["yes", "no"]
        )

        ax.set_title(population)
        ax.set_xlabel("Response")
        ax.set_ylabel("Percentage")

    fig.suptitle("Immune Cell Population Percentages for PBMC Samples: Miraclib Responders vs Non-Responders")
    plt.tight_layout()

    plt.savefig(OUTPUT_PLOT_PATH, dpi=300)
    plt.show()

def write_summary(stats_df):
    cd4_row = stats_df[stats_df["population"] == "cd4_t_cell"].iloc[0]

    cd4_p_value = cd4_row["p_value"]
    cd4_difference = cd4_row["difference_in_means"]

    if cd4_difference > 0:
        direction_sentence = "Responders had a higher average CD4 T-cell percentage than non-responders."
    else:
        direction_sentence = "Responders had a lower average CD4 T-cell percentage than non-responders."

    summary = f"""
    Part 3 Summary

    CD4 T cells showed the strongest evidence of a difference between responders and non-responders.

    The Mann-Whitney U test gave an unadjusted p-value of {cd4_p_value:.3f} for CD4 T cells. This is below the standard 0.05 threshold, suggesting a potential difference in CD4 T-cell percentage between the two response groups.

    {direction_sentence}

    The remaining immune-cell populations had p-values above 0.05, so there was not strong evidence of response-associated differences for those populations.

    Because five immune-cell populations were tested, this CD4 result should be interpreted cautiously after considering multiple comparisons. It is best described as a promising signal rather than a definitive biomarker.
    """

    print(summary)

    with open(OUTPUT_SUMMARY_PATH, "w") as f:
        f.write(summary)


def main():
    
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Could not find {DB_PATH}. Run load_data.py first.")

    conn = sqlite3.connect(DB_PATH)

    df = load_percentage_data(conn)

    conn.close()

    part3_df = filter_part3_data(df)

    print("Filtered Part 3 data:")
    print(part3_df.head())

    print("\nNumber of rows after filtering:")
    print(len(part3_df))
    
    #Should be number of rows/5 since each sample has 5 populations.
    print("\nNumber of unique samples after filtering:")
    print(part3_df["sample"].nunique())

    part3_df.to_csv(OUTPUT_DATA_PATH, index=False)

    stats_df = calculate_statistics(part3_df)

    print("\nPart 3 statistical summary:")
    print(stats_df)

    stats_df.to_csv(OUTPUT_STATS_PATH, index=False)

    make_boxplots(part3_df)
    
    write_summary(stats_df)

    print(f"\nSaved filtered data to: {OUTPUT_DATA_PATH}")
    print(f"Saved statistics to: {OUTPUT_STATS_PATH}")
    print(f"Saved boxplot to: {OUTPUT_PLOT_PATH}")
    print(f"Saved text summary to: {OUTPUT_SUMMARY_PATH}")


if __name__ == "__main__":
    main()