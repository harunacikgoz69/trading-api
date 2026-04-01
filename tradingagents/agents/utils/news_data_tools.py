from langchain_core.tools import tool
from typing import Annotated
from tradingagents.dataflows.interface import route_to_vendor

@tool
def get_news(
    ticker: Annotated[str, "Ticker symbol"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """
    Retrieve news data for a given ticker symbol.
    Uses the configured news_data vendor.
    Args:
        ticker (str): Ticker symbol
        start_date (str): Start date in yyyy-mm-dd format
        end_date (str): End date in yyyy-mm-dd format
    Returns:
        str: A formatted string containing news data
    """
    return route_to_vendor("get_news", ticker, start_date, end_date)

@tool
def get_global_news(
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "Number of days to look back"] = 7,
    limit: Annotated[int, "Maximum number of articles to return"] = 5,
) -> str:
    """
    Retrieve global news data.
    Uses the configured news_data vendor.
    Args:
        curr_date (str): Current date in yyyy-mm-dd format
        look_back_days (int): Number of days to look back (default 7)
        limit (int): Maximum number of articles to return (default 5)
    Returns:
        str: A formatted string containing global news data
    """
    return route_to_vendor("get_global_news", curr_date, look_back_days, limit)

@tool
def get_insider_transactions(
    ticker: Annotated[str, "ticker symbol"],
) -> str:
    """
    Retrieve insider transaction information about a company.
    Uses the configured news_data vendor.
    Args:
        ticker (str): Ticker symbol of the company
    Returns:
        str: A report of insider transaction data
    """
    return route_to_vendor("get_insider_transactions", ticker)

@tool
def get_tr_news(
    ticker: Annotated[str, "Ticker symbol (e.g. THYAO or THYAO.IS)"],
) -> str:
    """
    Retrieve Turkish economic news from AA and BBC Turkce RSS feeds.
    Filters news relevant to the given BIST stock symbol.
    Use this for BIST (Turkish stock market) stocks.
    Returns formatted Turkish news string.
    """
    from tradingagents.dataflows.tr_news import get_tr_news as _get_tr_news
    return _get_tr_news(ticker)


@tool
def get_tcmb_rates() -> str:
    """
    Retrieve current TCMB (Turkish Central Bank) exchange rates.
    Returns USD/TRY, EUR/TRY, GBP/TRY rates.
    Use this for BIST stocks to understand macro context.
    """
    from tradingagents.dataflows.tr_news import get_tcmb_rates as _get_tcmb_rates
    return _get_tcmb_rates()
