import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def get_recommendations(summary:dict) -> str:
    prompt = f"""You are a business analyst. Based on this data:
    -Total revenue: {summary.get('total_revenue')}
    -Best selling product: {list(summary.get('best_sellers', {}).keys())[0] if summary.get('best_sellers') else 'N/A'}
    Average Order Value: {summary.get('avg_order_value')}

    Give 3 specific, actionable business recommendations. Please"""

    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    return response.text