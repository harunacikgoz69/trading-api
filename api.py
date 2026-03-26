from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
import anthropic
import os
import yfinance as yf

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
    "anthropic": { "deep": "claude-opus-4-20250514",  "quick": "claude-sonnet-4-20250514" },
    "openai":    { "deep": "gpt-4o",                  "quick": "gpt-4o-mini" },
    "google":    { "deep": "gemini-2.0-flash", "quick": "gemini-2.0-flash" },
    "groq":      { "deep": "llama-3.3-70b-versatile", "quick": "llama-3.3-70b-versatile" },

BIST_TICKERS = [
    "ACSEL","ADEL","ADESE","ADGYO","AEFES","AFYON","AGESA","AGROT","AGYO","AHGAZ",
    "AKBNK","AKCNS","AKFEN","AKFGY","AKFYE","AKIM","AKISA","AKKGZ","AKKOM","AKPAZ",
    "AKSGY","AKSUE","AKTIF","ALARK","ALBRK","ALCAR","ALCTL","ALFAS","ALGYO","ALKA",
    "ALKIM","ALKLC","ALMAD","ALPMA","ALTIN","ALTNY","ALVES","ANELE","ANGEN","ANHYT",
    "ANSGR","ARASE","ARCLK","ARDYZ","ARENA","ARSAN","ARTMS","ARZUM","ASELS","ASGYO",
    "ASTOR","ASUZU","ATAGY","ATAKP","ATATP","ATEKS","ATLAS","ATPET","AVGYO","AVHOL",
    "AVOD","AVPGY","AVTUR","AYCES","AYEN","AYGAZ","AZTEK","BAGFS","BAKCL","BAKAB",
    "BALAT","BANVT","BARMA","BASCM","BASGZ","BAYRK","BEGYO","BERA","BEYAZ","BFREN",
    "BIMAS","BIOEN","BIONC","BIOSS","BIRTO","BITHM","BIZIM","BJKAS","BKFIN","BLCYT",
    "BNTAS","BOBET","BORLS","BORSK","BOSSA","BRISA","BRKSN","BRKVY","BRMEN","BRSAN",
    "BRYAT","BSOKE","BTCIM","BUCIM","BURCE","BURVA","BVSAN","CCOLA","CELHA","CEMAS",
    "CEMTS","CENGZ","CEOEM","CIMSA","CLEBI","CMBTN","CMENT","CONSE","COSMO","CRDFA",
    "CRFSA","CUSAN","CWENE","DAGI","DAPGM","DARDL","DESA","DESPC","DEVA","DGATE",
    "DGNMO","DINHO","DITAS","DMSAS","DNISI","DOAS","DOBUR","DOCO","DOGUB","DOHOL",
    "DOWAL","DRDGE","DURDO","DURKN","DYOBY","DZGYO","ECILC","ECZYT","EDATA","EDIP",
    "EGEEN","EGGUB","EGPRO","EGSER","EKGYO","EKSUN","ELITE","EMKEL","EMNIS","ENERY",
    "ENJSA","ENKAI","ENSRI","ENTRA","EPLAS","ERBOS","ERCB","EREGL","ERGLI","ESCAR",
    "ESCOM","ESEN","ETILR","ETYAT","EUHOL","EUPWR","EUREN","EUYO","EXXEN","FADE",
    "FENER","FMIZP","FONET","FORMT","FORTE","FRIGO","FROTO","FZLGY","GARAN","GARFA",
    "GEDIK","GEDZA","GENIL","GENTS","GEREL","GESAN","GIPTA","GLBMD","GLCVY","GLRYH",
    "GLYHO","GMTAS","GOLTS","GOODY","GOZDE","GRNYO","GRSEL","GRTRK","GSDDE",
    "GSDHO","GSRAY","GUBRF","GWIND","GZNMI","HALKB","HATEK","HDFGS","HEDEF","HEKTS",
    "HLGYO","HOROZ","HTTBT","HUBVC","HUNER","HURGZ","ICBCT","IDGYO","IEYHO","IHAAS",
    "IHEVA","IHGZT","IHLAS","IHLGM","IHYAY","IMASM","INDES","INFO","INTEM","INVEO",
    "IPEKE","ISATR","ISBIR","ISCTR","ISFIN","ISGSY","ISGYO","ISKPL","ISKUR","ISYAT",
    "ITTFK","IZFAS","IZMDC","IZTAR","JANTS","KAREL","KARSN","KARTN","KATMR","KAYSE",
    "KBORU","KCAER","KCHOL","KENT","KENVT","KERVT","KFEIN","KGYO","KILCO","KILICT",
    "KLGYO","KLKIM","KLNMA","KLRHO","KLSER","KMPUR","KNFRT","KOCMT","KONKA","KONTR",
    "KONYA","KOPOL","KORDS","KOSEN","KOTON","KOZAA","KOZAL","KRDMA","KRDMB","KRDMD",
    "KRGYO","KRONT","KRPLS","KRSTL","KRTEK","KRVGD","KSTUR","KTLEV","KTSKR","KUTPO",
    "KUVVA","KUYAS","KZBGY","KZGYO","LIDER","LIDFA","LINK","LKMNH","LOGO","LRSHO",
    "LUKSK","MAALT","MACKO","MAGEN","MAKIM","MAKTK","MANAS","MARBL","MARKA","MARTI",
    "MAVI","MEDTR","MEGAP","MEGMT","MEKAG","MEPET","MERCN","MERIT","MERKO","METRO",
    "METUR","MGROS","MIATK","MIPAZ","MMCAS","MNDRS","MNVAT","MOBTL","MOGAN","MPARK",
    "MRGYO","MRSHL","MSGYO","MTRKS","MZHLD","NATEN","NETAS","NIBAS","NILYT","NKAS",
    "NTHOL","NTGAZ","NUGYO","NUHCM","NUTKG","OBAMS","OBASE","ODAS","ODINE","OFISE",
    "ONCSM","ORCAY","ORGE","ORMA","OSMEN","OSTIM","OTKAR","OTTO","OYAKC","OYAYO",
    "OYLUM","OZGYO","OZKGY","OZRDN","OZSUB","PAGYO","PAMEL","PAPIL","PARSN","PASEU",
    "PCILT","PEGYO","PEKGY","PENGD","PENTA","PETKM","PETUN","PGSUS","PINSU","PKART",
    "PKENT","PLTUR","PNLSN","POLHO","POLTK","POLY","PRDGS","PRZMA","PSDTC","PSGYO",
    "QNBFB","QNBFL","QUAGR","RAYSG","REEDR","RGYAS","RHGYO","RNPOL","RODRG",
    "RTALB","RUBNS","RYSAS","SAFKR","SAHOL","SAMAT","SANEL","SANFM","SANKO","SARKY",
    "SASA","SAYAS","SDTTR","SEGMN","SEKFK","SEKUR","SELEC","SELGD","SELVA","SEYKM",
    "SILVR","SISE","SKBNK","SMART","SMRTG","SNGYO","SNKRN","SOKM","SODSN",
    "SOKE","SONME","SRVGY","SUMAS","SUWEN","TABGD","TACTR","TATGD","TAVHL","TBORG",
    "TCELL","TCKRC","TDGYO","TEKTU","TEZOL","TGSAS","THYAO","TKFEN","TKNSA",
    "TLMAN","TMSN","TMPOL","TNZTP","TOASO","TOFAS","TPVAM","TRGYO","TRILC","TSGYO",
    "TTKOM","TTRAK","TUCLK","TUKAS","TUPRS","TUREX","TURGG","TURSG","TVRST","TYHOL",
    "ULKER","ULUFA","ULUSE","ULUUN","UMPAS","UNLU","USAK","UZERB","VAKBN","VAKFN",
    "VAKKO","VANGD","VBTYZ","VERUS","VESBE","VESTL","VKFYO","VKGYO","VKING","VRGYO",
    "YAPRK","YATAS","YAYLA","YBTAS","YEOTK","YGGYO","YGYO","YKSLN","YKSPR","YUNSA",
    "ZEDUR","ZOREN","ZRGYO"
]

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
                "content": f"Asagidaki finansal analiz raporunu Turkcey cevir. Sadece ceviriyi ver, baska hicbir sey ekleme:\n\n{text[:3000]}"
            }]
        )
        return message.content[0].text
    except:
        return text

