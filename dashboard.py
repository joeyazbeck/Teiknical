import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from scipy.stats import mannwhitneyu


DB_PATH = Path("cell_counts.db")


st.set_page_config(
    page_title="Teiko Cell Count Dashboard",
    layout="wide"
)


PLOTLY_CONFIG = {
    "displayModeBar": True,
    "displaylogo": False,
    "responsive": True,
}

@st.cache_data
def load_initial_analysis_data():
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
            s.subject_id,
            p.project_name AS project,
            subj.condition,
            subj.age,
            subj.sex,
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
        JOIN projects AS p
            ON subj.project_id = p.project_id
        JOIN treatments AS t
            ON s.treatment_id = t.treatment_id
        ORDER BY
            cc.sample_id,
            cp.display_order;
    """

    df = pd.read_sql_query(query, conn)

    conn.close()

    return df



def calculate_responder_statistics(part3_df):
    results = []

    populations = (
        part3_df[["population", "display_order"]]
        .drop_duplicates()
        .sort_values("display_order")
    )

    for _, pop_row in populations.iterrows():
        population = pop_row["population"]

        pop_df = part3_df[part3_df["population"] == population]

        responder_values = pop_df[
            pop_df["response"].astype(str).str.lower() == "yes"
        ]["percentage"]

        non_responder_values = pop_df[
            pop_df["response"].astype(str).str.lower() == "no"
        ]["percentage"]

        responder_mean = responder_values.mean()
        non_responder_mean = non_responder_values.mean()
        difference = responder_mean - non_responder_mean

        if len(responder_values) > 0 and len(non_responder_values) > 0:
            _, p_value = mannwhitneyu(
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
            "difference_in_means": round(difference, 2),
            "p_value": p_value,
        })

    stats_df = pd.DataFrame(results)

    if not stats_df.empty:
        stats_df["p_value"] = stats_df["p_value"].round(4)
        stats_df["significant_unadjusted_0.05"] = stats_df["p_value"] < 0.05

    return stats_df




def clean_text(series):
    return series.astype(str).str.lower().str.strip()



def main():
    st.title("Teiko Cell Count Dashboard")

    if not DB_PATH.exists():
        st.error("Could not find cell_counts.db. Run load_data.py first.")
        return

    df = load_initial_analysis_data()

    st.header("Part 1: Database Status")

    st.success("Database loaded successfully.")

    col1, col2 = st.columns(2)

    col1.metric("Unique samples", df["sample"].nunique())
    col2.metric("Unique subjects", df["subject_id"].nunique())

    st.write(
        "The dashboard reads from the SQLite database created by `load_data.py`. "
        "The database stores subjects, samples, treatments, projects, immune-cell populations, "
        "and cell counts in separate relational tables."
    )

    st.header("Part 2: Initial Cell Count Analysis")

    st.write(
        "This section shows the total cell count for each sample and the percentage "
        "contribution of each immune-cell population."
    )

    population_order = (
        df[["population", "display_order"]]
        .drop_duplicates()
        .sort_values("display_order")["population"]
        .tolist()
    )

    st.sidebar.header("Filters")

    selected_conditions = st.sidebar.multiselect(
        "Condition",
        sorted(df["condition"].dropna().unique()),
        default=sorted(df["condition"].dropna().unique())
    )

    selected_sample_types = st.sidebar.multiselect(
        "Sample type",
        sorted(df["sample_type"].dropna().unique()),
        default=sorted(df["sample_type"].dropna().unique())
    )

    selected_treatments = st.sidebar.multiselect(
        "Treatment",
        sorted(df["treatment"].dropna().unique()),
        default=sorted(df["treatment"].dropna().unique())
    )

    selected_populations = st.sidebar.multiselect(
        "Immune-cell population",
        population_order,
        default=population_order
    )

    filtered_df = df[
        df["condition"].isin(selected_conditions) &
        df["sample_type"].isin(selected_sample_types) &
        df["treatment"].isin(selected_treatments) &
        df["population"].isin(selected_populations)
    ].copy()

    st.subheader("Filtered Initial Analysis Table")

    col3, col4, col5 = st.columns(3)

    col3.metric("Filtered rows", len(filtered_df))
    col4.metric("Filtered samples", filtered_df["sample"].nunique())
    col5.metric("Filtered subjects", filtered_df["subject_id"].nunique())

    st.dataframe(filtered_df, width=True)

    st.download_button(
        label="Download filtered initial analysis table",
        data=filtered_df.to_csv(index=False),
        file_name="filtered_initial_analysis.csv",
        mime="text/csv"
    )

    st.subheader("Immune-Cell Population Percentages")

    if filtered_df.empty:
        st.warning("No rows match the selected filters.")
        return

    fig_box = px.box(
        filtered_df,
        x="population",
        y="percentage",
        points="all",
        category_orders={"population": population_order},
        title="Distribution of Immune-Cell Percentages by Population"
    )

    st.plotly_chart(fig_box, config=PLOTLY_CONFIG)

    mean_percentage_df = (
        filtered_df
        .groupby("population", as_index=False)
        .agg(mean_percentage=("percentage", "mean"))
    )

    fig_bar = px.bar(
        mean_percentage_df,
        x="population",
        y="mean_percentage",
        category_orders={"population": population_order},
        title="Average Percentage by Immune-Cell Population"
    )

    st.plotly_chart(fig_bar, config=PLOTLY_CONFIG)

    st.header("Part 3: Responder vs Non-Responder Analysis")

    st.write(
        "This section compares immune-cell population percentages between "
        "responders and non-responders for melanoma PBMC samples treated with miraclib."
    )

    part3_df = df[
        (df["condition"].astype(str).str.lower() == "melanoma") &
        (df["sample_type"].astype(str).str.lower() == "pbmc") &
        (df["treatment"].astype(str).str.lower() == "miraclib") &
        (df["response"].astype(str).str.lower().isin(["yes", "no"]))
    ].copy()

    st.subheader("Part 3 Filtered Dataset")

    col6, col7, col8 = st.columns(3)

    col6.metric("Rows", len(part3_df))
    col7.metric("Unique samples", part3_df["sample"].nunique())
    col8.metric("Unique subjects", part3_df["subject_id"].nunique())

    st.dataframe(part3_df)

    st.download_button(
        label="Download Part 3 filtered data",
        data=part3_df.to_csv(index=False),
        file_name="part3_responder_analysis_data.csv",
        mime="text/csv"
    )

    if part3_df.empty:
        st.warning("No data found for the Part 3 responder analysis filters.")
    else:
        st.subheader("Responder vs Non-Responder Boxplot")

        fig_part3_box = px.box(
            part3_df,
            x="population",
            y="percentage",
            color="response",
            points="all",
            category_orders={"population": population_order},
            title="Immune-Cell Percentages: Responders vs Non-Responders"
        )

        st.plotly_chart(
            fig_part3_box,
            config=PLOTLY_CONFIG
        )

        st.subheader("Responder vs Non-Responder Statistical Summary")

        part3_stats_df = calculate_responder_statistics(part3_df)

        st.dataframe(part3_stats_df)

        st.download_button(
            label="Download Part 3 statistical summary",
            data=part3_stats_df.to_csv(index=False),
            file_name="part3_responder_statistics.csv",
            mime="text/csv"
        )

        usable_stats = part3_stats_df.dropna(subset=["p_value"])

        if not usable_stats.empty:
            strongest_row = usable_stats.sort_values("p_value").iloc[0]

            strongest_population = strongest_row["population"]
            strongest_p_value = strongest_row["p_value"]
            difference = strongest_row["difference_in_means"]

            if difference > 0:
                direction = "higher in responders"
            elif difference < 0:
                direction = "lower in responders"
            else:
                direction = "approximately the same between responders and non-responders"

            st.subheader("Part 3 Interpretation")

            st.write(
                f"The strongest response-associated signal was **{strongest_population}**, "
                f"with an unadjusted Mann-Whitney U p-value of **{strongest_p_value:.3f}**. "
                f"The mean percentage was **{direction}**."
            )

            st.write(
                "The p-values are unadjusted. Since multiple immune-cell populations were tested, "
                "the results should be interpreted cautiously."
            )
            
    
    st.header("Part 4: Bob's Data Subset Analysis")

    st.write(
        "This section identifies baseline melanoma PBMC samples from patients "
        "treated with miraclib, then summarizes the subset by project, response, "
        "sex, and B-cell count."
    )

    bob_subset = df[
        (clean_text(df["condition"]) == "melanoma") &
        (clean_text(df["sample_type"]) == "pbmc") &
        (df["time_from_treatment_start"] == 0) &
        (clean_text(df["treatment"]) == "miraclib")
    ].copy()

    bob_samples = bob_subset[
        [
            "sample",
            "subject_id",
            "project",
            "condition",
            "sex",
            "sample_type",
            "treatment",
            "response",
            "time_from_treatment_start",
        ]
    ].drop_duplicates()

    st.subheader("Baseline Melanoma PBMC Samples Treated with Miraclib")

    col9, col10, col11 = st.columns(3)

    col9.metric("Samples", bob_samples["sample"].nunique())
    col10.metric("Subjects", bob_samples["subject_id"].nunique())
    col11.metric("Projects", bob_samples["project"].nunique())

    st.dataframe(bob_samples)

    st.download_button(
        label="Download Part 4 subset samples",
        data=bob_samples.to_csv(index=False),
        file_name="part4_bob_subset_samples.csv",
        mime="text/csv"
    )

    if bob_samples.empty:
        st.warning("No samples matched Bob's Part 4 subset filters.")
    else:
        st.subheader("How Many Samples From Each Project?")

        samples_by_project = (
            bob_samples
            .groupby("project", as_index=False)
            .agg(number_of_samples=("sample", "nunique"))
            .sort_values("project")
        )

        st.dataframe(samples_by_project)

        fig_project = px.bar(
            samples_by_project,
            x="project",
            y="number_of_samples",
            title="Number of Samples by Project"
        )

        st.plotly_chart(
            fig_project,
            config=PLOTLY_CONFIG
        )

        st.subheader("How Many Subjects Were Responders / Non-Responders?")

        subject_level_df = bob_samples[
            ["subject_id", "response", "sex"]
        ].drop_duplicates()

        subjects_by_response = (
            subject_level_df
            .groupby("response", as_index=False)
            .agg(number_of_subjects=("subject_id", "nunique"))
            .sort_values("response")
        )

        st.dataframe(subjects_by_response)

        fig_response = px.bar(
            subjects_by_response,
            x="response",
            y="number_of_subjects",
            title="Number of Subjects by Response"
        )

        st.plotly_chart(
            fig_response,
            config=PLOTLY_CONFIG
        )

        st.subheader("How Many Subjects Were Males / Females?")

        subjects_by_sex = (
            subject_level_df
            .groupby("sex", as_index=False)
            .agg(number_of_subjects=("subject_id", "nunique"))
            .sort_values("sex")
        )

        st.dataframe(subjects_by_sex)

        fig_sex = px.bar(
            subjects_by_sex,
            x="sex",
            y="number_of_subjects",
            title="Number of Subjects by Sex"
        )

        st.plotly_chart(
            fig_sex,
            config=PLOTLY_CONFIG
        )

        st.subheader("Average B Cells for Melanoma Male Responders at Time = 0")

        b_cell_male_responders = bob_subset[
            (clean_text(bob_subset["population"]) == "b_cell") &
            (clean_text(bob_subset["response"]) == "yes") &
            (clean_text(bob_subset["sex"]).isin(["male", "m"]))
        ].copy()

        average_b_cells = b_cell_male_responders["count"].mean()

        if pd.isna(average_b_cells):
            st.warning(
                "No B-cell records found for melanoma male responders at time = 0."
            )
        else:
            st.metric(
                "Average B-cell count",
                f"{average_b_cells:.2f}"
            )

            st.write(
                f"Considering melanoma male responders at time = 0, "
                f"the average number of B cells is **{average_b_cells:.2f}**."
            )

        st.write("B-cell records used for this calculation:")

        st.dataframe(
            b_cell_male_responders[
                [
                    "sample",
                    "subject_id",
                    "project",
                    "sex",
                    "response",
                    "sample_type",
                    "treatment",
                    "time_from_treatment_start",
                    "population",
                    "count",
                ]
            ],
        )




if __name__ == "__main__":
    main()