@app.get("/test-mkk/{ticker}")
def test_mkk(ticker: str):
    import requests as req
    import base64
    api_key = os.environ.get("MKK_API_KEY", "")
    api_secret = os.environ.get("MKK_API_SECRET", "")
    
    results = {}
    encoded = base64.b64encode(f"{api_key}:{api_secret}".encode()).decode()
    
    test_cases = [
        ("prod_token", "https://apigw.mkk.com.tr/api/vyk/generateToken", {"Authorization": f"Basic {encoded}"}),
        ("dev_members", "https://apigwdev.mkk.com.tr/api/vyk/members", {"Authorization": f"Basic {encoded}"}),
        ("prod_members", "https://apigw.mkk.com.tr/api/vyk/members", {"Authorization": f"Basic {encoded}"}),
        ("dev_members_apikey", "https://apigwdev.mkk.com.tr/api/vyk/members", {"apikey": api_key}),
    ]
    
    for name, url, headers in test_cases:
        try:
            r = req.get(url, headers=headers, timeout=10, verify=False)
            results[name] = {"status": r.status_code, "body": r.text[:200]}
        except Exception as e:
            results[name] = {"error": str(e)}
    
    return results