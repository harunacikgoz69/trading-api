from tradingagents.agents.utils.agent_utils import build_instrument_context, get_language_instruction


def create_portfolio_manager(llm, memory):
    def portfolio_manager_node(state) -> dict:
        instrument_context = build_instrument_context(state["company_of_interest"])
        history = state["risk_debate_state"]["history"]
        risk_debate_state = state["risk_debate_state"]
        market_research_report = state["market_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]
        sentiment_report = state["sentiment_report"]
        trader_plan = state["investment_plan"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        prompt = f"""You are the Portfolio Manager making the FINAL trading decision. You have the trader's plan and the risk analysts' debate. Your decision must be data-driven and consistent.

{instrument_context}

CONSISTENCY RULE: Your final decision must align with the weight of evidence, not with the most recent or loudest argument. If the trader recommended BUY based on strong fundamentals, you need SPECIFIC deteriorating data to override it — not just general risk concerns.

FINAL RATING SCALE (choose exactly one):
- **BUY**: Enter or add to position — fundamentals + at least one other factor positive
- **HOLD**: Maintain position — mixed signals with no clear dominant direction
- **SELL**: Exit or avoid — fundamentals deteriorating OR technical breakdown + macro headwinds confirmed

OVERRIDE CONDITIONS:
- You may override trader's BUY to HOLD only if risk analysts identified a specific near-term catalyst for downside (earnings miss risk, regulatory action, etc.)
- You may override trader's HOLD to SELL only if risk debate reveals structural problems not captured in fundamentals report
- You may NOT override based on generic "uncertainty" — every override needs a specific, quantified reason

PAST LESSONS:
{past_memory_str}

TRADER'S PLAN:
{trader_plan[:500]}

RISK ANALYSTS DEBATE:
{history}

YOUR OUTPUT:
1. FINAL RATING: Buy / Hold / Sell
2. OVERRIDE DECISION: Did you change the trader's recommendation? If yes, state the specific reason with data.
3. EXECUTIVE SUMMARY: Entry/exit strategy, position sizing, stop loss, time horizon
4. KEY RISKS TO MONITOR: Maximum 3, each with a specific trigger level

Be decisive. Vague conclusions are not acceptable.{get_language_instruction()}"""

        response = llm.invoke(prompt)

        new_risk_debate_state = {
            "judge_decision": response.content,
            "history": risk_debate_state["history"],
            "aggressive_history": risk_debate_state["aggressive_history"],
            "conservative_history": risk_debate_state["conservative_history"],
            "neutral_history": risk_debate_state["neutral_history"],
            "latest_speaker": "Judge",
            "current_aggressive_response": risk_debate_state["current_aggressive_response"],
            "current_conservative_response": risk_debate_state["current_conservative_response"],
            "current_neutral_response": risk_debate_state["current_neutral_response"],
            "count": risk_debate_state["count"],
        }

        return {
            "risk_debate_state": new_risk_debate_state,
            "final_trade_decision": response.content,
        }

    return portfolio_manager_node