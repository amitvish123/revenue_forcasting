# Implementation Plan - Streamlit Application for Revenue Forecasting

Create a Streamlit application to visualize the actual vs. predicted revenue graphs from [Untitled3.ipynb](file:///c:/Users/Admin/revenue_forcasting/Untitled3.ipynb).

## User Review Required

> [!IMPORTANT]
> The original dataset `WEB_CHALLAN_DETAILS_filtered.csv` is **2.4 GB**, which is too large to load directly in a Streamlit app on every run.
> We propose to pre-aggregate this data into a small daily dataset (`daily_data.csv`) of less than 1 MB, ensuring the Streamlit app loads instantly.

> [!TIP]
> To make the app highly interactive and premium, we will:
> 1. Use **Plotly** for interactive zooming, panning, and hovering on the charts instead of static matplotlib images.
> 2. Allow interactive tuning of model hyperparameters (XGBoost max depth, learning rate, Ridge alpha, etc.) in the sidebar.
> 3. Display live model performance metrics (RMSE per fold, Mean RMSE).

## Proposed Changes

### Data Preprocessing Component

#### [NEW] [aggregate_data.py](file:///c:/Users/Admin/revenue_forcasting/aggregate_data.py)
A one-time script that aggregates the 2.4 GB CSV file into a daily summary `daily_data.csv` to ensure fast loading times for the Streamlit app.

### Streamlit Application Component

#### [NEW] [app.py](file:///c:/Users/Admin/revenue_forcasting/app.py)
The core Streamlit application which:
- Loads the pre-aggregated daily data.
- Provides sidebar inputs for hyperparameter tuning (XGBoost & Ridge) and Train/Test split date.
- Trains models on-the-fly and generates predictions.
- Displays an interactive actual vs. predicted plot using Plotly.
- Shows cross-validation RMSE performance metrics.

## Verification Plan

### Automated/Manual Verification
1. Run `python aggregate_data.py` to generate the aggregated dataset.
2. Run `streamlit run app.py` to start the application.
3. Open the application in the browser and verify:
   - Interactive Plotly chart with tooltips.
   - Metric cards showing Ridge, XGBoost, and Ensemble RMSE.
   - Adjusting sidebar controls updates the models and charts in real-time.
