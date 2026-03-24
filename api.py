from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
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

@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    models = PROVIDER_MODELS.get(req.provider, PROVIDER_MODELS["anthropic"])
    config = DEFAULT_CONFIG.copy()
    config["llm_provider"] = req.provider
    config["deep_think_llm"] = models["deep"]
    config["quick_think_llm"] = models["quick"]
    config["max_debate_rounds"] = req.depth
    config["online_tools"] = True

    if req.lang == "tr":
        config["language"] = "Turkish"
    else:
        config["language"] = "English"

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

    return {"decision": str(decision), "reports": reports}