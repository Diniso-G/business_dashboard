import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = None

def get_client():
    global client
    if client is None:
        api_key =os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("Gemini_Api_key is not set")
        client = genai.Client(api_key=api_key)
    return client

def get_recommendations(summary:dict) -> str:
    prompt = f"""You are a business analyst. Based on this data:
    -Total revenue: {summary.get('total_revenue')}
    -Best selling product: {list(summary.get('best_sellers', {}).keys())[0] if summary.get('best_sellers') else 'N/A'}
    Average Order Value: {summary.get('avg_order_value')}

    Give 3 specific, actionable business recommendations. Please"""

    client = get_client()
    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    return response.text