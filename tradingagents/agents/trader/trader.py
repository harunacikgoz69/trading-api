import functools
from tradingagents.agents.utils.agent_utils import build_instrument_context


def create_trader(llm, memory):
    def trader_node(state, name):
        company_name = state["company_of_interest"]
        instrument_context = build_instrument_context(company_name)
        investment_plan = state["investment_plan"]
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        curr_situation = f"{market_research_report[:500]}\n\n{sentiment_report[:300]}\n\n{news_report[:300]}\n\n{fundamentals_report[:500]}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        if past_memories:
            for i, rec in enumerate(past_memories, 1):
                past_memory_str += rec["recommendation"] + "\n\n"
        else:
            past_memory_str = "No past memories found."

        messages = [
            {
                "role": "system",
                "content": f"""You are a disciplined trading agent. You must evaluate the investment plan using a structured 4-factor decision framework. Do NOT simply follow the loudest argument — weigh each factor independently with specific data points, then synthesize.

DECISION FRAMEWORK — evaluate each factor separately:

1. FUNDAMENTALS (weight: 35%)
   - Revenue growth trend (positive/negative/flat)
   - Profitability: net margin, EBITDA margin
   - Balance sheet: debt levels, cash flow
   - Valuation: is current price justified vs. forward earnings?
   Score each: STRONG POSITIVE / NEUTRAL / STRONG NEGATIVE

2. TECHNICAL MOMENTUM (weight: 25%)
   - Trend direction (above/below key MAs)
   - Momentum indicators (RSI, MACD)
   - Support/resistance levels
   Score each: STRONG POSITIVE / NEUTRAL / STRONG NEGATIVE

3. MACRO & NEWS (weight: 25%)
   - Sector tailwinds or headwinds
   - Currency/interest rate exposure
   - Geopolitical or regulatory risks
   Score each: STRONG POSITIVE / NEUTRAL / STRONG NEGATIVE

4. SENTIMENT (weight: 15%)
   - Market sentiment trend
   - Insider activity or institutional signals
   Score each: STRONG POSITIVE / NEUTRAL / STRONG NEGATIVE

SYNTHESIS RULES (apply strictly):
- 3+ factors STRONG POSITIVE → BUY
- 3+ factors STRONG NEGATIVE → SELL
- 2 STRONG POSITIVE, 2 STRONG NEGATIVE → HOLD (explain the key swing factor)
- Mixed signals: identify the SINGLE most important factor for this specific company/context and weight it higher
- NEVER default to HOLD just because both sides argued well — commit to the dominant signal

IMPORTANT: A bear argument is only valid if it contains specific numbers or data. Generic risks (geopolitics, competition) without quantified impact do NOT override strong positive fundamentals.

Past lessons from similar situations: {past_memory_str}""",
            },
            {
                "role": "user",
                "content": f"""Apply the 4-factor decision framework to make a trading decision for {company_name}.

{instrument_context}

INVESTMENT PLAN FROM RESEARCH TEAM:
{investment_plan[:1000]}

SUPPORTING DATA:
- Fundamentals: {fundamentals_report[:600]}
- Technical: {market_research_report[:400]}
- News/Macro: {news_report[:300]}
- Sentiment: {sentiment_report[:200]}

Structure your response as:
1. FACTOR SCORES (one paragraph each, with specific data)
2. SYNTHESIS (which factors dominate and why)
3. FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**""",
            },
        ]

        result = llm.invoke(messages)

        return {
            "messages": [result],
            "trader_investment_plan": result.content,
            "sender": name,
        }

    return functools.partial(trader_node, name="Trader")