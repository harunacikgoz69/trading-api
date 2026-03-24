from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
import anthropic
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    ticker: str
    date: str
    depth: int = 1
    provider: str = "anthropic"
    lang: str = "en"

PROVIDER_MODELS = {
    "anthropic": { "deep": "claude-opus-4-20250514", "quick": "claude-sonnet-4-20250514" },
    "openai":    { "deep": "gpt-4o", "quick": "gpt-4o-mini" },
    "google":    { "deep": "gemini-1.5-pro", "quick": "gemini-1.5-flash" },
}

def translate_to_turkish(text: str) -> str:
    if not text or len(text.strip()) < 10:
        return text
    try:
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": f"Aşağıdaki finansal analiz raporunu Türkçeye çevir. Sadece çeviriyi ver, başka hiçbir şey ekleme:\n\n{text[:3000]}"
            }]
        )
        return message.content[0].text
    except:
        return text

@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    models = PROVIDER_MODELS.get(req.provider, PROVIDER_MODELS["anthropic"])
    config = DEFAULT_CONFIG.copy()
    config["llm_provider"] = req.provider
    config["deep_think_llm"] = models["deep"]
    config["quick_think_llm"] = models["quick"]
    config["max_debate_rounds"] = req.depth
    config["online_tools"] = True

    ta = TradingAgentsGraph(debug=False, config=config)
    state, decision = ta.propagate(req.ticker, req.date)

    def get(key):
        val = state.get(key)
        if not val:
            return ""
        return str(val)

    debate = state.get("investment_debate_state") or {}

    reports = {
        "fundamentals": get("market_report"),
        "sentiment":    get("sentiment_report"),
        "news":         get("news_report"),
        "technical":    get("technical_report"),
        "bull":         str(debate.get("bull_history", "") or ""),
        "bear":         str(debate.get("bear_history", "") or ""),
        "trader":       get("trader_investment_plan"),
        "risk":         get("final_trade_decision"),
    }

    final_decision = str(decision)

    if req.lang == "tr":
        for key in reports:
            reports[key] = translate_to_turkish(reports[key])
        final_decision = translate_to_turkish(final_decision)

    return {"decision": final_decision, "reports": reports}