import pandas as ps
from app.analytics import analyze_datafrm, generate_charts

df = ps.read_csv("../uploads/test_sales_data.csv")
results = analyze_datafrm(df.copy())
print("results:", results)
charts = generate_charts(df.copy())
print("chart keys", list(charts.keys()))
print("full charts", charts)