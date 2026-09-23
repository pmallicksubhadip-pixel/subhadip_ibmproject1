"""Marvel Cinematic Universe box-office analytics dashboard."""
from __future__ import annotations

import io
import zipfile
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

KAGGLE_SOURCE = "https://www.kaggle.com/api/v1/datasets/download/parthfr/marvel-cinematic-universe-boxoffice-csv"
DATASET_PAGE = "https://www.kaggle.com/datasets/parthfr/marvel-cinematic-universe-boxoffice-csv"
EXPECTED_COLUMNS = [
    "movie_title", "mcu_phase", "release_date", "tomato_meter", "audience_score",
    "movie_duration", "production_budget", "opening_weekend", "domestic_box_office",
    "worldwide_box_office",
]


@st.cache_data(show_spinner=False)
def load_kaggle_dataset() -> pd.DataFrame:
    request = Request(KAGGLE_SOURCE, headers={"User-Agent": "mcu-analytics-streamlit"})
    with urlopen(request, timeout=20) as response:
        payload = response.read()
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        if "mcu.csv" not in archive.namelist():
            raise ValueError("Kaggle download did not contain the approved file mcu.csv.")
        with archive.open("mcu.csv") as handle:
            return pd.read_csv(handle)


def load_uploaded(uploaded_file) -> pd.DataFrame:
    try:
        return pd.read_csv(uploaded_file)
    except Exception as exc:
        raise ValueError(f"Could not read the uploaded CSV: {exc}") from exc


def validate_schema(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result.columns = [str(c).strip().lower() for c in result.columns]
    missing = [column for column in EXPECTED_COLUMNS if column not in result.columns]
    if missing:
        raise ValueError("The file is not the approved MCU schema. Missing columns: " + ", ".join(missing))
    return result[EXPECTED_COLUMNS]


def inspect_data(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "column": df.columns, "dtype": df.dtypes.astype(str).values,
        "non_null": df.notna().sum().values, "missing": df.isna().sum().values,
        "unique": df.nunique(dropna=True).values,
    })


