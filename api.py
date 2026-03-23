from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

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

@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    config = DEFAULT_CONFIG.copy()
    config["llm_provider"] = "anthropic"
    config["deep_think_llm"] = "claude-opus-4-20250514"
    config["quick_think_llm"] = "claude-sonnet-4-20250514"
    config["max_debate_rounds"] = req.depth
    config["online_tools"] = True

    ta = TradingAgentsGraph(debug=False, config=config)
    _, decision = ta.propagate(req.ticker, req.date)

    return { "decision": str(decision), "reports": {} }
