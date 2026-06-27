import  pandas as ps
import plotly.express as px
import json
#from sqlalchemy import result_tuple

def prepare_datafrm(df: ps.DataFrame) -> ps.DataFrame:
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df = df.replace("N/A", ps.NA)

    if "revenue" not in df.columns and "quantity" in df.columns and "price" in df.columns:
        df["quantity"] = ps.to_numeric(df["quantity"], errors="coerce")
        df["price"] = ps.to_numeric(df["price"], errors="coerce")
        df["revenue"] = df["quantity"] * df["price"]

    if "date" in df.columns:
        df["date"] = ps.to_datetime(df["date"], errors="coerce")

    return df

def analyze_datafrm(df: ps.DataFrame) -> dict:
    #df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df = prepare_datafrm(df)
    results = {}

    if "revenue" in df.columns:
        results["total_revenue"] = round(float(df["revenue"].sum()), 2)
        results["avg_order_value"] = round(float(df["revenue"].mean()), 2)

    quant_col = "units" if "units" in df.columns else "quantity" if "quantity" in df.columns else None
    if "product" in df.columns and quant_col:
        best = (df.groupby("product")[quant_col].sum().nlargest(5).to_dict())
        results["best_sellers"] = {str(k):v for k, v in best.items()}

    if "date" in df.columns and "revenue" in df.columns:
        #df["date"] = ps.to_datetime(df["date"])
        monthly = (df.groupby(df["date"].dt.to_period("M"))["revenue"]
        .sum().astype(float).to_dict())
        results["monthly_trend"] = {str(k):v for k, v in monthly.items()}

    return results


def generate_charts(df: ps.DataFrame) -> dict:
    charts = {}
    #df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df = prepare_datafrm(df)
    '''
    charts["_debug_columns"] = list(df.columns)
    charts["_debug_has_revenue"] = "revenue" in df.columns
    charts["_debug_has_date"] = "date" in df.columns
    print("DEBUG generate_charts_columns:", list(df.columns))
    print("DEBUG generate_charts dtypes:", df.dtypes.to_dict())
'''
    if "date" in df.columns and "revenue" in df.columns:
        #df["date"] = ps.to_datetime(df["date"])

        fig = px.line(df, x="date", y="revenue", title="Revenue Over Time")
        charts["revenue_trend"] = json.loads(fig.to_json())

    quant_col = "units" if "units" in df.columns else "quantity" if "quantity" in df.columns else None
    if "product" in df.columns and quant_col:
        top = df.groupby("product")[quant_col].sum().nlargest(5).reset_index()
        fig = px.bar(top, x="product", y=quant_col, title="Top 5 Products")
        charts["best_sellers"] = json.loads(fig.to_json())

    print("DEBUG charts keys returned:", list(charts.keys()))
    return charts
    '''
    return {"test": "HELLO_THIS IS WORKING"}'''