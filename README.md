# Marvel Cinematic Universe Box-Office Analytics

## Project overview

This college-level Data Analytics project analyzes the exact Kaggle dataset **Marvel Cinematic Universe Box Office CSV** and presents the results through a single-file Streamlit dashboard. The application cleans the source data, reports data quality, engineers business-style metrics, performs exploratory and statistical analysis, and provides interactive filters and Plotly visualizations.

## Problem statement

MCU titles span multiple phases and differ in critical reception, audience reception, runtime, budget, and box-office performance. The project examines these relationships while explicitly accounting for missing financial values and source records that may represent future or non-theatrical titles.

## Objectives

- Acquire and validate the approved Kaggle dataset.
- Correct source data types and identify missing and duplicate records.
- Preserve missing financial values rather than treating them as zero.
- Compare ratings, budgets, opening weekends, and box-office performance.
- Examine trends by release year and MCU phase.
- Detect potential numerical outliers using the IQR rule.
- Deliver an interactive, reproducible Streamlit dashboard.

## Dataset

- **Name:** Marvel Cinematic Universe Box Office CSV
- **Kaggle page:** https://www.kaggle.com/datasets/parthfr/marvel-cinematic-universe-boxoffice-csv
- **Download endpoint:** https://www.kaggle.com/api/v1/datasets/download/parthfr/marvel-cinematic-universe-boxoffice-csv
- **File:** `mcu.csv`
- **Observed size:** 62 rows and 10 columns
- **Fields:** `movie_title`, `mcu_phase`, `release_date`, `tomato_meter`, `audience_score`, `movie_duration`, `production_budget`, `opening_weekend`, `domestic_box_office`, and `worldwide_box_office`

The source contains 62 unique title records, six MCU phases, and complete critic and audience scores. Runtime and financial fields contain `NA` values for 24 records each. The source date range is 2008-05-02 through 2026-09-01; dates in the future relative to execution should be interpreted as source-scheduled records, not confirmed completed releases.

## Technologies used

- Python
- Streamlit
- pandas
- NumPy
- Plotly Express

## Project structure

```text
app.py                 # Complete pipeline and Streamlit dashboard
requirements.txt       # Runtime dependencies
README.md              # Project documentation
Project_Report.docx    # College project report
```

All Python source code is intentionally contained in `app.py`.

## Data analytics methodology

1. Load `mcu.csv` from the exact Kaggle API endpoint or accept the approved CSV through the sidebar uploader.
2. Validate the expected ten-column schema.
3. Inspect dimensions, types, non-null counts, missing values, unique values, and duplicates.
4. Normalize common text missing markers such as `NA`.
5. Convert scores and financial fields to numeric values and parse `release_date` as a date.
6. Remove exact duplicate rows while preserving the original title-level observations.
7. Engineer release year, profit, ROI, opening-to-worldwide percentage, and critic/audience score gap.
8. Use complete available observations for each metric; missing budgets and revenues remain missing.
9. Summarize distributions, rankings, MCU phases, correlations, and IQR outliers.
10. Display all results dynamically in the dashboard.

## Data cleaning and preprocessing

- Schema validation prevents unrelated datasets from being analyzed.
- `"NA"`, `"N/A"`, `"null"`, `"None"`, and empty strings are converted to missing values.
- Currency-like punctuation is removed before numeric conversion.
- Invalid numeric or date values become missing and are not silently fabricated.
- Exact duplicates are removed from the cleaned analytical frame.
- Missing financial values are not median-imputed because doing so would invent commercial results.
- Derived metrics remain missing when their required source fields are unavailable.

## Exploratory data analysis

The dashboard includes:

- Top-title rankings for worldwide box office, domestic box office, opening weekend, production budget, and calculated profit.
- MCU phase-level worldwide totals and average ROI.
- Budget versus worldwide gross scatter plot.
- Critic-score versus audience-score scatter plot.
- Correlation heatmap for available numeric variables.
- IQR outlier summary for numeric columns.
- Raw schema and missing-value tables.

## KPI description

- **Movies:** number of records in the active phase filter.
- **Worldwide gross:** sum of available worldwide box-office values.
- **Average ROI:** mean of `(worldwide box office - production budget) / production budget × 100` for available values.
- **Average Tomato Meter:** mean critic score.
- **Median runtime:** median available runtime.

KPI values recalculate when the MCU phase filter changes.

## Dashboard features

- Exact Kaggle loading with a controlled uploader fallback.
- MCU phase filter.
- Five dashboard tabs: Overview, Data quality, Box office EDA, Ratings & relationships, and Insights & export.
- Interactive Plotly charts.
- Dynamically generated insights.
- Download button for the cleaned and engineered dataset.

## Installation and execution

```bash
pip install -r requirements.txt
streamlit run app.py
```

If the Kaggle endpoint is unavailable, download the approved `mcu.csv` from the dataset page and upload it in the sidebar.

## Key findings from the supplied CSV

These observations were calculated from the exact downloaded source, not hard-coded into the dashboard:

- The dataset contains **62 records**, **10 source columns**, and **0 exact duplicate rows**.
- Critic scores range from **46 to 99**, while audience scores range from **32 to 98**.
- The mean critic score is **82.63** and the mean audience score is **81.21**.
- There are **38 available worldwide box-office values**; the remaining 24 are missing.
- The highest available worldwide box office is **Avengers Endgame: $2,799,439,100**.
- The highest critic score is **99 for X-Men '97**.
- The average audience-minus-critic score gap is approximately **-1.42 points**.
- Financial comparisons across later phases must be interpreted with caution because financial fields are incomplete.

## Limitations

- The dataset is small and observational.
- Financial data are unavailable for 24 records in several fields.
- Source dates include future or scheduled titles.
- Box-office values are strongly skewed by blockbuster titles.
- Correlation does not demonstrate causation.
- The dataset does not provide marketing spend, distribution terms, streaming viewership, or inflation-adjusted revenue.

## Future scope

- Add an explicit release-status view based on execution date.
- Add inflation-adjusted revenue comparisons.
- Add external metadata such as theatrical versus streaming classification.
- Add confidence intervals and non-parametric tests where sample sizes support them.
- Add automated dataset freshness checks and a reproducible data-version log.

## Conclusion

The project provides a transparent, interactive view of MCU ratings and commercial performance while preserving the limitations of the source data. Its single-file architecture makes the full analytics pipeline easy to inspect and explain during a college viva.
