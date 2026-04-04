from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
import anthropic
import os
import uuid
import threading

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# In-memory job store
jobs = {}
jobs_lock = threading.Lock()

class AnalyzeRequest(BaseModel):
    ticker: str
    date: str
    depth: int = 1
    provider: str = "anthropic"
    lang: str = "en"
    market: str = "US"
    sources: dict = None

PROVIDER_MODELS = {
    "anthropic": {"deep": "claude-opus-4-20250514", "quick": "claude-haiku-4-5-20251001"},
    "openai":    {"deep": "gpt-4o", "quick": "gpt-4o-mini"},
}

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
                "content": f"Asagidaki finansal analiz raporunu Turkce cevir. Sadece ceviriyi ver, baska hicbir sey ekleme:\n\n{text[:3000]}"
            }]
        )
        return message.content[0].text
    except:
        return text

def run_analysis_job(job_id: str, req: AnalyzeRequest):
    try:
        with jobs_lock:
            jobs[job_id]["status"] = "running"

        ticker = req.ticker
        if ticker in BIST_TICKERS and not ticker.endswith(".IS"):
            ticker = ticker + ".IS"

        models = PROVIDER_MODELS.get(req.provider, PROVIDER_MODELS["anthropic"])
        config = DEFAULT_CONFIG.copy()
        config["deep_think_llm"] = models["deep"]
        config["quick_think_llm"] = models["quick"]
        config["max_debate_rounds"] = req.depth
        config["online_tools"] = True
        config["max_recur_limit"] = 30
        if req.lang == "tr":
            config["output_language"] = "Turkish"

        if req.provider == "openai":
            config["llm_provider"] = "openai"
            config["backend_url"] = "https://api.openai.com/v1"
            real_key = os.environ.get("OPENAI_API_KEY_REAL", os.environ.get("OPENAI_API_KEY", ""))
            os.environ["OPENAI_API_KEY"] = real_key
        elif req.provider == "anthropic":
            config["llm_provider"] = "anthropic"
            config["backend_url"] = "https://api.anthropic.com"

        if req.sources:
            if req.market == "BIST":
                os.environ["ANALYST_SOURCE_NOTES"] = (
                    f"ONEMLI: Bu analiz Turkiye borsasi hissesi icin yapilmaktadir. "
                    f"Temel analiz icin {', '.join(req.sources.get('fundamentals', []))} kaynaklarini kullan."
                )
            else:
                os.environ["ANALYST_SOURCE_NOTES"] = (
                    f"IMPORTANT: Focus on these sources - "
                    f"Fundamentals: {', '.join(req.sources.get('fundamentals', []))}."
                )
        else:
            os.environ["ANALYST_SOURCE_NOTES"] = ""

        ta = TradingAgentsGraph(debug=False, config=config)
        state, decision = ta.propagate(ticker, req.date)
        def get(key):
            val = state.get(key)
            if not val:
                return ""
            return str(val)

        def get_sources():
            sources = set()
            try:
                messages = state.get("messages", [])[:50]  # max 50 mesaj
                for msg in messages:
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tc in msg.tool_calls:
                            name = tc.get("name", "") if isinstance(tc, dict) else getattr(tc, "name", "")
                            if name:
                                sources.add(name)
                    if hasattr(msg, "name") and msg.name:
                        sources.add(msg.name)
            except:
                pass
            source_labels = {
                "get_stock_data": "Yahoo Finance (Hisse Verisi)",
                "get_indicators": "Yahoo Finance (Teknik Göstergeler)",
                "get_fundamentals": "Yahoo Finance (Temel Analiz)",
                "get_balance_sheet": "Yahoo Finance (Bilanço)",
                "get_cashflow": "Yahoo Finance (Nakit Akışı)",
                "get_income_statement": "Yahoo Finance (Gelir Tablosu)",
                "get_news": "Yahoo Finance (Haberler)",
                "get_global_news": "Yahoo Finance (Global Haberler)",
                "get_insider_transactions": "Yahoo Finance (İçeriden İşlemler)",
                "get_tr_news": "AA Ekonomi + BBC Türkçe",
                "get_tcmb_rates": "TCMB (Döviz Kurları)",
                "get_kap_disclosures": "KAP/MKK (Resmi Bildirimler)",
            }
            used = [source_labels.get(s, s) for s in sorted(sources) if s]
            if not used:
                used = ["Yahoo Finance", "AA Ekonomi", "BBC Türkçe", "TCMB"]
            return "## Kullanılan Veri Kaynakları\n\n" + "\n".join(f"- {u}" for u in used)

        debate = state.get("investment_debate_state") or {}

        reports = {
            "fundamentals": get("fundamentals_report"),
            "sentiment":    get("sentiment_report"),
            "news":         get("news_report"),
            "technical":    get("market_report"),
            "bull":         str(debate.get("bull_history", "") or ""),
            "bear":         str(debate.get("bear_history", "") or ""),
            "trader":       get("trader_investment_plan"),
            "risk":         get("final_trade_decision"),
            "scenario":     get("scenario_report"),
            "sources":      get_sources(),
        }

        final_decision = str(decision)

        with jobs_lock:
            jobs[job_id]["status"] = "done"
            jobs[job_id]["result"] = {
                "decision": final_decision,
                "reports": reports,
            }

    except Exception as e:
        with jobs_lock:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = str(e)


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    job_id = str(uuid.uuid4())
    with jobs_lock:
        jobs[job_id] = {"status": "queued", "result": None, "error": None}
    thread = threading.Thread(target=run_analysis_job, args=(job_id, req))
    thread.daemon = True
    thread.start()
    return {"job_id": job_id}