def missing_summary(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({"missing_count": df.isna().sum(),
                         "missing_pct": (df.isna().mean() * 100).round(2)}).sort_values(
                             "missing_count", ascending=False)


def normalize_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Convert common textual missing markers to pandas missing values."""
    result = df.copy()
    return result.replace({"NA": np.nan, "N/A": np.nan, "null": np.nan, "None": np.nan, "": np.nan})


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    result = normalize_missing_values(validate_schema(df)).drop_duplicates().reset_index(drop=True)
    numeric = [c for c in EXPECTED_COLUMNS if c not in ("movie_title", "mcu_phase", "release_date")]
    for column in numeric:
        result[column] = pd.to_numeric(
            result[column].astype(str).str.replace(r"[$,%]", "", regex=True).str.replace(",", ""),
            errors="coerce",
        )
    result["release_date"] = pd.to_datetime(result["release_date"], errors="coerce")
    result["release_year"] = result["release_date"].dt.year
    for column in ("movie_title", "mcu_phase"):
        result[column] = result[column].fillna("Unknown").astype(str)
    result["profit"] = result["worldwide_box_office"] - result["production_budget"]
    result["roi"] = np.where(
        result["production_budget"] > 0,
        result["profit"] / result["production_budget"] * 100,
        np.nan,
    )
    result["opening_to_worldwide_pct"] = np.where(
        result["worldwide_box_office"] > 0,
        result["opening_weekend"] / result["worldwide_box_office"] * 100,
        np.nan,
    )
    result["audience_tomato_gap"] = result["audience_score"] - result["tomato_meter"]
    return result


def iqr_outliers(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for column in df.select_dtypes(include=np.number).columns:
        q1, q3 = df[column].quantile([0.25, 0.75])
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        count = ((df[column] < lower) | (df[column] > upper)).sum()
        rows.append({"column": column, "lower_bound": lower, "upper_bound": upper,
                     "outlier_count": int(count), "outlier_pct": count / len(df) * 100})
    return pd.DataFrame(rows)


def show_empty_state(df: pd.DataFrame) -> bool:
    """Prevent charts and rankings from running on an empty filter result."""
    if df.empty:
        st.info("No records match the current filter.")
        return True
    return False


def main():
    st.set_page_config(page_title="MCU Box Office Analytics", page_icon="🎬", layout="wide")
    st.title("🎬 Marvel Cinematic Universe Box-Office Analytics")
    st.caption("Approved Kaggle dataset: parthfr/marvel-cinematic-universe-boxoffice-csv")
    with st.sidebar:
        uploaded = st.file_uploader("Upload approved mcu.csv", type=["csv"])
        st.markdown(f"[Kaggle dataset page]({DATASET_PAGE})")
    try:
        raw = load_uploaded(uploaded) if uploaded is not None else load_kaggle_dataset()
        clean = clean_data(raw)
    except Exception as exc:
        st.warning("Kaggle access is unavailable. Upload the approved mcu.csv file to continue.")
        st.error(str(exc))
        return
    with st.sidebar:
        phases = ["All"] + sorted(clean["mcu_phase"].unique().tolist())
        phase = st.selectbox("MCU phase", phases)
        filtered = clean if phase == "All" else clean[clean["mcu_phase"] == phase]
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Overview", "Data quality", "Box office EDA", "Ratings & relationships", "Insights & export"]
    )
    with tab1:
        cols = st.columns(5)
        cols[0].metric("Movies", f"{len(filtered):,}")
        cols[1].metric("Worldwide gross", f"${filtered.worldwide_box_office.sum():,.0f}")
        cols[2].metric("Average ROI", f"{filtered.roi.mean():.1f}%")
        cols[3].metric("Average tomato meter", f"{filtered.tomato_meter.mean():.1f}")
        cols[4].metric("Median runtime", f"{filtered.movie_duration.median():.0f} min")
        st.dataframe(filtered[EXPECTED_COLUMNS + ["profit", "roi"]].head(25), use_container_width=True)
    with tab2:
        st.subheader("Schema inspection")
        st.dataframe(inspect_data(raw), use_container_width=True)
        st.subheader("Missing values and duplicates")
        st.dataframe(missing_summary(normalize_missing_values(raw)), use_container_width=True)
        st.write(f"Duplicate rows detected: **{raw.duplicated().sum():,}**")
        st.subheader("IQR outlier report")
        st.dataframe(iqr_outliers(clean), use_container_width=True)
    with tab3:
        if show_empty_state(filtered):
            st.stop()
        metric = st.selectbox("Box-office measure", ["worldwide_box_office", "domestic_box_office",
                                                       "opening_weekend", "production_budget", "profit"])
        metric_labels = {
            "worldwide_box_office": "Worldwide box office (USD)",
            "domestic_box_office": "Domestic box office (USD)",
            "opening_weekend": "Opening weekend (USD)",
            "production_budget": "Production budget (USD)",
            "profit": "Estimated profit (USD)",
        }
        metric_data = filtered.dropna(subset=[metric])
        if metric_data.empty:
            st.info(f"{metric_labels[metric]} is unavailable for this filter.")
        else:
            st.plotly_chart(px.bar(metric_data.sort_values(metric, ascending=False).head(15),
                               x=metric, y="movie_title", orientation="h",
                               labels={metric: metric_labels[metric], "movie_title": "Movie title"},
                               title=f"Top MCU movies by {metric_labels[metric]}"),
                            use_container_width=True)
        phase_summary = filtered.groupby("mcu_phase", as_index=False).agg(
            movies=("movie_title", "count"), worldwide=("worldwide_box_office", "sum"),
            average_roi=("roi", "mean"))
        st.plotly_chart(px.bar(phase_summary, x="mcu_phase", y="worldwide",
                               labels={"mcu_phase": "MCU phase", "worldwide": "Worldwide box office (USD)"},
                               title="Worldwide box office by MCU phase"),
                        use_container_width=True)
        financial_scatter = filtered.dropna(
            subset=["production_budget", "worldwide_box_office", "opening_weekend"]
        )
        if financial_scatter.empty:
            st.info("Budget, opening-weekend, and worldwide box-office data are unavailable for this filter.")
        else:
            st.plotly_chart(
                px.scatter(
                    financial_scatter,
                    x="production_budget",
                    y="worldwide_box_office",
                    size="opening_weekend",
                    color="mcu_phase",
                    hover_name="movie_title",
                    labels={
                        "production_budget": "Production budget (USD)",
                        "worldwide_box_office": "Worldwide box office (USD)",
                        "opening_weekend": "Opening weekend (USD)",
                        "mcu_phase": "MCU phase",
                    },
                    title="Budget, opening weekend, and worldwide gross",
                ),
                use_container_width=True,
            )
        yearly = filtered.groupby("release_year", as_index=False).agg(
            movies=("movie_title", "count"))
        st.plotly_chart(px.line(yearly, x="release_year", y="movies", markers=True,
                                labels={"release_year": "Release year", "movies": "Number of titles"},
                                title="MCU releases by year"),
                        use_container_width=True)
    with tab4:
        if show_empty_state(filtered):
            st.stop()
        ratings_scatter = filtered.dropna(
            subset=["tomato_meter", "audience_score", "worldwide_box_office"]
        )
        if ratings_scatter.empty:
            st.info("Ratings and worldwide box-office data are unavailable for this filter.")
        else:
            st.plotly_chart(
                px.scatter(
                    ratings_scatter,
                    x="tomato_meter",
                    y="audience_score",
                    size="worldwide_box_office",
                    color="mcu_phase",
                    hover_name="movie_title",
                    labels={
                        "tomato_meter": "Tomato Meter score",
                        "audience_score": "Audience score",
                        "worldwide_box_office": "Worldwide box office (USD)",
                        "mcu_phase": "MCU phase",
                    },
                    title="Critic and audience ratings",
                ),
                use_container_width=True,
            )
        corr_cols = ["tomato_meter", "audience_score", "movie_duration", "production_budget",
                     "opening_weekend", "domestic_box_office", "worldwide_box_office", "roi"]
        corr = filtered[corr_cols].corr()
        if corr.dropna(how="all").dropna(axis=1, how="all").empty:
            st.info("Correlation analysis is unavailable for this filter.")
        else:
            st.plotly_chart(px.imshow(corr, text_auto=".2f", zmin=-1, zmax=1,
                                      color_continuous_scale="RdBu_r",
                                      title="MCU numeric correlations"),
                            use_container_width=True)
    with tab5:
        if show_empty_state(filtered):
            st.stop()
        highest_data = filtered.dropna(subset=["worldwide_box_office"])
        roi_data = filtered.dropna(subset=["roi"])
        if highest_data.empty:
            st.info("Worldwide box-office insight is unavailable for this filter.")
        else:
            highest = highest_data.loc[highest_data["worldwide_box_office"].idxmax()]
            st.write(f"• Highest worldwide gross in the current filter: **{highest.movie_title}** (${highest.worldwide_box_office:,.0f}).")
        if roi_data.empty:
            st.info("ROI insight is unavailable because budget or worldwide box-office values are missing.")
        else:
            best_roi = roi_data.loc[roi_data["roi"].idxmax()]
            st.write(f"• Highest estimated ROI: **{best_roi.movie_title}** ({best_roi.roi:.1f}%).")
        st.write(f"• Average critic/audience gap: **{filtered.audience_tomato_gap.mean():.1f} points**.")
        st.write("All values above are calculated dynamically from the approved dataset and active phase filter.")
        st.download_button("Download cleaned MCU analytics CSV", clean.to_csv(index=False).encode(),
                           "cleaned_mcu.csv", "text/csv")


if __name__ == "__main__":
    main()
