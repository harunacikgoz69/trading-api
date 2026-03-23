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

PROVIDER_MODELS = {
    "anthropic": {
        "deep": "claude-opus-4-20250514",
        "quick": "claude-sonnet-4-20250514",
    },
    "openai": {
        "deep": "gpt-4o",
        "quick": "gpt-4o-mini",
    },
    "google": {
        "deep": "gemini-1.5-pro",
        "quick": "gemini-1.5-flash",
    },
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

    ta = TradingAgentsGraph(debug=False, config=config)
    state, decision = ta.propagate(req.ticker, req.date)

    reports = {
        "fundamentals": str(state.get("market_report", "") or ""),
        "sentiment": str(state.get("sentiment_report", "") or ""),
        "news": str(state.get("news_report", "") or ""),
        "technical": str(state.get("technical_report", "") or ""),
        "bull": str(state.get("investment_debate_state", {}).get("bull_history", "") or ""),
        "bear": str(state.get("investment_debate_state", {}).get("bear_history", "") or ""),
        "trader": str(state.get("trader_investment_plan", "") or ""),
        "risk": str(state.get("final_trade_decision", "") or ""),
    }

    return {"decision": str(decision), "reports": reports}