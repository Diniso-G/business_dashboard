import  pandas as ps
from sqlalchemy import result_tuple


def analyze_datafrm(df: ps.DataFrame) -> dict:

    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    results = {}

    if "revenue" in df.columns:
        results["total_revenue"] = round(df["revenue"].sum(), 2)
        results["avg_order_value"] = round(df["revenue"].mean(), 2)

    if "product" in df.columns and "units" in df.columns:
        results["best_sellers"] = (df.groupby("product")["units"].sum().nlargest(5).to_dict())

    if "date" in df.columns and "revenue" in df.columns:
        df["date"] = ps.to_datetime(df["date"])
        results["monthly_trend"] = (df.groupby(df["date"].dt.to_period("M"))["revenue"]
        .sum().astype(float).to_dict())


    return results