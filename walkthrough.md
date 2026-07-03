# Walkthrough - Revenue Forecasting Dashboard

We have successfully created and launched a Streamlit forecasting application.

## Changes Made

1. **Pre-processing Script (`aggregate_data.py`)**:
   - Aggregated the large 2.4 GB `WEB_CHALLAN_DETAILS_filtered.csv` dataset to a small daily summary (`daily_data.csv`), bringing down load times to less than a second.

2. **Streamlit App (`app.py`)**:
   - Loaded the daily dataset and engineered date-based features, lag variables, and rolling statistical metrics.
   - Built interactive widgets in the sidebar to configure data ranges, model hyperparameters (XGBoost & Ridge), and prediction weights.
   - Integrated dynamic metric cards for real-time Cross-Validation RMSE feedback.
   - Displayed actual vs. predicted revenue using Plotly charts with interactive month-end hover cards.

## Visual Verification

Here is the screenshot of the dashboard running locally:

![Forecasting Dashboard](/C:/Users/Admin/.gemini/antigravity-ide/brain/7bca2828-683b-45c8-9365-883ff2bdcccd/dashboard_loaded_1782971321175.png)

## How to Run locally

To launch the Streamlit app again:
```bash
C:\Users\Admin\anaconda3\python.exe -m streamlit run app.py
```
