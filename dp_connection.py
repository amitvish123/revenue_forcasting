import oracledb
import csv
import os

dsn = f"172.18.210.27:1521/IFMIS"
conn = oracledb.connect(
    user="system",
    password="system",
    dsn=dsn
)


print(f"database connected")
cursor = conn.cursor()
cursor.arraysize = 100000

tables = [
    ("PROD_IFMIS", "FD_RND_CMN_RCPT_TXN"),
    ("PROD_WEBPORTAL", "WEB_CHALLAN_DETAILS"),
    ("PROD_WEBPORTAL", "WEB_PURPOSE_DETAILS")
]

table_configs = [
    {
        "schema": "PROD_IFMIS",
        "table": "FD_RND_CMN_RCPT_TXN",
        "date_col": "TXN_DATE"
    },
    {
        "schema": "PROD_WEBPORTAL",
        "table": "WEB_CHALLAN_DETAILS",
        "date_col": "WCD_CREATED_DT"
    },
    {
        "schema": "PROD_WEBPORTAL",
        "table": "WEB_PURPOSE_DETAILS",
        "date_col": "WPD_CREATED_DT"
    }
]

# DATE_FILTER = """
# TO_DATE({date_col}, 'DD-MM-YYYY HH24:MI:SS')
# BETWEEN TO_DATE('01-01-2018 00:00:00','DD-MM-YYYY HH24:MI:SS')
#     AND TO_DATE('31-12-2026 23:59:59','DD-MM-YYYY HH24:MI:SS')
# """

DATE_FILTER = """
{date_col} BETWEEN
    DATE '2018-01-01'
AND DATE '2027-01-01'
"""

for owner, table_name in tables:
    print(f"\n{'='*80}")
    print(f"Schema: {owner}")
    print(f"Table : {table_name}")
    print(f"{'='*80}")

    cursor.execute("""
        SELECT
            column_id,
            column_name,
            data_type,
            data_length,
            data_precision,
            data_scale,
            nullable
        FROM all_tab_columns
        WHERE owner = :owner
          AND table_name = :table_name
        ORDER BY column_id
    """, owner=owner, table_name=table_name)

    for row in cursor:
        print(row)

# query1 = """
#         SELECT * FROM PROD_WEBPORTAL.WEB_CHALLAN_DETAILS where TO_NUMBER(WCD_USER_ID) = 25161920
#     """
# query1 = """
# SELECT data_type
# FROM all_tab_columns
# WHERE owner = 'PROD_WEBPORTAL'
# AND table_name = 'WEB_CHALLAN_DETAILS'
# AND column_name = 'WCD_USER_ID';
# """
# cursor.execute(query1)
# for row in cursor:
#     print(row)
  # important for speed

# cursor.execute("""
#         SELECT
#             COUNT(*)
#         FROM PROD_WEBPORTAL.WEB_CHALLAN_DETAILS
#         WHERE WCD_CREATED_DT BETWEEN
#         DATE '2024-01-01'
#         AND DATE '2025-01-01'
#     """)

# for row in cursor:
#     print(row)
# def export_table(schema, table):
#     filename = f"{table}.csv"
#     print(f"\nExporting {schema}.{table} -> {filename}")

#     query = f"SELECT * FROM {schema}.{table}"
#     cursor.execute(query)

#     with open(filename, "w", newline="", encoding="utf-8") as f:
#         writer = csv.writer(f)

#         # write header
#         writer.writerow([col[0] for col in cursor.description])

#         total = 0

#         while True:
#             rows = cursor.fetchmany(100000)

#             if not rows:
#                 break

#             writer.writerows(rows)
#             total += len(rows)

#             print(f"{table}: exported {total} rows")

#     print(f"DONE -> {filename}")
def export_table(schema, table):
    filename = f"{table}_filtered_1.csv"
    print(f"\nExporting {schema}.{table} -> {filename} ")

    query = """
        WITH revised_table AS (
            SELECT *
            FROM PROD_WEBPORTAL.WEB_CHALLAN_DETAILS where WCD_STATUS = 'Success' AND WCD_TXN_CIN_NO IS NOT NULL
        )
        SELECT
            WCD_CIN_NO AS CinNo,
            WCD_TXN_CIN_NO AS CinTxnNo,
            WCD_CREATED_DT AS CreatedDate,
            WCD_BANK_REF AS BankRef,
            CHALLAN_NO AS ChallanNo,
            WCD_TOTAL_AMOUNT AS TotalAmount ,
            WCD_TXN_CIN_NO AS ChallanNo,
            WCD_TAX_TYPE AS TaxType,
            WCD_MAJOR_HEAD AS MajorHead,
            WCD_LOCATION_CODE AS LocationCode,
            WCD_CIRCLE_ID AS CircleId,
            POST_CODE AS PostCode,
            BUDGETLINE_CODE AS BudgetLine,
            WCD_DEPT_CODE AS DeptCode,
            PAYMENT_TYPE AS PaymentType,
            WCD_BANK_CODE AS BankCode,
            RECONCILIATION_STATUS AS ReconciliationStatus,
            WCD_APPROVED_FLAG AS ApprovedFlag,
            WCD_DISCOUNT AS Discount,
            WCD_GROSS_AMOUNT AS GrossAmount
        FROM revised_table
        WHERE WCD_CREATED_DT >= DATE '2018-01-01'
            AND WCD_CREATED_DT < DATE '2026-01-01'
        ORDER BY WCD_CREATED_DT DESC
    """
    # query = """
    # SELECT count(*)
    # FROM PROD_WEBPORTAL.WEB_CHALLAN_DETAILS where WCD_STATUS = 'Success'
    # """
    cursor.execute(query)

    # for row in cursor:
    #     print(row)
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # write header
        writer.writerow([col[0] for col in cursor.description])

        total = 0

        while True:
            rows = cursor.fetchmany(100000)

            if not rows:
                break

            writer.writerows(rows)
            total += len(rows)

            print(f"{table}: exported {total} rows")

    print(f"DONE -> {filename} (TOTAL: {total})")

# # for schema, table in tables:
    
export_table("PROD_WEBPORTAL", "WEB_CHALLAN_DETAILS")
# def export_table(schema, table, date_col, max_rows=1_000_000):
#     filename = f"{table}.csv"
#     print(f"\nExporting {schema}.{table} -> {filename} (FILTERED 2018–2026)")

#     query = f"""
#         SELECT *
#         FROM {schema}.{table}
#         WHERE {DATE_FILTER.format(date_col=date_col)}
#     """

#     cursor.execute(query)


#     if os.path.exists(filename):
#         os.remove(filename)

#     with open(filename, "w", newline="", encoding="utf-8") as f:
#         writer = csv.writer(f)

#         writer.writerow([col[0] for col in cursor.description])

#         total = 0

#         while True:
#             rows = cursor.fetchmany(100000)
#             if not rows:
#                 break

#             remaining = max_rows - total
#             if remaining <= 0:
#                 break

#             if len(rows) > remaining:
#                 rows = rows[:remaining]

#             writer.writerows(rows)
#             total += len(rows)

#             print(f"{table}: exported {total} rows")

#             if total >= max_rows:
#                 break

#     print(f"DONE -> {filename} (TOTAL: {total})")

# for cfg in table_configs:
#     export_table(cfg["schema"], cfg["table"], cfg["date_col"])

cursor.close()
conn.close()

print("\nALL EXPORTS COMPLETED")

