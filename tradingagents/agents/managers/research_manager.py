from tradingagents.agents.utils.agent_utils import build_instrument_context


def create_research_manager(llm, memory):
    def research_manager_node(state) -> dict:
        instrument_context = build_instrument_context(state["company_of_interest"])
        history = state["investment_debate_state"].get("history", "")
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]
        investment_debate_state = state["investment_debate_state"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        prompt = f"""You are the Research Manager adjudicating the Bull vs Bear debate. Your job is to determine which side presented STRONGER EVIDENCE — not which side argued more forcefully.

{instrument_context}

EVIDENCE QUALITY RULES (apply strictly):
1. Arguments backed by SPECIFIC NUMBERS (revenue growth %, debt ratios, price targets with methodology) outweigh generic claims
2. Generic risks like "geopolitical uncertainty" or "competition" without quantified impact do NOT override strong data-backed arguments
3. If bull presents specific financial data and bear presents only general risks → lean BUY
4. If bear presents specific deteriorating metrics and bull presents only narrative → lean SELL
5. HOLD is valid ONLY when both sides present equally strong specific evidence pointing in opposite directions

PAST MISTAKES TO AVOID:
{past_memory_str}

YOUR OUTPUT MUST INCLUDE:
1. WINNING ARGUMENT: Which side (Bull/Bear) had stronger evidence and why (cite specific data points)
2. LOSING ARGUMENT: What the other side got wrong or lacked
3. INVESTMENT PLAN FOR TRADER: Concrete recommendation with specific price levels, time horizon, and key catalysts to watch
4. PRELIMINARY STANCE: Buy / Hold / Sell

Be direct. Do not hedge excessively. The trader needs a clear, actionable plan.

DEBATE HISTORY:
{history}"""

        response = llm.invoke(prompt)

        new_investment_debate_state = {
            "judge_decision": response.content,
            "history": investment_debate_state.get("history", ""),
            "bear_history": investment_debate_state.get("bear_history", ""),
            "bull_history": investment_debate_state.get("bull_history", ""),
            "current_response": response.content,
            "count": investment_debate_state["count"],
        }

        return {
            "investment_debate_state": new_investment_debate_state,
            "investment_plan": response.content,
        }

    return research_manager_node