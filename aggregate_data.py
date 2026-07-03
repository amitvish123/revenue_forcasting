import pandas as pd
import os

def main():
    csv_path = "WEB_CHALLAN_DETAILS_filtered.csv"
    output_path = "daily_data.csv"
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return
        
    print(f"Reading and aggregating {csv_path}...")
    
    # Load only necessary columns to optimize memory usage
    df = pd.read_csv(csv_path, usecols=["CREATEDDATE", "TOTALAMOUNT"])
    
    # Drop rows with missing values or zero amounts
    df = df[df["TOTALAMOUNT"].notna() & (df["TOTALAMOUNT"] != 0)]
    
    # Convert dates and aggregate daily
    df["CREATEDDATE"] = pd.to_datetime(df["CREATEDDATE"])
    daily_df = df.groupby(pd.Grouper(key="CREATEDDATE", freq="D"))["TOTALAMOUNT"].sum().reset_index()
    
    # Filter daily records
    daily_df = daily_df[daily_df["TOTALAMOUNT"].notna() & (daily_df["TOTALAMOUNT"] != 0)]
    
    # Save the small aggregated file
    daily_df.to_csv(output_path, index=False)
    print(f"Aggregation complete. Saved daily summary to {output_path} ({len(daily_df)} rows).")

if __name__ == "__main__":
    main()