@app.get("/status/{job_id}")
def get_status(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
    if not job:
        return {"status": "not_found"}
    return {
        "status": job["status"],
        "result": job.get("result"),
        "error": job.get("error"),
    }


@app.get("/bist-stocks")
def get_bist_stocks():
    stocks = [{"symbol": t, "name": t} for t in BIST_TICKERS]
    return {"stocks": stocks}


@app.get("/price/{symbol}")
def get_price(symbol: str):
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info
        price = info.last_price
        prev_close = info.previous_close
        change = price - prev_close
        change_pct = (change / prev_close) * 100
        return {
            "symbol": symbol,
            "price": round(price, 2),
            "change": round(change, 2),
            "changePercent": round(change_pct, 2)
        }
    except Exception as e:
        return {"symbol": symbol, "price": None, "error": str(e)}


class CompareRequest(BaseModel):
    symbol: str
    current_decision: str
    current_report: str
    previous_decision: str
    previous_report: str


@app.post("/compare")
def compare_analyses(req: CompareRequest):
    try:
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": f"""Asagida {req.symbol} hissesi icin iki farkli tarihte yapilan analiz var.

Onceki Analiz Karari: {req.previous_decision[:200]}
Yeni Analiz Karari: {req.current_decision[:200]}

Bu iki analiz arasindaki en onemli degisiklikleri 2-3 cumleyle Turkce olarak ozet."""
            }]
        )
        return {"note": message.content[0].text}
    except Exception as e:
        return {"note": "", "error": str(e)}

@app.get("/cache/clear")
def clear_cache():
    import glob
    cache_dir = os.path.join(DEFAULT_CONFIG["project_dir"], "dataflows/data_cache")
    files = glob.glob(os.path.join(cache_dir, "*.csv"))
    for f in files:
        try:
            os.remove(f)
        except:
            pass
    return {"cleared": len(files), "files": [os.path.basename(f) for f in files]}

@app.get("/test-mkk/{ticker}")
def test_mkk(ticker: str):
    from tradingagents.dataflows.kap_client import get_kap_disclosures, get_kap_member_detail
    disclosures = get_kap_disclosures(ticker)
    member = get_kap_member_detail(ticker)
    return {"disclosures": disclosures[:1000], "member": member[:300]}

class PortfolioOptimizeRequest(BaseModel):
    symbols: list
    analyses: list = []
    lang: str = "tr"

@app.post("/optimize-portfolio")
def optimize_portfolio(req: PortfolioOptimizeRequest):
    job_id = str(uuid.uuid4())
    with jobs_lock:
        jobs[job_id] = {"status": "queued", "result": None, "error": None}

    def run_optimizer():
        try:
            with jobs_lock:
                jobs[job_id]["status"] = "running"


            # Claude ile portföy optimizasyonu
            client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

            analysis_lines = []
            for a in req.analyses:
                decision = a.get("decision", "")
                symbol = a.get("symbol", "")
                report = a.get("report", "")[:500]
                if "buy" in decision.lower() or "al" in decision.lower():
                    karar = "BUY ✅"
                elif "sell" in decision.lower() or "sat" in decision.lower():
                    karar = "SELL ❌"
                else:
                    karar = "HOLD ⚠️"
                analysis_lines.append(f"- {symbol}: {karar}\n  Rapor özeti: {report[:200]}")

            analysis_text = "\n".join(analysis_lines) if analysis_lines else "Analiz verisi yok, sadece semboller: " + ", ".join(req.symbols)

            prompt = f"""Sen bir portföy optimizasyon uzmanısın. Aşağıdaki GERÇEK analiz sonuçlarına KESINLIKLE uy.

ANALIZ SONUÇLARI (bu verileri değiştirme, kullan):
{analysis_text}

ZORUNLU KURALLAR:
1. BUY kararı → %15-35 ağırlık ver
2. HOLD kararı → %5-15 ağırlık ver  
3. SELL kararı → %0-5 ağırlık ver (portföye dahil etme)
4. Toplam = %100
5. Hiçbir hisse %40 üstünde olamaz
6. En az 2 farklı sektör olmalı

Şu formatı kullan:

## Portföy Önerisi

| Hisse | Ağırlık | Sektör | Analiz Kararı | Gerekçe |
|-------|---------|--------|---------------|---------|
| XXXX | %XX | Sektör | BUY/HOLD/SELL | Kısa gerekçe |

## Özet
[Analiz kararlarına dayalı 2-3 cümle]

## Risk Değerlendirmesi
[Risk faktörleri]

Türkçe yanıt ver. Analiz kararlarını KESINLIKLE yansıt."""

            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            result = message.content[0].text

            with jobs_lock:
                jobs[job_id]["status"] = "done"
                jobs[job_id]["result"] = {"portfolio": result, "symbols": req.symbols}

        except Exception as e:
            with jobs_lock:
                jobs[job_id]["status"] = "error"
                jobs[job_id]["error"] = str(e)

    thread = threading.Thread(target=run_optimizer)
    thread.daemon = True
    thread.start()
    return {"job_id": job_id}

@app.get("/chart-data/{symbol}")
def get_chart_data(symbol: str, period: str = "1mo"):
    try:
        import yfinance as yf
        import pandas as pd
        
        # BIST sembolü düzelt
        yf_symbol = symbol
        if not symbol.endswith(".IS") and symbol in BIST_TICKERS:
            yf_symbol = symbol + ".IS"
        
        # Period mapping
        period_map = {
            "7d": ("7d", "1h"),
            "1mo": ("1mo", "1d"),
            "1y": ("1y", "1wk"),
        }
        yf_period, interval = period_map.get(period, ("1mo", "1d"))
        
        ticker = yf.Ticker(yf_symbol)
        hist = ticker.history(period=yf_period, interval=interval)
        
        if hist.empty:
            return {"error": "Veri bulunamadı", "symbol": symbol}
        
        hist = hist.reset_index()
        
        # Tarih kolonunu string'e çevir
        date_col = "Datetime" if "Datetime" in hist.columns else "Date"
        hist[date_col] = hist[date_col].astype(str)
        
        prices = []
        for _, row in hist.iterrows():
            prices.append({
                "date": str(row[date_col])[:16],
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]),
            })
        
        # Teknik göstergeler hesapla
        closes = [p["close"] for p in prices]
        
        def sma(data, window):
            result = []
            for i in range(len(data)):
                if i < window - 1:
                    result.append(None)
                else:
                    result.append(round(sum(data[i-window+1:i+1]) / window, 2))
            return result
        
        def ema(data, window):
            result = []
            k = 2 / (window + 1)
            for i in range(len(data)):
                if i == 0:
                    result.append(data[0])
                else:
                    result.append(round(data[i] * k + result[-1] * (1 - k), 2))
            return result
        
        def rsi(data, window=14):
            result = [None] * window
            for i in range(window, len(data)):
                gains = []
                losses = []
                for j in range(i - window, i):
                    diff = data[j+1] - data[j]
                    if diff >= 0:
                        gains.append(diff)
                    else:
                        losses.append(abs(diff))
                avg_gain = sum(gains) / window if gains else 0
                avg_loss = sum(losses) / window if losses else 0
                if avg_loss == 0:
                    result.append(100)
                else:
                    rs = avg_gain / avg_loss
                    result.append(round(100 - (100 / (1 + rs)), 2))
            return result
        
        def bollinger(data, window=20, num_std=2):
            upper, lower, middle = [], [], []
            for i in range(len(data)):
                if i < window - 1:
                    upper.append(None)
                    lower.append(None)
                    middle.append(None)
                else:
                    slice_ = data[i-window+1:i+1]
                    avg = sum(slice_) / window
                    std = (sum((x - avg) ** 2 for x in slice_) / window) ** 0.5
                    middle.append(round(avg, 2))
                    upper.append(round(avg + num_std * std, 2))
                    lower.append(round(avg - num_std * std, 2))
            return upper, middle, lower
        
        def macd(data, fast=12, slow=26, signal=9):
            ema_fast = ema(data, fast)
            ema_slow = ema(data, slow)
            macd_line = [round(f - s, 2) if f and s else None 
                        for f, s in zip(ema_fast, ema_slow)]
            # Signal line (EMA of MACD)
            macd_values = [m for m in macd_line if m is not None]
            signal_raw = ema(macd_values, signal)
            # Pad with None
            pad = len(macd_line) - len(signal_raw)
            signal_line = [None] * pad + signal_raw
            histogram = [round(m - s, 2) if m is not None and s is not None else None
                        for m, s in zip(macd_line, signal_line)]
            return macd_line, signal_line, histogram
        
        sma20 = sma(closes, 20)
        sma50 = sma(closes, 50)
        ema10 = ema(closes, 10)
        rsi14 = rsi(closes, 14)
        bb_upper, bb_middle, bb_lower = bollinger(closes, 20)
        macd_line, signal_line, histogram = macd(closes)
        
        # Her price point'e indikatörleri ekle
        for i, p in enumerate(prices):
            p["sma20"] = sma20[i]
            p["sma50"] = sma50[i]
            p["ema10"] = ema10[i]
            p["rsi"] = rsi14[i]
            p["bb_upper"] = bb_upper[i]
            p["bb_middle"] = bb_middle[i]
            p["bb_lower"] = bb_lower[i]
            p["macd"] = macd_line[i]
            p["macd_signal"] = signal_line[i]
            p["macd_hist"] = histogram[i]
        
        # Özet istatistikler
        current = closes[-1] if closes else 0
        high_52w = max(closes) if closes else 0
        low_52w = min(closes) if closes else 0
        
        return {
            "symbol": symbol,
            "period": period,
            "prices": prices,
            "summary": {
                "current": round(current, 2),
                "high": round(high_52w, 2),
                "low": round(low_52w, 2),
                "rsi": rsi14[-1] if rsi14 else None,
                "macd": macd_line[-1] if macd_line else None,
                "sma20": sma20[-1] if sma20 else None,
                "sma50": sma50[-1] if sma50 else None,
            }
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


