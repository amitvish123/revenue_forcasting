import streamlit as st
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold, cross_val_score
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
import plotly.graph_objects as go
import datetime

# Page configuration
st.set_page_config(
    page_title="Revenue Forecasting Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling for premium look
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6;
    }
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e6e9ef;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        text-align: center;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-label {
        font-size: 14px;
        color: #7f7f7f;
    }
</style>
""", unsafe_allow_html=True)

# App Title
st.title("Revenue Forecasting Dashboard 📈")
st.markdown("An interactive web interface for revenue visualization and forecasting based on the optimized models trained from **Untitled3.ipynb**.")

# Load aggregated data
@st.cache_data
def load_data():
    if not os.path.exists("daily_data.csv"):
        # Fallback aggregate if daily_data.csv isn't found
        import subprocess
        subprocess.run(["C:\\Users\\Admin\\anaconda3\\python.exe", "aggregate_data.py"])
    df = pd.read_csv("daily_data.csv")
    df["CREATEDDATE"] = pd.to_datetime(df["CREATEDDATE"])
    return df

import os
try:
    daily_df = load_data()
except Exception as e:
    st.error(f"Error loading daily_data.csv: {e}. Please ensure aggregate_data.py has run successfully.")
    st.stop()

# Sidebar controls
st.sidebar.header("📅 Data Configuration")
min_date = daily_df["CREATEDDATE"].min().to_pydatetime()
max_date = daily_df["CREATEDDATE"].max().to_pydatetime()

# Date range and Split Date Selection
train_start = st.sidebar.date_input("Train Start Date", value=datetime.date(2022, 3, 1), min_value=min_date, max_value=max_date)
split_date = st.sidebar.date_input("Train/Test Split Date", value=datetime.date(2025, 2, 1), min_value=train_start, max_value=max_date)

# XGBoost Hyperparameters Tuning
st.sidebar.header("⚙️ XGBoost Hyperparameters")
xgb_max_depth = st.sidebar.slider("Max Depth", 1, 10, 1)
xgb_lr = st.sidebar.slider("Learning Rate", 0.01, 0.3, 0.05, step=0.01)
xgb_n_estimators = st.sidebar.slider("N Estimators", 50, 500, 200, step=50)
xgb_subsample = st.sidebar.slider("Subsample", 0.5, 1.0, 0.7, step=0.1)
xgb_colsample = st.sidebar.slider("Colsample By Tree", 0.5, 1.0, 0.7, step=0.1)
xgb_alpha = st.sidebar.number_input("Reg Alpha", value=5.0)
xgb_lambda = st.sidebar.number_input("Reg Lambda", value=10.0)

# Ridge Hyperparameters Tuning
st.sidebar.header("⚙️ Ridge Hyperparameters")
ridge_alpha = st.sidebar.number_input("Ridge Alpha", value=10.0)

# Ensemble Tuning
st.sidebar.header("⚖️ Ensemble Configuration")
xgb_weight = st.sidebar.slider("XGBoost Prediction Weight", 0.0, 1.0, 0.5, step=0.05)
ridge_weight = 1.0 - xgb_weight

# Feature Engineering
def create_features_daily(df):
    df = df.copy()
    df["dayofweek"] = df["CREATEDDATE"].dt.dayofweek
    df["day"] = df["CREATEDDATE"].dt.day
    df["month"] = df["CREATEDDATE"].dt.month
    df["year"] = df["CREATEDDATE"].dt.year
    df["day_sin"] = np.sin(2 * np.pi * df["dayofweek"] / 7)
    df["day_cos"] = np.cos(2 * np.pi * df["dayofweek"] / 7)
    df["dayofyear"] = df["CREATEDDATE"].dt.dayofyear
    df["year_sin"] = np.sin(2 * np.pi * df["dayofyear"] / 365)
    df["year_cos"] = np.cos(2 * np.pi * df["dayofyear"] / 365)
    for l in [1, 2, 3, 7, 14, 30, 60, 90]:
        df[f"lag_{l}"] = df["TOTALAMOUNT"].shift(l)
    for w in [7, 14, 30, 60, 90]:
        df[f"rolling_mean_{w}"] = df["TOTALAMOUNT"].shift(1).rolling(w).mean()
    df["rolling_std_7"] = df["TOTALAMOUNT"].shift(1).rolling(7).std()
    df["rolling_std_30"] = df["TOTALAMOUNT"].shift(1).rolling(30).std()
    df["diff_1"] = df["TOTALAMOUNT"].diff(1)
    df["diff_7"] = df["TOTALAMOUNT"].diff(7)
    df["pct_change_1"] = df["TOTALAMOUNT"].pct_change(1)
    return df

# Prepare datasets
train_raw = daily_df.loc[(daily_df["CREATEDDATE"] >= pd.Timestamp(train_start)) & (daily_df["CREATEDDATE"] < pd.Timestamp(split_date))]
test_raw = daily_df.loc[daily_df["CREATEDDATE"] >= pd.Timestamp(split_date)]

train = create_features_daily(train_raw)
test = create_features_daily(test_raw)

FEATURES = [col for col in train.columns if col not in ["CREATEDDATE", "TOTALAMOUNT"]]
TARGET = 'TOTALAMOUNT'

X_train = train[FEATURES]
y_train = train[TARGET]
X_test = test[FEATURES]
y_test = test[TARGET]

y_train_log = np.log1p(y_train)

# Setup Models
xgb_model = xgb.XGBRegressor(
    objective="reg:squarederror",
    max_depth=xgb_max_depth,
    learning_rate=xgb_lr,
    n_estimators=xgb_n_estimators,
    subsample=xgb_subsample,
    colsample_bytree=xgb_colsample,
    reg_alpha=xgb_alpha,
    reg_lambda=xgb_lambda,
    min_child_weight=5,
    random_state=42
)

ridge_model = Pipeline([
    ("imputer", SimpleImputer(strategy="mean")),
    ("ridge", Ridge(alpha=ridge_alpha))
])

# Cross-validation metrics
kf = KFold(n_splits=5, shuffle=True, random_state=42)

try:
    xgb_cv = -cross_val_score(xgb_model, X_train, y_train_log, cv=kf, scoring="neg_root_mean_squared_error")
    ridge_cv = -cross_val_score(ridge_model, X_train, y_train_log, cv=kf, scoring="neg_root_mean_squared_error")
    
    xgb_cv_mean = xgb_cv.mean()
    ridge_cv_mean = ridge_cv.mean()
except Exception as e:
    xgb_cv_mean = np.nan
    ridge_cv_mean = np.nan
    st.warning("Could not calculate cross-validation scores due to insufficient data for the selected date range.")

# Train models
xgb_model.fit(X_train, y_train_log)
ridge_model.fit(X_train, y_train_log)

# Predictions
y_pred_xgb_log = xgb_model.predict(X_test)
y_pred_ridge_log = ridge_model.predict(X_test)

# Ensemble calculation
y_pred_ensemble_log = (xgb_weight * y_pred_xgb_log) + (ridge_weight * y_pred_ridge_log)
y_pred_ensemble = np.expm1(y_pred_ensemble_log)

# Predictions alignment
all_dates = pd.concat([train["CREATEDDATE"], test["CREATEDDATE"]], ignore_index=True)
test_dates = test["CREATEDDATE"].reset_index(drop=True)
train_dates = train["CREATEDDATE"].reset_index(drop=True)

y_test_aligned = y_test.reset_index(drop=True)
actual = np.concatenate([y_train, y_test_aligned])
predicted = np.concatenate([np.full(len(y_train), np.nan), y_pred_ensemble])

# Residuals and interval bounds
residuals = y_test_aligned - y_pred_ensemble
std = residuals.std()
upper = y_pred_ensemble + 2 * std
lower = y_pred_ensemble - 2 * std

# Plot dataframes
df_plot = pd.DataFrame({
    "date": all_dates,
    "actual": actual,
    "predicted": predicted,
})
monthly_df = df_plot.set_index("date").resample("ME").sum().reset_index()

test_plot = pd.DataFrame({
    "date": test_dates,
    "actual": y_test_aligned,
    "predicted": y_pred_ensemble
})
monthly_test = test_plot.set_index("date").resample("ME").sum().reset_index()

interval_df = pd.DataFrame({
    "date": test_dates.reset_index(drop=True),
    "upper": upper,
    "lower": lower
})
monthly_interval = interval_df.set_index("date").resample("ME").sum().reset_index()

# Metric summary cards in main page
m1, m2, m3 = st.columns(3)
with m1:
    st.markdown(f'<div class="metric-card"><div class="metric-label">XGBoost CV Mean RMSE</div><div class="metric-value">{xgb_cv_mean:.4f}</div></div>', unsafe_allow_html=True)
with m2:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Ridge CV Mean RMSE</div><div class="metric-value">{ridge_cv_mean:.4f}</div></div>', unsafe_allow_html=True)
with m3:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Ensemble Residual Std Dev</div><div class="metric-value">{std:,.0f}</div></div>', unsafe_allow_html=True)

st.write("")

# Tabs configuration
tab1, tab2, tab3 = st.tabs(["📊 Interactive Forecast Chart", "📉 Model Comparison Details", "📋 Prediction Table"])

with tab1:
    st.subheader("Monthly Actual vs Predicted Forecast")
    
    fig = go.Figure()
    
    # Actuals
    fig.add_trace(go.Scatter(
        x=monthly_df["date"],
        y=monthly_df["actual"],
        mode='lines+markers',
        name='Actual (Monthly)',
        line=dict(color='#1f77b4', width=2),
        marker=dict(size=6)
    ))
    
    # Predictions
    fig.add_trace(go.Scatter(
        x=monthly_test["date"],
        y=monthly_test["predicted"],
        mode='lines+markers',
        name='Predicted (Monthly)',
        line=dict(color='#ff7f0e', dash='dash', width=2),
        marker=dict(symbol='square', size=6)
    ))
    
    # Prediction Range
    fig.add_trace(go.Scatter(
        x=monthly_interval["date"],
        y=monthly_interval["upper"],
        mode='lines',
        line=dict(color='rgba(44, 160, 44, 0.3)', width=1),
        showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=monthly_interval["date"],
        y=monthly_interval["lower"],
        mode='lines',
        fill='tonexty',
        fillcolor='rgba(44, 160, 44, 0.1)',
        line=dict(color='rgba(44, 160, 44, 0.3)', width=1),
        name='Prediction Range (±2 Std)'
    ))
    
    # Train/Test Split Vertical line
    fig.add_vline(
        x=train_dates.iloc[-1].timestamp() * 1000,
        line_width=2,
        line_dash="dot",
        line_color="black"
    )
    
    fig.update_layout(
        xaxis_title="Year",
        yaxis_title="Total Amount (Monthly Aggregated)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        margin=dict(l=40, r=40, t=40, b=40),
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Model Performance Details")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**XGBoost Model Fold Details**")
        if not np.isnan(xgb_cv_mean):
            st.dataframe(pd.DataFrame({
                "Fold": [f"Fold {i+1}" for i in range(5)],
                "RMSE": xgb_cv
            }))
        else:
            st.info("No fold metrics calculated.")
            
    with col2:
        st.markdown("**Ridge Model Fold Details**")
        if not np.isnan(ridge_cv_mean):
            st.dataframe(pd.DataFrame({
                "Fold": [f"Fold {i+1}" for i in range(5)],
                "RMSE": ridge_cv
            }))
        else:
            st.info("No fold metrics calculated.")

with tab3:
    st.subheader("Monthly Prediction Output Table")
    output_df = monthly_test.copy()
    output_df["Actual Amount"] = output_df["actual"].map('{:,.2f}'.format)
    output_df["Predicted Amount"] = output_df["predicted"].map('{:,.2f}'.format)
    output_df["Difference"] = (output_df["actual"] - output_df["predicted"]).map('{:,.2f}'.format)
    output_df = output_df[["date", "Actual Amount", "Predicted Amount", "Difference"]].rename(columns={"date": "Month-End Date"})
    st.dataframe(output_df, use_container_width=True)