@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    ticker = req.ticker

    # BIST hisseleri icin .IS ekle
    if ticker in BIST_TICKERS and not ticker.endswith(".IS"):
        ticker = ticker + ".IS"

    models = PROVIDER_MODELS.get(req.provider, PROVIDER_MODELS["anthropic"])
    config = DEFAULT_CONFIG.copy()
    config["llm_provider"] = req.provider
    config["deep_think_llm"] = models["deep"]
    config["quick_think_llm"] = models["quick"]
    config["max_debate_rounds"] = req.depth
    config["online_tools"] = True

    # Provider ayarlari
    if req.provider == "groq":
        config["llm_provider"] = "openai"
        config["backend_url"] = "https://api.groq.com/openai/v1"
        config["openai_api_key"] = os.environ.get("GROQ_API_KEY", "")
    elif req.provider == "openai":
        config["backend_url"] = "https://api.openai.com/v1"
        config["openai_api_key"] = os.environ.get("OPENAI_API_KEY", "")
    elif req.provider == "google":
        config["backend_url"] = "https://generativelanguage.googleapis.com/v1beta"
    elif req.provider == "anthropic":
        config["backend_url"] = "https://api.anthropic.com"

    ta = TradingAgentsGraph(debug=False, config=config)
    state, decision = ta.propagate(ticker, req.date)

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

@app.get("/bist-stocks")
def get_bist_stocks():
    stocks = [{"symbol": t, "name": t} for t in BIST_TICKERS]
    return {"stocks": stocks}
