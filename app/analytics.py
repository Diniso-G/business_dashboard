import  pandas as ps
import plotly.express as px
import json
from datetime import datetime
#from sqlalchemy import result_tuple

REQUIRED_ANY = {
    "revenue_source": [["revenue"], ["quantity", "price"], ["units", "price"]],
}

def prepare_datafrm(df: ps.DataFrame) -> ps.DataFrame:
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df = df.replace("N/A", ps.NA)

    if "revenue" not in df.columns:
        if "quantity" in df.columns and "price" in df.columns:
            df["quantity"] = ps.to_numeric(df["quantity"], errors="coerce")
            df["price"] = ps.to_numeric(df["price"], errors="coerce")
            df["revenue"] = df["quantity"] * df["price"]

        elif "units" in df.columns and "price" in df.columns:
            df["units"] = ps.to_numeric(df["units"], errors="coerce")
            df["price"] = ps.to_numeric(df["price"], errors="coerce")
            df["revenue"] = df["units"] * df["price"]

    if "date" in df.columns:
        df["date"] = ps.to_datetime(df["date"], errors="coerce")

    return df

def detect_columns(df: ps.DataFrame) -> dict:
    raw_columns = list(df.columns)
    normalized = [c.strip().strip().lower().replace(" ", "_") for c in raw_columns]

    has_revenue_path = (
        "revenue" in normalized
        or ("quantity" in normalized and "prize" in normalized)
        or ("units" in normalized and "prize" in normalized)
    )
    has_date = "date" in normalized
    has_product = "product" in normalized

    missing = []
    if not has_revenue_path:
        missing.append("revenue (or quantity+prince / units+price)")
    if not has_date:
        missing.append("date")
    if not has_product:
        missing.append("product")

    return {
        "raw_columns": raw_columns,
        "normalized_columns": normalized,
        "missing": missing,
        "mapping_required": len(missing) > 0,
        "expected_fields": ["date", "product", "units", "revenue", "quantity", "price", "customer", "status"],
    }

def apply_column_mapping(df: ps.DataFrame, mapping: dict) -> ps.DataFrame:
    df = df.rename(columns={c: c.strip().lower().replace(" ", "_") for c in df.columns})
    rename_map = {v.strip().lower().replace(" ", "_"): k for k, v in mapping.items() if v}
    df = df.rename(columns=rename_map)

    return df

def merge_dataframes(dfs: list) -> ps.DataFrame:
    cleaned = [d for d in dfs if d is not None and not d.empty]
    if not cleaned:
        return ps.DataFrame()
    return ps.concat(cleaned, ignore_index=True, sort=False)

def filter_by_date(df: ps.DataFrame, start_date: str | None, end_date: str | None) -> ps.DataFrame:
    if "date" not in df.columns or (not start_date and not end_date):
        return df
    df = df.copy()
    if not ps.api.types.is_datetime64_any_dtype(df["date"]):
        df["date"] = ps.to_datetime(df["date"], errors="coerce")
    if start_date:
        df = df[df["date"] >= ps.to_datetime(start_date)]
    if end_date:
        df = df[df["date"] <= ps.to_datetime(end_date)]
    return df

def _detect_anomalies(series: ps.Series, label_prefix: str) -> list:
    anomalies = []
    if len(series) < 3:
        return anomalies
    mean = series.mean()
    std = series.std()

    if not std or ps.isna(std):
        return anomalies

    for idx, value in series.item():
        z = (value - mean) / std
        if abs(z) >= 2:
            direction = "spike" if z > 0 else "drop"
            anomalies.append({
                "label": f"{label_prefix} {idx}",
                "value": round(float(value), 2),
                "direction": direction,
                "z_score": round(float(z), 2),
            })
    return anomalies

