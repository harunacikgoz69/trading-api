from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tradingagents.agents.utils.agent_utils import get_language_instruction


def create_scenario_agent(llm):
    def scenario_agent_node(state):
        current_date = state["trade_date"]
        company = state["company_of_interest"]
        final_decision = state.get("final_trade_decision", "")
        market_report = state.get("market_report", "")
        fundamentals_report = state.get("fundamentals_report", "")
        news_report = state.get("news_report", "")
        sentiment_report = state.get("sentiment_report", "")

        system_message = f"""You are an expert scenario analyst. Based on all the research reports and the final trade decision, 
you must generate three probability-weighted price scenarios for {company} as of {current_date}.

You have access to:
- Market/Technical report
- Fundamentals report  
- News report
- Sentiment report
- Final trade decision: {final_decision}

Generate exactly this structure:

## Scenario Analysis for {company} — {current_date}

### Bull Scenario (probability: X%)
- Thesis: [what needs to go right]
- 1-month target: $XX
- 3-month target: $XX
- 6-month target: $XX
- 12-month target: $XX

### Base Scenario (probability: X%)
- Thesis: [most likely outcome]
- 1-month target: $XX
- 3-month target: $XX
- 6-month target: $XX
- 12-month target: $XX

### Bear Scenario (probability: X%)
- Thesis: [what could go wrong]
- 1-month target: $XX
- 3-month target: $XX
- 6-month target: $XX
- 12-month target: $XX

### Probability-Weighted Expected Price
- 1-month: $XX
- 3-month: $XX
- 6-month: $XX
- 12-month: $XX

### Key Risks & Catalysts
- [list main upside catalysts]
- [list main downside risks]

Probabilities must sum to 100%. Be specific with price targets based on the research.
{get_language_instruction()}"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", f"""Here are brief research summaries:

MARKET: {market_report[:500]}

FUNDAMENTALS: {fundamentals_report[:500]}

NEWS: {news_report[:500]}

SENTIMENT: {sentiment_report[:500]}

Based on all this research and the final decision of {final_decision}, generate the scenario analysis."""),
        ])

        chain = prompt | llm
        result = chain.invoke({})

        return {
            "messages": [result],
            "scenario_report": result.content,
        }

    return scenario_agent_node