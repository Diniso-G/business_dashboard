import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = None

SMALL_SAMPLE_THRESHOLD = 20

def get_client():
    global client
    if client is None:
        api_key =os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("Gemini_Api_key is not set")
        client = genai.Client(api_key=api_key)
    return client

def _sample_size_note(summary: dict) -> str:
    count = summary.get("transaction_count")
    if count is not None and count < SMALL_SAMPLE_THRESHOLD:
        return (f"\nNote: this dataset only has {count} transactions, which is a small sample - treat any recommendation based on it as a low-confidence early signal, not a firm conclusion.")

    return ""

def get_recommendations(summary:dict) -> str:
    try:
        best_sellers = summary.get("best_sellers", {})
        prompt = f"""You are a business analyst. Based on this data:
            -Total revenue: {summary.get('total_revenue')}
            -Transactions analyzed: {summary.get('transaction_count')}
            -Best selling product: {list(summary.get('best_sellers', {}).keys())[0] if summary.get('best_sellers') else 'N/A'}
            -Average Order Value: {summary.get('avg_order_value')}
            -Revenue growth vs prior period: {summary.get('revenue_growth_pct', 'N/A')}%
            -Busiest month: {summary.get('busiest_month', 'N/A')}
            -Busiest day of week: {summary.get('busiest_day_of_week', 'N/A')}
            -Refund rate: {summary.get('refund_rate_pct', 'N/A')}%
            -Notable anomalies: {summary.get('anomalies', 'none detected')}

            Give 3 specific, actionable business recommendations. If the sample size is small, explicitly say the recommendations are preliminary. Keep it concise."""

        client = get_client()
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return (response.text or "").strip() + _sample_size_note(summary)
    except Exception as err:
        return f"AI recommendations temporarily unavailable ({type(err).__name__})."

def chat_about_report(summary: dict, question: str, history: list | None = None) -> str:
    try:
        history = history or []
        transcript = "\n".join(f"{h['role']}: {h['content']}" for h in history[-6:])

        prompt = f"""You are a business analyst assistant. You may Only use the summary data below to answer. Do not invent numbers that aren't present, and say so if the data doesn't contain what's needed to answer.
        
        Summary data:
        {summary}

        Conversation so far:
        {transcript}
        
        New questions: {question}

        Answer concisely and specifically, referencing the actual numbers above where relevant."""

        client = get_client()
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return (response.text or "").strip()
    except Exception as err:
        return f"Chat is temporarily unavailable ({type(err).__name__})."

    