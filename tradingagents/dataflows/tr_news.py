import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Optional

RSS_FEEDS = {
    "aa_ekonomi": "https://www.aa.com.tr/tr/rss/default?cat=ekonomi",
    "aa_genel": "https://www.aa.com.tr/tr/rss/default?cat=guncel",
    "bbc_turkce": "https://feeds.bbci.co.uk/turkce/rss.xml",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml",
}

def fetch_rss(url: str, timeout: int = 10) -> list:
    try:
        res = requests.get(url, headers=HEADERS, timeout=timeout, verify=False)
        res.encoding = "utf-8"
        root = ET.fromstring(res.content)
        items = []
        for item in root.findall(".//item"):
            title = item.findtext("title", "").strip()
            desc = item.findtext("description", "").strip()
            link = item.findtext("link", "").strip()
            pub_date = item.findtext("pubDate", "").strip()
            if title:
                items.append({
                    "title": title,
                    "description": desc,
                    "link": link,
                    "pubDate": pub_date,
                })
        return items
    except Exception as e:
        return []

def get_tr_news(symbol: str, days_back: int = 7) -> str:
    """
    Fetch Turkish economic news from AA and BBC Türkçe RSS feeds.
    Filters news relevant to the given stock symbol.
    Returns formatted news string for agent consumption.
    """
    company_name = symbol.replace(".IS", "").replace(".is", "")
    
    all_news = []
    for source, url in RSS_FEEDS.items():
        items = fetch_rss(url)
        for item in items:
            text = (item["title"] + " " + item["description"]).upper()
            all_news.append({
                "source": source,
                "title": item["title"],
                "description": item["description"],
                "link": item["link"],
                "pubDate": item["pubDate"],
                "relevant": company_name.upper() in text,
            })

    relevant = [n for n in all_news if n["relevant"]]
    general_economic = [n for n in all_news if not n["relevant"]][:10]

    output = []

    if relevant:
        output.append(f"## {company_name} ile İlgili Haberler\n")
        for n in relevant:
            output.append(f"**{n['title']}**")
            if n["description"]:
                output.append(f"{n['description'][:300]}")
            output.append(f"Kaynak: {n['source']} | {n['pubDate']}\n")
    else:
        output.append(f"## {company_name} için Doğrudan Haber Bulunamadı\n")

    output.append("## Genel Ekonomi Haberleri (Son 10)\n")
    for n in general_economic:
        output.append(f"**{n['title']}**")
        if n["description"]:
            output.append(f"{n['description'][:200]}")
        output.append(f"Kaynak: {n['source']} | {n['pubDate']}\n")

    return "\n".join(output)


def get_tcmb_rates() -> str:
    """
    Fetch TCMB interest rate and key economic indicators.
    """
    try:
        url = "https://www.tcmb.gov.tr/kurlar/today.xml"
        res = requests.get(url, headers=HEADERS, timeout=10, verify=False)
        res.encoding = "utf-8"
        root = ET.fromstring(res.content)

        rates = {}
        for currency in root.findall(".//Currency"):
            code = currency.get("CurrencyCode", "")
            buying = currency.findtext("ForexBuying", "")
            selling = currency.findtext("ForexSelling", "")
            if code in ["USD", "EUR", "GBP"]:
                rates[code] = {"buying": buying, "selling": selling}

        if not rates:
            return "TCMB kur verisi alınamadı."

        output = ["## TCMB Güncel Kurlar\n"]
        for code, r in rates.items():
            output.append(f"**{code}/TRY** — Alış: {r['buying']} | Satış: {r['selling']}")

        return "\n".join(output)
    except Exception as e:
        return f"TCMB verisi alınamadı: {str(e)}"