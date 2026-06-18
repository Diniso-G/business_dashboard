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

import plotly.express as px
import json

def generate_charts(df: ps.DataFrame) -> dict:
    charts = {}
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    if "date" in df.columns and "revenue" in df.columns:
        df["date"] = ps.to_datetime(df["date"])
        fig = px.line(df, x="date", y="revenue", title="Revenue Over Time")
        charts["revenue_trend"] = json.loads(fig.to_json())

    if "product" in df.columns and "units" in df.columns:
        top = df.groupby("product")["units"].sum().nlargest(5).reset_index()
        fig = px.bar(top, x="product", y="units", title="Top 5 Products")
        charts["best_sellers"] = json.loads(fig.to_json())

    return charts