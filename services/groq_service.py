import os
from groq import Groq

client = None

def get_client():
    global client
    if client is None:
        api_key = os.getenv('GROQ_API_KEY', '')
        if api_key:
            client = Groq(api_key=api_key)
    return client

def generate_ceo_report(context_data: dict) -> str:
    """Generate executive CEO report using Groq"""
    c = get_client()
    if not c:
        return _fallback_report(context_data)

    prompt = f"""You are a senior supply chain risk analyst. Generate a structured executive CEO report based on the following data:

PLATFORM DATA SUMMARY:
- Total News Events Analyzed: {context_data.get('total_news', 0)}
- High Severity Events: {context_data.get('high_severity', 0)}
- Most Affected Countries: {context_data.get('top_countries', [])}
- Most Affected Industries: {context_data.get('top_industries', [])}
- Average Risk Score: {context_data.get('avg_risk', 0):.1f}/100
- Active Alerts: {context_data.get('active_alerts', 0)}
- Recent Shock Types: {context_data.get('shock_types', [])}

Generate a professional report with these exact sections:
1. EXECUTIVE SUMMARY (2-3 sentences)
2. KEY RISKS IDENTIFIED (3-5 bullet points)
3. FINANCIAL IMPACT ASSESSMENT (specific estimates)
4. STRATEGIC RECOMMENDATIONS (4-5 actionable items)
5. MITIGATION STRATEGIES (3-4 specific strategies)

Keep it concise, data-driven, and actionable. Format clearly with headers."""

    try:
        response = c.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Groq error: {e}")
        return _fallback_report(context_data)

def chat_assistant(user_question: str, db_context: dict) -> str:
    """AI Chat Assistant using Groq with DB context"""
    c = get_client()
    if not c:
        return "Groq API key not configured. Please add your GROQ_API_KEY to .env file."

    system_prompt = """You are a supply chain intelligence assistant. Answer questions about global supply chain risks, disruptions, and investment opportunities. 
Use the provided database context to give specific, data-driven answers. Be concise and professional."""

    context = f"""
CURRENT DATABASE CONTEXT:
- Recent News Events: {db_context.get('recent_news', [])}
- High Risk Countries: {db_context.get('high_risk_countries', [])}
- Active Alerts: {db_context.get('alerts', [])}
- Top Shock Types: {db_context.get('shock_types', [])}
- Affected Industries: {db_context.get('industries', [])}
"""

    try:
        response = c.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {user_question}"}
            ],
            max_tokens=500,
            temperature=0.5
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Groq chat error: {e}")
        return f"Unable to process query: {str(e)}"

def _fallback_report(data: dict) -> str:
    return f"""
## EXECUTIVE SUMMARY
Based on current monitoring data, the global supply chain faces elevated risk conditions with {data.get('total_news', 0)} events analyzed and {data.get('active_alerts', 0)} active alerts requiring immediate attention.

## KEY RISKS IDENTIFIED
- High severity disruptions detected in {', '.join(data.get('top_countries', ['multiple regions']))}
- Critical industries affected: {', '.join(data.get('top_industries', ['various sectors']))}
- Average risk score elevated at {data.get('avg_risk', 0):.1f}/100

## FINANCIAL IMPACT ASSESSMENT
- Estimated revenue impact: 5-15% reduction in affected sectors
- Price increases expected: 8-20% for key commodities
- Lead time extensions: 2-6 weeks across major supply routes

## STRATEGIC RECOMMENDATIONS
1. Diversify supplier base across multiple geographies
2. Increase safety stock for critical components
3. Establish alternative logistics routes
4. Activate contingency procurement plans

## MITIGATION STRATEGIES
- Implement real-time supplier monitoring
- Build strategic inventory reserves
- Develop multi-source procurement contracts
- Establish risk-sharing agreements with key partners

*(Note: Configure GROQ_API_KEY for AI-enhanced reports)*
"""