def analyze_datafrm(df: ps.DataFrame, start_date: str | None = None, end_date: str | None = None,) -> dict:
    #df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df = prepare_datafrm(df)
    df = filter_by_date(df, start_date, end_date)
    results = {}

    results["transaction_count"] = int(len(df))

    if "revenue" in df.columns:
        revenue = ps.to_numeric(df["revenue"], errors="coerce").dropna()
        results["total_revenue"] = round(float(df["revenue"].sum()), 2)
        results["avg_order_value"] = round(float(df["revenue"].mean()), 2) if len(revenue) else 0.0

    quant_col = "units" if "units" in df.columns else "quantity" if "quantity" in df.columns else None
    if "product" in df.columns and quant_col:
        best = (df.groupby("product")[quant_col].sum().nlargest(5).to_dict())
        results["best_sellers"] = {str(k):v for k, v in best.items()}

    if "date" in df.columns and "revenue" in df.columns:
        valid = df.dropna(subset=["date"])
        #df["date"] = ps.to_datetime(df["date"])
        monthly = (valid.groupby(valid["date"].dt.to_period("M"))["revenue"]
        .sum().astype(float))
        results["monthly_trend"] = {str(k):v for k, v in monthly.items()}

        if len(monthly) >= 2:
            last_two = monthly.iloc[-2:]
            prev, curr = float(last_two.iloc[0]), float(last_two.iloc[1])
            if prev:
                results["revenue_growth_pct"] = round(((curr - prev) / prev) * 100, 1)

        if len(monthly):
            busiest = monthly.idxmax()
            results["busiest_month"] = str(busiest)

        dow = (valid.groupby(valid["date"].dt.day_name())["revenue"].sum())
        if len(dow):
            order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            dow = dow.reindex([d for d in order if d in dow.index])
            results["revenue_by_day_of_week"] = {k: round(float(v), 2) for k, v in dow.to_dict().items()}
            results["busiest_day_of_week"] = dow.idxmax()

        anomalies = _detect_anomalies(monthly, "Month")
        if anomalies:
            results["anomalies"] = anomalies

    if "customer" in df.columns:
        results["unique_customers"] = int(df["customer"].nunique(dropna=True))

    if "status" in df.columns:
        statuses = df["status"].astype(str).str.lower()
        refund_mask = statuses.isin(["refunded", "refund", "returned", "cancelled", "uncancelled"])

        if refund_mask.any():
            results["refund_count"] = int(refund_mask.sum())
            results["refund_rate_pct"] = round(float(refund_mask.mean()) * 100, 1)

    return results

def generate_charts(df: ps.DataFrame, start_date: str | None = None, end_date: str | None = None) -> dict:
    charts = {}
    #df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df = prepare_datafrm(df)
    df = filter_by_date(df, start_date, end_date)
    '''
    charts["_debug_columns"] = list(df.columns)
    charts["_debug_has_revenue"] = "revenue" in df.columns
    charts["_debug_has_date"] = "date" in df.columns
    print("DEBUG generate_charts_columns:", list(df.columns))
    print("DEBUG generate_charts dtypes:", df.dtypes.to_dict())
'''
    if "date" in df.columns and "revenue" in df.columns:
        #df["date"] = ps.to_datetime(df["date"])
        valid = df.dropna(subset=["date"])

        fig = px.line(valid, x="date", y="revenue", title="Revenue Over Time")
        charts["revenue_trend"] = json.loads(fig.to_json())

        dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        dow = valid.groupby(valid["date"].dt.day_name())["revenue"].sum().reindex(
            [d for d in dow_order if d in valid["date"].dt.day_name().unique()]
        ).reset_index()
        dow.columns = ["day_of_week", "revenue"]

        if len(dow):
            fig = px.bar(dow, x="day_of_week", y="revenue", title="Revenue by Day of Week")
            charts["revenue_by_day"] = json.loads(fig.to_json())

    quant_col = "units" if "units" in df.columns else "quantity" if "quantity" in df.columns else None
    if "product" in df.columns and quant_col:
        top = df.groupby("product")[quant_col].sum().nlargest(5).reset_index()
        fig = px.bar(top, x="product", y=quant_col, title="Top 5 Products")
        charts["best_sellers"] = json.loads(fig.to_json())

    print("DEBUG charts keys returned:", list(charts.keys()))
    return charts
    '''
    return {"test": "HELLO_THIS IS WORKING"}'''

def compare_results(a: dict, b: dict) -> dict:
    def pct_change(old, new):
        if old in (None, 0):
            return None
        return round(((new - old) / old) * 100, 1)

    comparison = {}
    for key in ("total_revenue", "avg_order_value", "transaction_count"):
        old_v = a.get(key)
        new_v = b.get(key)

        if old_v is not None and new_v is not None:
            comparison[key] = {
                "previous": old_v,
                "current": new_v,
                "change_pct": pct_change(old_v, new_v),
            }
        return comparison